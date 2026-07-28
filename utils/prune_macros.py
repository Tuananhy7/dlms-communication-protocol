#!/usr/bin/env python3
"""
prune_macros.py  (v2 - sua loi nghiem trong trong v1)
=======================================================
Muc dich: Doi chieu file .i (preprocessed output, ARM Compiler 6 / clang -E
-frewrite-includes) voi file .cpp/.h goc, de loai bo cac nhanh
#if/#ifdef/#ifndef/#elif/#else KHONG duoc bien dich cho mot product cu the,
trong khi GIU NGUYEN 100% format, comment, whitespace cua nhanh con lai.

=== BAI HOC TU v1 (quan trong, doc truoc khi tin tuong ket qua) ===
Ban dau (v1) thuat toan dua vao: "co line marker (# N "file") + co noi
dung ngay sau no trong .i" => coi la 'song'. Dieu nay SAI. Da kiem chung
truc tiep qua source code Clang (lib/Frontend/Rewrite/InclusionRewriter.cpp,
ham xu ly tok::pp_if/tok::pp_elif):

    OS << (elif ? "#elif " : "#if ") << (isTrue ? "1" : "0")
       << " /* evaluated by -frewrite-includes */" << MainEOL;

Clang in ra CA HAI nhanh (true va false) cua moi #if/#elif duoi dang van
ban RAW (kem line marker day du), chi khac nhau o so 0/1 ngay sau
"#if"/"#elif" - do la TIN HIEU DUY NHAT dang tin, KHONG PHAI viec co
marker/content hay khong (ca 2 nhanh deu co).

=== THUAT TOAN DUNG (v2) ===
  1. Quet .i, tim moi dong dang:
         #if 0|1 /* evaluated by -frewrite-includes */
         #elif 0|1 /* evaluated by -frewrite-includes */
     Dong NGAY SAU (marker "# N "file"") cho biet dong bat dau cua than
     nhanh trong file GOC -> suy ra dong cua chinh directive #if/#elif do
     la N-1. Luu vao dict {(file, dong_directive): True/False}.
     Day la GROUND TRUTH THAT SU cho #if/#elif.

  2. QUAN TRONG: Clang KHONG co xu ly dac biet cho #ifdef/#ifndef (khong
     co case rieng trong switch cua InclusionRewriter - roi vao default,
     chi copy nguyen van bat ke true/false). Nghia la voi #ifdef/#ifndef,
     .i KHONG cho tin hieu true/false dang tin cay nao ca.
     => Voi #ifdef X / #ifndef X, thuat toan co gang SUY LUAN qua tuong
     quan: neu o dau do trong CUNG FILE co "#if defined(X)" hoac
     "#elif defined(X)" (dang gia tri macro X) da duoc xac dinh true/false
     o buoc 1, dung lai gia tri do (macro X co dinh nghia hay khong trong
     suot 1 lan build thi khong doi, tru khi co #undef xen giua - script
     KHONG xu ly truong hop #undef xen giua nay, hiem gap).
     Neu KHONG tim duoc tuong quan nao -> KHONG DOAN, giu nguyen ca
     #ifdef/#endif va noi dung ben trong trong output, kem canh bao ro
     rang cuoi cung de nguoi dung tu kiem tra thu cong.
     Dung --defines-file <path> de XUAT danh sach macro suy luan duoc
     (defined=true) ra file, tien theo doi/audit hoac doi chieu thu cong.

  3. Parse file .cpp/.h goc thanh cay khoi dieu kien (nhu v1, co comment-
     aware de tranh nham #ifdef trong /* */).

  4. Voi moi group (#if/.../#endif), dung ket qua buoc 1+2 de chon dung
     1 nhanh song, xoa cac nhanh con lai VA xoa directive.

=== VAN CAN LUU Y ===
  - Chi xu ly 1 file .cpp/.h muc tieu tai 1 thoi diem.
  - LUON build lai (-E) file output va diff voi .i goc de xac nhan truoc
    khi dua vao codebase that - day la buoc bat buoc, khong phai tuy chon.
  - Dieu kien phuc tap (vd "#if defined(A) && defined(B)") KHONG the suy
    ra tung macro rieng le cho #ifdef tuong quan - chi ho tro dang don
    gian: defined(X), !defined(X), hoac bare macro sau ifdef/ifndef.
"""

import re
import sys
import os
from dataclasses import dataclass, field

LINE_MARKER_RE = re.compile(r'^#\s+(\d+)\s+"((?:[^"\\]|\\.)*)"\s*(.*)$')
DIRECTIVE_RE = re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)$')
EVAL_RE = re.compile(r'^\s*#\s*(if|elif)\s+([01])\s*/\*\s*evaluated by -frewrite-includes')


# ---------------------------------------------------------------------------
# BUOC 1: Doc ground-truth true/false cho tung #if/#elif tu annotation that
# ---------------------------------------------------------------------------

def parse_i_eval_truths(i_path):
    """
    Tra ve dict {(filename, directive_line_1based): bool}
    Dua truc tiep vao annotation "evaluated by -frewrite-includes" cua
    Clang - day la GROUND TRUTH, khong phai suy doan.
    """
    truths = {}
    pending = None  # bool dang cho marker xac nhan dong

    with open(i_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        for raw in f:
            line = raw.rstrip('\r\n')

            if pending is not None:
                m = LINE_MARKER_RE.match(line)
                if m:
                    body_line = int(m.group(1))
                    fname = m.group(2)
                    directive_line = body_line - 1
                    truths[(fname, directive_line)] = pending
                    pending = None
                    continue
                else:
                    # Khong thay marker ngay sau (hiem - vd ShowLineMarkers
                    # bi tat). Bo qua, khong ghi nhan duoc entry nay.
                    pending = None

            m2 = EVAL_RE.match(line)
            if m2:
                pending = (m2.group(2) == '1')
                continue

    return truths


def list_filenames_in_i(i_path):
    """Ho tro debug: liet ke cac filename co xuat hien trong marker cua .i"""
    names = set()
    with open(i_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        for raw in f:
            m = LINE_MARKER_RE.match(raw.rstrip('\r\n'))
            if m:
                names.add(m.group(2))
    for n in sorted(names):
        print(n)


# ---------------------------------------------------------------------------
# BUOC 3: Parse .cpp/.h thanh cay khoi dieu kien (comment-aware)
# ---------------------------------------------------------------------------

@dataclass
class Branch:
    directive_line_idx: int          # index (0-based) cua dong #if/#elif/#else
    content_start: int               # index dong dau tien thuoc noi dung nhanh
    content_end: int = None          # index dong directive ke tiep (exclusive)
    children: list = field(default_factory=list)


@dataclass
class Group:
    branches: list = field(default_factory=list)
    endif_line_idx: int = None


def compute_line_start_in_code(lines):
    """
    Quet toan bo file o cap ky tu, theo doi block comment /* */, string,
    char literal. Tra ve list[bool]: dau moi dong co dang o code binh
    thuong hay khong - de tranh nham #ifdef nam trong comment thanh that.
    Gioi han: khong xu ly raw string C++11 R"(...)" nhieu dong (hiem gap
    trong code embedded).
    """
    n = len(lines)
    line_start_in_code = [True] * n
    in_block_comment = False

    for idx, line in enumerate(lines):
        line_start_in_code[idx] = not in_block_comment
        in_string = False
        in_char = False
        j = 0
        L = len(line)
        while j < L:
            c = line[j]
            if in_block_comment:
                if c == '*' and j + 1 < L and line[j + 1] == '/':
                    in_block_comment = False
                    j += 2
                    continue
                j += 1
                continue
            if in_string:
                if c == '\\':
                    j += 2
                    continue
                if c == '"':
                    in_string = False
                j += 1
                continue
            if in_char:
                if c == '\\':
                    j += 2
                    continue
                if c == "'":
                    in_char = False
                j += 1
                continue
            if c == '/' and j + 1 < L and line[j + 1] == '/':
                break
            if c == '/' and j + 1 < L and line[j + 1] == '*':
                in_block_comment = True
                j += 2
                continue
            if c == '"':
                in_string = True
                j += 1
                continue
            if c == "'":
                in_char = True
                j += 1
                continue
            j += 1

    return line_start_in_code


def parse_conditional_tree(lines):
    root = []
    stack = []
    top_output = root

    def current_output():
        return stack[-1][1] if stack else top_output

    i = 0
    n = len(lines)
    code_start = 0
    line_start_in_code = compute_line_start_in_code(lines)

    def flush_code(end_idx):
        out = current_output()
        if end_idx > code_start:
            out.append(('code', code_start, end_idx))

    while i < n:
        line = lines[i]
        m = DIRECTIVE_RE.match(line) if line_start_in_code[i] else None
        if m:
            flush_code(i)
            kind = m.group(1)
            if kind in ('if', 'ifdef', 'ifndef'):
                grp = Group()
                branch = Branch(directive_line_idx=i, content_start=i + 1)
                grp.branches.append(branch)
                current_output().append(('group', grp))
                stack.append((grp, branch.children))
            elif kind in ('elif', 'else'):
                if not stack:
                    raise ValueError(f"#{kind} khong co #if tuong ung tai dong {i+1}")
                grp, _ = stack[-1]
                grp.branches[-1].content_end = i
                branch = Branch(directive_line_idx=i, content_start=i + 1)
                grp.branches.append(branch)
                stack[-1] = (grp, branch.children)
            elif kind == 'endif':
                if not stack:
                    raise ValueError(f"#endif du thua tai dong {i+1}")
                grp, _ = stack.pop()
                grp.branches[-1].content_end = i
                grp.endif_line_idx = i
            code_start = i + 1
        i += 1

    flush_code(n)
    if stack:
        raise ValueError("Thieu #endif - kiem tra lai file, co the co #if trong string/comment gay nham")
    return root


# ---------------------------------------------------------------------------
# BUOC 2 + 4: Tuong quan ten macro cho #ifdef/#ifndef, roi resolve + render
# ---------------------------------------------------------------------------

MACRO_DEFINED_RE = re.compile(r'^\s*#\s*(if|elif)\s+defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$')
MACRO_NOTDEFINED_RE = re.compile(r'^\s*#\s*(if|elif)\s+!\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$')
IFDEF_RE = re.compile(r'^\s*#\s*ifdef\s+([A-Za-z_]\w*)\s*$')
IFNDEF_RE = re.compile(r'^\s*#\s*ifndef\s+([A-Za-z_]\w*)\s*$')
DIRECTIVE_KIND_RE = re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else)\b')


def directive_kind(line):
    m = DIRECTIVE_KIND_RE.match(line)
    return m.group(1) if m else None


def export_defines_file(macro_truth, output_path):
    """
    Xuat danh sach macro suy luan duoc tu tuong quan #if defined(X)/
    #elif defined(X) trong file goc, doi chieu voi annotation
    'evaluated by -frewrite-includes' trong .i.
    - Macro TRUE (duoc dinh nghia)  -> ghi dang "#define X"
    - Macro FALSE (khong dinh nghia) -> ghi dang comment "/* #undef X */"
      de tien theo doi/audit, khong anh huong khi doc lai.
    File nay co the dung lam tham khao hoac chia se giua cac lan chay
    khac nhau tren cung 1 codebase/build config.
    """
    defined = sorted(m for m, v in macro_truth.items() if v)
    undefined = sorted(m for m, v in macro_truth.items() if not v)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("/* Xuat tu prune_macros.py - macro suy luan duoc tu .i (-frewrite-includes) */\n")
        f.write("/* Macro DUOC dinh nghia (evaluated = 1): */\n")
        for m in defined:
            f.write(f"#define {m}\n")
        f.write("\n/* Macro KHONG duoc dinh nghia (evaluated = 0), chi de tham khao: */\n")
        for m in undefined:
            f.write(f"/* #undef {m} */\n")
    print(f"Da xuat defines-file: {output_path}  ({len(defined)} macro defined, {len(undefined)} macro undefined)")
    return output_path


def build_macro_truth_table(tree, lines, target_fname, truths):
    """
    Duyet toan bo cay, voi moi branch #if/#elif co dang DON GIAN
    "defined(X)" hoac "!defined(X)" VA co ground-truth tu buoc 1,
    suy ra X co duoc dinh nghia hay khong. Tra ve dict {macro_name: bool}.
    Dung de resolve #ifdef/#ifndef sau nay (macro cung ten thi cung trang
    thai dinh nghia trong suot 1 lan build, tru truong hop #undef xen giua
    - khong duoc xu ly o day).
    """
    macro_truth = {}

    def walk(items):
        for item in items:
            if item[0] != 'group':
                continue
            _, grp = item
            for branch in grp.branches:
                line = lines[branch.directive_line_idx]
                directive_line_1based = branch.directive_line_idx + 1
                key = (target_fname, directive_line_1based)
                if key in truths:
                    val = truths[key]
                    m1 = MACRO_DEFINED_RE.match(line)
                    if m1:
                        macro_truth.setdefault(m1.group(2), val)
                        continue
                    m2 = MACRO_NOTDEFINED_RE.match(line)
                    if m2:
                        macro_truth.setdefault(m2.group(2), not val)
                        continue
                walk(branch.children)
    walk(tree)
    return macro_truth


def resolve_group(grp, lines, target_fname, truths, macro_truth, unresolved):
    """
    Tra ve index cua branch 'song' trong grp.branches, hoac None neu
    khong nhanh nao song (vd #if false, khong co #else), hoac 'UNRESOLVED'
    neu co branch #ifdef/#ifndef khong the xac dinh -> trong truong hop
    nay GIU NGUYEN toan bo group (an toan hon la doan bay).
    """
    true_idx = None
    has_unresolved = False

    for idx, branch in enumerate(grp.branches):
        line = lines[branch.directive_line_idx]
        kind = directive_kind(line)
        directive_line_1based = branch.directive_line_idx + 1
        key = (target_fname, directive_line_1based)

        if kind in ('if', 'elif'):
            if key in truths:
                if truths[key]:
                    true_idx = idx
                continue
            else:
                has_unresolved = True
                unresolved.append((directive_line_1based, line.strip(), 'khong tim thay entry evaluated trong .i'))
                continue

        if kind == 'ifdef':
            m = IFDEF_RE.match(line)
            macro = m.group(1) if m else None
            if macro and macro in macro_truth:
                if macro_truth[macro]:
                    true_idx = idx
            else:
                has_unresolved = True
                unresolved.append((directive_line_1based, line.strip(),
                                    f"khong the suy luan macro '{macro}' - .i khong danh dau #ifdef, va khong tim thay #if defined({macro}) tuong quan trong file nay"))
            continue

        if kind == 'ifndef':
            m = IFNDEF_RE.match(line)
            macro = m.group(1) if m else None
            if macro and macro in macro_truth:
                if not macro_truth[macro]:
                    true_idx = idx
            else:
                has_unresolved = True
                unresolved.append((directive_line_1based, line.strip(),
                                    f"khong the suy luan macro '{macro}' - .i khong danh dau #ifndef, va khong tim thay #if defined({macro}) tuong quan trong file nay"))
            continue

        # kind == 'else': khong co dieu kien rieng, xu ly qua elimination
        # ben duoi (khong lam gi o day)

    if has_unresolved:
        return 'UNRESOLVED'

    if true_idx is not None:
        return true_idx

    # Khong branch if/elif/ifdef/ifndef nao true -> neu co #else cuoi cung,
    # do la nhanh song (dung logic loai tru cua chinh preprocessor).
    last_line = lines[grp.branches[-1].directive_line_idx]
    if directive_kind(last_line) == 'else':
        return len(grp.branches) - 1

    return None  # khong nhanh nao song, ca group bi loai bo


def render_items(items, lines, target_fname, truths, macro_truth, unresolved, out):
    for item in items:
        if item[0] == 'code':
            _, s, e = item
            out.extend(lines[s:e])
        else:
            _, grp = item
            choice = resolve_group(grp, lines, target_fname, truths, macro_truth, unresolved)
            if choice == 'UNRESOLVED':
                start = grp.branches[0].directive_line_idx
                end = grp.endif_line_idx + 1
                out.extend(lines[start:end])
            elif choice is not None:
                branch = grp.branches[choice]
                render_items(branch.children, lines, target_fname, truths, macro_truth, unresolved, out)


# ---------------------------------------------------------------------------
# API chinh
# ---------------------------------------------------------------------------

def resolve_target_filename(i_path, target_fname_in_i, truths):
    """Neu ten khong khop chinh xac, thu tim theo basename (chuan hoa '\\' -> '/')."""
    all_files = set(f for (f, _) in truths.keys())
    # Bo sung them cac ten file tu marker thuan tuy (truong hop khong co
    # bat ky #if/#elif nao trong file - vi du header thuan khai bao).
    with open(i_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        for raw in f:
            m = LINE_MARKER_RE.match(raw.rstrip('\r\n'))
            if m:
                all_files.add(m.group(2))

    if target_fname_in_i in all_files:
        return target_fname_in_i

    def norm_basename(p):
        return os.path.basename(p.replace('\\', '/'))

    candidates = [k for k in all_files if norm_basename(k) == norm_basename(target_fname_in_i)]
    if len(candidates) == 1:
        return candidates[0]

    print("KHONG TIM THAY filename khop trong .i. Cac filename co trong .i:")
    for k in sorted(all_files):
        print("  ", k)
    raise SystemExit(1)


def prune_file(cpp_path, i_path, target_fname_in_i, output_path, defines_file=None):
    with open(cpp_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        lines = f.readlines()

    truths = parse_i_eval_truths(i_path)
    target_fname_in_i = resolve_target_filename(i_path, target_fname_in_i, truths)

    tree = parse_conditional_tree(lines)
    macro_truth = build_macro_truth_table(tree, lines, target_fname_in_i, truths)

    unresolved = []
    out = []
    render_items(tree, lines, target_fname_in_i, truths, macro_truth, unresolved, out)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(out)

    print(f"Da ghi: {output_path}  ({len(out)} / {len(lines)} dong con lai)")

    if defines_file:
        export_defines_file(macro_truth, defines_file)

    if unresolved:
        print()
        print(f"!!! CANH BAO: {len(unresolved)} khoi #ifdef/#ifndef/#if KHONG suy luan duoc, da GIU NGUYEN trong output, can ban tu kiem tra thu cong:")
        for line_no, text, reason in unresolved:
            print(f"  Dong {line_no}: {text}")
            print(f"    -> {reason}")

    return output_path


def explain_line(cpp_path, i_path, target_fname_in_i, line_no):
    """
    Audit: cho biet dong (1-based) trong file goc thuoc branch nao, va
    branch do duoc resolve la song/chet/unresolved theo co che nao.
    """
    with open(cpp_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        lines = f.readlines()

    truths = parse_i_eval_truths(i_path)
    target_fname_in_i = resolve_target_filename(i_path, target_fname_in_i, truths)

    tree = parse_conditional_tree(lines)
    macro_truth = build_macro_truth_table(tree, lines, target_fname_in_i, truths)
    unresolved = []

    idx0 = line_no - 1

    def find_branch(items, path):
        for item in items:
            if item[0] == 'code':
                _, s, e = item
                if s <= idx0 < e:
                    return None  # ngoai moi group, luon song
            else:
                _, grp = item
                for bi, branch in enumerate(grp.branches):
                    if branch.content_start <= idx0 < branch.content_end:
                        return (grp, bi, branch, path)
                    inner = find_branch(branch.children, path + [(grp, bi)])
                    if inner is not None:
                        return inner
        return None

    result = find_branch(tree, [])
    if result is None:
        print(f"Dong {line_no}: nam NGOAI moi khoi #if/#ifdef (code khong dieu kien) -> LUON SONG.")
        return

    grp, bi, branch, path = result
    choice = resolve_group(grp, lines, target_fname_in_i, truths, macro_truth, unresolved)
    line_text = lines[branch.directive_line_idx].rstrip('\r\n')
    print(f"Dong {line_no} thuoc branch: {line_text.strip()}  (directive tai dong {branch.directive_line_idx+1})")

    if choice == 'UNRESOLVED':
        print("KET LUAN: UNRESOLVED - khong suy luan duoc, script se GIU NGUYEN block nay.")
        for ln, txt, reason in unresolved:
            print(f"  Dong {ln}: {txt}\n    -> {reason}")
    elif choice == bi:
        print("KET LUAN: SONG (branch nay duoc chon).")
    else:
        print("KET LUAN: DEAD (mot branch KHAC trong cung group moi la branch song).")

    key = (target_fname_in_i, branch.directive_line_idx + 1)
    if key in truths:
        print(f"Bang chung: annotation 'evaluated by -frewrite-includes' tai dong {branch.directive_line_idx+1} cua .i => {'1 (true)' if truths[key] else '0 (false)'}")
    else:
        kind = directive_kind(line_text)
        if kind in ('ifdef', 'ifndef'):
            m = IFDEF_RE.match(line_text) or IFNDEF_RE.match(line_text)
            macro = m.group(1) if m else None
            if macro in macro_truth:
                print(f"Bang chung: suy luan qua ten macro '{macro}' (tim thay #if defined({macro}) noi khac trong file, gia tri: {macro_truth[macro]})")
            else:
                print(f"Bang chung: KHONG CO - macro '{macro}' khong xuat hien duoi dang #if defined(...) o dau khac trong file nay.")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--i-file', required=True, help='File .i (preprocessed output, -frewrite-includes)')
    ap.add_argument('--cpp-file', help='File .cpp/.h goc can prune')
    ap.add_argument('--target-name', help='Ten file dung trong line marker cua .i (mac dinh = --cpp-file)')
    ap.add_argument('--output', help='File output')
    ap.add_argument('--list-files', action='store_true', help='Liet ke cac filename co trong .i roi thoat')
    ap.add_argument('--explain-line', type=int, help='Audit 1 dong cu the (1-based) trong --cpp-file')
    ap.add_argument('--defines-file', help='Duong dan OUTPUT: xuat danh sach macro suy luan duoc (defined=true qua doi chieu #if defined(X) trong --cpp-file voi annotation "evaluated by -frewrite-includes" trong .i)')
    args = ap.parse_args()

    if args.list_files:
        list_filenames_in_i(args.i_file)
        sys.exit(0)

    if args.explain_line is not None:
        if not args.cpp_file:
            ap.error('--cpp-file la bat buoc khi dung --explain-line')
        target = args.target_name or args.cpp_file
        explain_line(args.cpp_file, args.i_file, target, args.explain_line)
        sys.exit(0)

    if args.defines_file and not args.output:
        # Che do chi xuat defines-file, khong prune file nao ca.
        if not args.cpp_file:
            ap.error('--cpp-file la bat buoc khi dung --defines-file')
        target = args.target_name or args.cpp_file
        with open(args.cpp_file, 'r', encoding='utf-8', errors='replace', newline='') as f:
            lines = f.readlines()
        truths = parse_i_eval_truths(args.i_file)
        target = resolve_target_filename(args.i_file, target, truths)
        tree = parse_conditional_tree(lines)
        macro_truth = build_macro_truth_table(tree, lines, target, truths)
        export_defines_file(macro_truth, args.defines_file)
        sys.exit(0)

    if not args.cpp_file or not args.output:
        ap.error('--cpp-file va --output la bat buoc (tru khi dung --list-files/--explain-line/--defines-file doc lap)')

    target = args.target_name or args.cpp_file
    prune_file(args.cpp_file, args.i_file, target, args.output, args.defines_file)