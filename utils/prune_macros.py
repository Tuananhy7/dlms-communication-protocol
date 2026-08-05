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

     NGOAI LE duy nhat duoc suy luan ma KHONG can tuong quan #if defined(X):
     pattern "include guard" kinh dien #ifndef X / #define X (xem ham
     is_include_guard) - vi #define X nam ngay trong nhanh #ifndef X nen tu
     than no khong the anh huong ket qua danh gia cua chinh no, suy ra X
     chac chan chua dinh nghia truoc do TRONG FILE NAY. Khac voi cac macro
     suy luan thong thuong (duoc GHI VAO macro_truth roi XOA directive nhu
     1 group da resolve binh thuong), include guard duoc resolve_group tra
     ve rieng qua sentinel 'GUARD': KHONG canh bao, nhung dong #ifndef/#endif
     duoc GIU NGUYEN (khong xoa) - chi noi dung BEN TRONG moi tiep tuc duoc
     de quy prune nhu thuong. Ly do giu nguyen thay vi xoa: header thuong
     bao toan bo than file trong 1 include guard duy nhat; giu lai 2 dong
     directive vo hai nay an toan hon la coi no nhu macro suy luan thong
     thuong roi lam sai trong truong hop hiem gap.

     NGOAI LE THU HAI (cung sentinel 'GUARD'): #ifdef/#ifndef voi ten macro
     thuoc KNOWN_BUILTIN_MACROS (hien tai: __cplusplus) - day la macro do
     COMPILER dinh nghia san, khong phai macro cua codebase, nen KHONG BAO
     GIO co the tuong quan qua "#if defined(X)" o noi khac (vi #ifdef X
     chinh la cach DUY NHAT de kiem tra no). Neu group chi co 1 nhanh don
     gian (#ifdef __cplusplus / #endif, khong #else), xu ly giong include
     guard: giu nguyen directive, khong canh bao, van de quy vao ben trong.
     Neu group co nhieu nhanh (vd co #else) thi khong the chon nhanh nao de
     de quy -> tra ve 'SILENT_UNRESOLVED': giu nguyen CA GROUP (nhu
     UNRESOLVED) nhung KHONG canh bao (vi day la truong hop DA BIET TRUOC).

  3. Parse file .cpp/.h goc thanh cay khoi dieu kien (nhu v1, co comment-
     aware de tranh nham #ifdef trong /* */). Directive nhieu dong noi bang
     '\\' cuoi dong duoc GOM lai thanh 1 khoi logic (xem
     directive_end_line_idx/directive_full_text) - ca khi doi chieu ground-
     truth (.i annotate tai dong VAT LY CUOI CUNG cua directive, khong phai
     dong dau) lan khi tach noi dung than nhanh (cac dong noi khong duoc
     tinh la code).

  4. Voi moi group (#if/.../#endif), dung ket qua buoc 1+2 de chon dung
     1 nhanh song, xoa cac nhanh con lai VA xoa directive.

=== VAN CAN LUU Y ===
  - Chi xu ly 1 file .cpp/.h muc tieu tai 1 thoi diem.
  - LUON build lai (-E) file output va diff voi .i goc de xac nhan truoc
    khi dua vao codebase that - day la buoc bat buoc, khong phai tuy chon.
  - Dieu kien phuc tap (vd "#if defined(A) && defined(B)") KHONG the suy
    ra tung macro rieng le cho #ifdef tuong quan - chi ho tro dang don
    gian: defined(X), !defined(X), hoac bare macro sau ifdef/ifndef.
  - Include guard chi duoc nhan dien khi group chi co 1 nhanh #ifndef
    (khong #elif/#else) VA dong noi dung dau tien la #define cung ten.
    Khong yeu cau phai la TOP-LEVEL - include guard long trong dieu kien
    khac van duoc nhan dien theo cung tieu chi. Neu khong khop du 2 dieu
    kien tren, van roi ve duong xu ly thong thuong (co the UNRESOLVED va
    canh bao nhu cu).
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


def directive_end_line_idx(lines, start_idx):
    """
    Tra ve index (0-based) cua dong VAT LY CUOI CUNG thuoc cung 1 directive,
    tinh ca cac dong noi bang '\\' o cuoi dong (line continuation). Neu
    directive chi nam tren 1 dong, tra ve chinh start_idx.

    QUAN TRONG: khi mot #if/#elif/#ifdef/#ifndef trai dai nhieu dong vat ly
    bang '\\', Clang/-frewrite-includes GOP toan bo thanh 1 dong annotation
    "#if 0/1 ..." duy nhat trong .i, roi COPY NOI DUNG TU DONG SAU CUNG cua
    directive goc (khong phai dong dau tien "#if"/"#elif"). Vi vay ground-
    truth o Buoc 1 (body_line - 1) tro toi dong CUOI CUNG cua directive, va
    moi noi doi chieu voi truths[] deu phai dung dong nay, khong phai
    directive_line_idx (dong dau tien) - neu khong se bi lech va bao loi
    "khong tim thay entry evaluated trong .i" mot cach sai lech.
    """
    idx = start_idx
    n = len(lines)
    while idx < n - 1:
        stripped = lines[idx].rstrip('\r\n').rstrip()
        if stripped.endswith('\\'):
            idx += 1
        else:
            break
    return idx


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
            end_idx = directive_end_line_idx(lines, i)
            kind = m.group(1)
            if kind in ('if', 'ifdef', 'ifndef'):
                grp = Group()
                branch = Branch(directive_line_idx=i, content_start=end_idx + 1)
                grp.branches.append(branch)
                current_output().append(('group', grp))
                stack.append((grp, branch.children))
            elif kind in ('elif', 'else'):
                if not stack:
                    raise ValueError(f"#{kind} khong co #if tuong ung tai dong {i+1}")
                grp, _ = stack[-1]
                grp.branches[-1].content_end = i
                branch = Branch(directive_line_idx=i, content_start=end_idx + 1)
                grp.branches.append(branch)
                stack[-1] = (grp, branch.children)
            elif kind == 'endif':
                if not stack:
                    raise ValueError(f"#endif du thua tai dong {i+1}")
                grp, _ = stack.pop()
                grp.branches[-1].content_end = i
                grp.endif_line_idx = i
            code_start = end_idx + 1
            i = end_idx
        i += 1

    flush_code(n)
    if stack:
        raise ValueError("Thieu #endif - kiem tra lai file, co the co #if trong string/comment gay nham")
    return root


# ---------------------------------------------------------------------------
# BUOC 2 + 4: Tuong quan ten macro cho #ifdef/#ifndef, roi resolve + render
# ---------------------------------------------------------------------------

# Hau to comment tuy chon (/* ... */ hoac // ...) o cuoi directive - idiom
# rat pho bien (vd "#ifndef X /* X */", "#endif // X") ma cac directive
# don gian van phai nhan dien duoc, khong the doi hoi $ ngay sau ten macro.
TRAILING_COMMENT_SUFFIX = r'\s*(?:/\*.*\*/\s*|//.*)?$'

MACRO_DEFINED_RE = re.compile(r'^\s*#\s*(if|elif)\s+defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?' + TRAILING_COMMENT_SUFFIX)
MACRO_NOTDEFINED_RE = re.compile(r'^\s*#\s*(if|elif)\s+!\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?' + TRAILING_COMMENT_SUFFIX)
IFDEF_RE = re.compile(r'^\s*#\s*ifdef\s+([A-Za-z_]\w*)' + TRAILING_COMMENT_SUFFIX)
IFNDEF_RE = re.compile(r'^\s*#\s*ifndef\s+([A-Za-z_]\w*)' + TRAILING_COMMENT_SUFFIX)

# Macro do COMPILER/NGON NGU dinh nghia san (built-in), KHONG PHAI macro cua
# chinh codebase - vi vay khong bao gio the tuong quan qua "#if defined(X)"
# o noi khac trong file (vi #ifdef X chinh la cach DUY NHAT ma code C/C++
# dung de kiem tra su ton tai cua no; khong ai "#define __cplusplus" ca).
# Gia tri that su phu thuoc ngon ngu/compiler dung de bien dich file nay
# (vd __cplusplus chi duoc dinh nghia khi bien dich nhu C++), nam NGOAI
# pham vi suy luan TINH (static) cua 1 file don le. Khi gap #ifdef/#ifndef
# voi ten macro trong danh sach nay ma khong co bang chung nao khac, script
# KHONG canh bao (vi day la truong hop DA BIET TRUOC, khong phai loi suy
# luan), va van GIU NGUYEN directive (an toan, giong include guard).
KNOWN_BUILTIN_MACROS = {'__cplusplus'}
DIRECTIVE_KIND_RE = re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else)\b')
DEFINE_NAME_RE = re.compile(r'^\s*#\s*define\s+([A-Za-z_]\w*)\b')


def directive_kind(line):
    m = DIRECTIVE_KIND_RE.match(line)
    return m.group(1) if m else None


def directive_full_text(lines, start_idx, end_idx):
    """
    Noi cac dong vat ly tu start_idx den end_idx (ca 2 dau) thanh 1 chuoi
    logic, bo ky tu noi dong '\\' va xuong dong, dung de match cac regex
    dieu kien don gian (defined(X), ifdef X...) khi directive trai dai
    nhieu dong vat ly.
    """
    if end_idx <= start_idx:
        return lines[start_idx].rstrip('\r\n')
    parts = []
    for i in range(start_idx, end_idx + 1):
        seg = lines[i].rstrip('\r\n').rstrip()
        if seg.endswith('\\'):
            seg = seg[:-1].rstrip()
        parts.append(seg)
    return ' '.join(parts)


def is_include_guard(grp, lines):
    """
    Nhan dien pattern "include guard" kinh dien cua header file:
        #ifndef X
        #define X
        ...
        #endif
    (khong co #elif/#else). Day la idiom PHO BIEN NHAT trong C/C++ header,
    duoc MOI compiler cong nhan.

    Ly do suy luan an toan: Clang khong annotate #ifdef/#ifndef (xem docstring
    dau file), nen binh thuong script KHONG co bang chung nao cho #ifndef X
    neu X khong tung xuat hien duoi dang #if defined(X)/#elif defined(X) o
    noi khac. Nhung voi dung pattern nay, dong #define X nam NGAY BEN TRONG
    nhanh #ifndef X - tuc la trong pham vi file nay, X chi co THE duoc dinh
    nghia tai chinh dong do. Vi #define X nam SAU diem kiem tra #ifndef X,
    no khong the anh huong ket qua cua chinh no => tai thoi diem #ifndef
    duoc danh gia, X chac chan CHUA duoc dinh nghia boi BAT KY dieu gi truoc
    do TRONG FILE NAY => nhanh #ifndef luon la nhanh song.
    (Truong hop hiem: X da duoc -D tu ben ngoai compiler flag, hoac header
    nay da duoc include truoc do trong cung 1 TU - ca hai deu nam ngoai
    pham vi 1 file don le ma script nay xu ly.)

    CHU Y: khac voi cach suy luan macro thong thuong (dien gia tri vao
    macro_truth roi de resolve_group tu chon nhanh song va XOA directive),
    include guard duoc xu ly RIENG: resolve_group tra ve sentinel 'GUARD'
    va render_items GIU NGUYEN dong #ifndef/#endif (khong xoa), chi de quy
    binh thuong vao noi dung BEN TRONG. Ly do: header thuong bao toan bo
    than file trong 1 include guard duy nhat - neu xoa han directive nay
    (nhu 1 group duoc "resolve" binh thuong) thi khong sao ve mat noi dung,
    nhung neu coi no la macro suy luan thong thuong va lam SAI (vd macro
    trung ten voi 1 dieu kien khac phuc tap hon) thi rui ro cao hon nhieu
    so voi chi giu nguyen 2 dong directive vo hai nay.
    """
    if len(grp.branches) != 1:
        return False
    branch = grp.branches[0]
    if directive_kind(lines[branch.directive_line_idx]) != 'ifndef':
        return False
    end_idx = directive_end_line_idx(lines, branch.directive_line_idx)
    full_text = directive_full_text(lines, branch.directive_line_idx, end_idx)
    m = IFNDEF_RE.match(full_text)
    if not m:
        return False
    macro = m.group(1)
    for ln in lines[branch.content_start:branch.content_end]:
        stripped = ln.strip()
        if not stripped:
            continue
        dm = DEFINE_NAME_RE.match(stripped)
        return bool(dm and dm.group(1) == macro)
    return False


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

    LUU Y: include guard (#ifndef X / #define X) KHONG di qua bang nay -
    no duoc resolve_group nhan dien rieng qua is_include_guard() va xu ly
    bang sentinel 'GUARD' (giu nguyen directive, van de quy vao ben trong).
    """
    macro_truth = {}

    def walk(items):
        for item in items:
            if item[0] != 'group':
                continue
            _, grp = item
            for branch in grp.branches:
                end_idx = directive_end_line_idx(lines, branch.directive_line_idx)
                full_text = directive_full_text(lines, branch.directive_line_idx, end_idx)
                key = (target_fname, end_idx + 1)
                if key in truths:
                    val = truths[key]
                    m1 = MACRO_DEFINED_RE.match(full_text)
                    if m1:
                        macro_truth.setdefault(m1.group(2), val)
                        continue
                    m2 = MACRO_NOTDEFINED_RE.match(full_text)
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
    nay GIU NGUYEN toan bo group (an toan hon la doan bay), hoac 'GUARD'
    neu day la include guard kinh dien (#ifndef X / #define X) hoac group
    chi co 1 nhanh #ifdef/#ifndef voi ten macro thuoc KNOWN_BUILTIN_MACROS
    (xem is_include_guard) - ca 2 truong hop nay KHONG canh bao, va
    render_items se GIU NGUYEN dong #ifdef|#ifndef/#endif nhung van de quy
    vao ben trong de tiep tuc prune noi dung binh thuong. Neu group nhieu
    nhanh (co #else) va van khong the resolve do macro built-in, tra ve
    'SILENT_UNRESOLVED' - giu nguyen CA GROUP (khong the chon nhanh nao de
    de quy) nhung cung KHONG canh bao.
    """
    if is_include_guard(grp, lines):
        return 'GUARD'

    true_idx = None
    has_unresolved = False
    has_silent_unresolved = False

    for idx, branch in enumerate(grp.branches):
        line = lines[branch.directive_line_idx]
        kind = directive_kind(line)
        start_line_1based = branch.directive_line_idx + 1
        end_idx = directive_end_line_idx(lines, branch.directive_line_idx)
        full_text = directive_full_text(lines, branch.directive_line_idx, end_idx)
        # Ground-truth trong .i tro toi dong VAT LY CUOI CUNG cua directive
        # (xem directive_end_line_idx), khong phai dong dau tien - directive
        # nhieu dong noi bang '\' phai doi chieu bang end_idx + 1.
        key = (target_fname, end_idx + 1)
        display_text = line.strip() if end_idx == branch.directive_line_idx else full_text

        if kind in ('if', 'elif'):
            if key in truths:
                if truths[key]:
                    true_idx = idx
                continue
            else:
                has_unresolved = True
                unresolved.append((start_line_1based, display_text, 'khong tim thay entry evaluated trong .i'))
                continue

        if kind == 'ifdef':
            m = IFDEF_RE.match(full_text)
            macro = m.group(1) if m else None
            if macro and macro in macro_truth:
                if macro_truth[macro]:
                    true_idx = idx
            elif macro in KNOWN_BUILTIN_MACROS:
                has_silent_unresolved = True
            else:
                has_unresolved = True
                unresolved.append((start_line_1based, display_text,
                                    f"khong the suy luan macro '{macro}' - .i khong danh dau #ifdef, va khong tim thay #if defined({macro}) tuong quan trong file nay"))
            continue

        if kind == 'ifndef':
            m = IFNDEF_RE.match(full_text)
            macro = m.group(1) if m else None
            if macro and macro in macro_truth:
                if not macro_truth[macro]:
                    true_idx = idx
            elif macro in KNOWN_BUILTIN_MACROS:
                has_silent_unresolved = True
            else:
                has_unresolved = True
                unresolved.append((start_line_1based, display_text,
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

    if has_silent_unresolved:
        # Chi con lai cac nhanh khong the resolve vi macro built-in (vd
        # __cplusplus) - khong canh bao. Neu group chi co 1 nhanh don gian
        # (vd "#ifdef __cplusplus / #endif"), an toan de GIU NGUYEN directive
        # va van de quy vao ben trong (giong GUARD). Neu co nhieu nhanh
        # (vd co #else) thi khong the chon nhanh nao de de quy -> giu
        # nguyen CA GROUP, khong canh bao.
        if len(grp.branches) == 1:
            return 'GUARD'
        return 'SILENT_UNRESOLVED'

    return None  # khong nhanh nao song, ca group bi loai bo


def render_items(items, lines, target_fname, truths, macro_truth, unresolved, out):
    for item in items:
        if item[0] == 'code':
            _, s, e = item
            out.extend(lines[s:e])
        else:
            _, grp = item
            choice = resolve_group(grp, lines, target_fname, truths, macro_truth, unresolved)
            if choice in ('UNRESOLVED', 'SILENT_UNRESOLVED'):
                start = grp.branches[0].directive_line_idx
                end = grp.endif_line_idx + 1
                out.extend(lines[start:end])
            elif choice == 'GUARD':
                # Include guard hoac #ifdef/#ifndef macro built-in da biet
                # (vd __cplusplus): giu nguyen dong #ifdef|#ifndef/#endif,
                # van de quy vao noi dung ben trong de tiep tuc prune binh
                # thuong.
                branch = grp.branches[0]
                directive_end = directive_end_line_idx(lines, branch.directive_line_idx)
                out.extend(lines[branch.directive_line_idx:directive_end + 1])
                render_items(branch.children, lines, target_fname, truths, macro_truth, unresolved, out)
                out.extend(lines[grp.endif_line_idx:grp.endif_line_idx + 1])
            elif choice is not None:
                branch = grp.branches[choice]
                render_items(branch.children, lines, target_fname, truths, macro_truth, unresolved, out)


# ---------------------------------------------------------------------------
# API chinh
# ---------------------------------------------------------------------------

def resolve_target_filename(i_path, target_fname_in_i, truths):
    """
    Neu ten khong khop CHINH XAC (dung case), thu tim theo:
      1. Full path, KHONG PHAN BIET CHU HOA/THUONG.
      2. Basename (chuan hoa '\\' -> '/'), cung KHONG PHAN BIET HOA/THUONG.
    Ly do can buoc 1+2 khong phan biet hoa/thuong: Windows filesystem
    khong phan biet hoa/thuong, nen .i (line marker thuong do preprocessor
    tu sinh, hay o dang chu thuong nhu "main.c") va --cpp-file nguoi dung
    truyen vao (co the viet hoa, vd "MAIN.c") thuong tro toi CUNG 1 file
    vat ly du khac nhau ve chu hoa/thuong.
    """
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

    def norm_path(p):
        return p.replace('\\', '/').lower()

    def norm_basename(p):
        return os.path.basename(norm_path(p))

    target_norm = norm_path(target_fname_in_i)
    exact_ci = [k for k in all_files if norm_path(k) == target_norm]
    if len(exact_ci) == 1:
        return exact_ci[0]

    target_basename = norm_basename(target_fname_in_i)
    candidates = [k for k in all_files if norm_basename(k) == target_basename]
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
    end_idx = directive_end_line_idx(lines, branch.directive_line_idx)
    full_text = directive_full_text(lines, branch.directive_line_idx, end_idx)
    span = f"{branch.directive_line_idx+1}-{end_idx+1}" if end_idx != branch.directive_line_idx else f"{branch.directive_line_idx+1}"
    print(f"Dong {line_no} thuoc branch: {line_text.strip()}  (directive tai dong {span})")

    if choice == 'UNRESOLVED':
        print("KET LUAN: UNRESOLVED - khong suy luan duoc, script se GIU NGUYEN block nay.")
        for ln, txt, reason in unresolved:
            print(f"  Dong {ln}: {txt}\n    -> {reason}")
        return
    elif choice == 'GUARD':
        print("KET LUAN: GUARD (include guard kinh dien, hoac #ifdef/#ifndef macro built-in")
        print("  da biet nhu __cplusplus) - directive duoc GIU NGUYEN khong xoa, khong canh")
        print("  bao; noi dung ben trong van duoc prune binh thuong.")
        return
    elif choice == 'SILENT_UNRESOLVED':
        print("KET LUAN: SILENT_UNRESOLVED (macro built-in da biet nhu __cplusplus, nhung group")
        print("  co nhieu nhanh nen khong the chon 1 nhanh de de quy) - GIU NGUYEN CA GROUP,")
        print("  khong canh bao.")
        return
    elif choice == bi:
        print("KET LUAN: SONG (branch nay duoc chon).")
    else:
        print("KET LUAN: DEAD (mot branch KHAC trong cung group moi la branch song).")

    key = (target_fname_in_i, end_idx + 1)
    if key in truths:
        print(f"Bang chung: annotation 'evaluated by -frewrite-includes' tai dong {end_idx+1} cua .i => {'1 (true)' if truths[key] else '0 (false)'}")
    else:
        kind = directive_kind(line_text)
        if kind in ('ifdef', 'ifndef'):
            m = IFDEF_RE.match(full_text) or IFNDEF_RE.match(full_text)
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