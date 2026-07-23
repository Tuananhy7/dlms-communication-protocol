#!/usr/bin/env python3
"""
count_loc_from_markers.py

Muc dich
--------
Sau khi preprocess mot file .c bang armcc/armclang/gcc voi option giu lai
line marker (vd: armcc --preprocess --no_include, armclang -E -frewrite-includes,
gcc -E -dD), output .i se chua cac dong dang:

    # 12 "product_a.c"
    #line 12 "product_a.c"

Script nay:
  1. Doc file .i, parse toan bo line marker de biet CHINH XAC nhung dong nao
     trong file GOC (.c) con "song sot" sau khi cat bo cac nhanh #ifdef
     khong lien quan.
  2. Doc lai file GOC (khong phai file .i) de lay noi dung that cua tung
     dong (tranh bi anh huong boi macro expansion trong file .i).
  3. Phan loai moi dong goc: CODE / BLANK / COMMENT (co xu ly block comment
     /* ... */ da dong va dong // don gian).
  4. Tinh LOC hieu dung (effective LOC) = so dong CODE con song sot.

Gioi han da biet (ghi ro de tranh hieu nham ket qua)
-----------------------------------------------------
- Neu mot dong goc chua goi ham-macro nhieu dong (function-like macro
  invocation trai dai nhieu dong vat ly), mot so compiler co the gop lai
  thanh 1 dong logic trong output. Script van map dung theo line marker
  ma compiler sinh ra, nhung ban nen doi chieu lai thu cong voi cac file
  co nhieu macro phuc tap.
- Cac dong sinh tu "<built-in>" hoac "<command-line>" (do compiler tu them
  cac -D vao dau) se bi bo qua, khong tinh vao LOC file goc.
- Neu ban KHONG dung --no_include / -frewrite-includes, header se bi
  "nuot" vao va xuat hien nhu cac file rieng trong marker - script van
  xu ly dung (moi filename duoc gom rieng), nhung ban se thay ca LOC cua
  header, khong chi file .c dang xet.

Cach dung
---------
    python count_loc_from_markers.py <file.i> <file_goc.c> [--dump-survived out.c]

Vi du:
    python count_loc_from_markers.py product_a.i product_a.c --dump-survived product_a.filtered.c
"""

import argparse
import re
import sys
from pathlib import Path

# Regex cho 2 kieu line marker pho bien:
#   # 12 "file.c"
#   # 12 "file.c" 1 2
#   #line 12 "file.c"
MARKER_RE = re.compile(r'^#\s*(?:line\s+)?(\d+)\s+"([^"]*)"\s*(.*)$')

# armclang/clang voi -frewrite-includes giu lai directive va noi dung cua
# nhanh da duoc danh gia bang cac wrapper nhu:
#
#   #if 0 /* disabled by -frewrite-includes */
#   #if defined(FEATURE_A)
#   #endif
#   #endif /* disabled by -frewrite-includes */
#   #if 0 /* evaluated by -frewrite-includes */
#   # 70 "main.c"
#       code cua nhanh da bi loai
#   #endif
#
# Neu chi dua vao line marker, noi dung nam trong wrapper #if 0 van bi hieu
# nham la "song sot". Cac regex duoi day dung de theo doi va bo qua cac block
# do. Wrapper "evaluated" voi #if 1 van duoc doc noi dung binh thuong.
REWRITE_IF_RE = re.compile(
    r'^\s*#\s*if\s+([01])\s*/\*\s*(disabled|evaluated)\s+by\s+'
    r'-frewrite-includes\s*\*/'
)
CPP_IF_RE = re.compile(r'^\s*#\s*(?:if|ifdef|ifndef)\b')
CPP_ENDIF_RE = re.compile(r'^\s*#\s*endif\b')

# Cac "gia" filename ma compiler tu sinh, khong phai file that -> bo qua
IGNORED_FILES = {"<built-in>", "<command-line>", "<command line>", "<stdin>"}


def parse_markers(preprocessed_path: Path):
    """
    Doc file .i, tra ve dict: { filename: set(line_numbers_song_sot) }

    Logic:
    - current_file, current_line: file/line ma DONG KE TIEP (khong phai
      marker) se tuong ung trong file goc.
    - Moi khi gap 1 dong noi dung (khong phai marker), ghi nhan
      (current_file, current_line) la "song sot", roi current_line += 1.
    - Moi khi gap marker, cap nhat lai current_file/current_line theo
      marker do.
    """
    survived = {}
    current_file = None
    current_line = None

    # Moi phan tu mo ta mot wrapper do -frewrite-includes sinh ra.
    # `active=False` nghia la bo qua toan bo noi dung, ke ca line marker.
    # `depth` giup tim dung #endif khi ben trong co conditional long nhau.
    rewrite_blocks = []

    with open(preprocessed_path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            rewrite_if = REWRITE_IF_RE.match(raw_line)

            if rewrite_blocks:
                block = rewrite_blocks[-1]

                if not block["active"]:
                    # Dang o trong #if 0 do -frewrite-includes sinh ra:
                    # chi theo doi do sau de tim #endif, khong cap nhat marker
                    # va khong danh dau bat ky dong goc nao la song sot.
                    if CPP_IF_RE.match(raw_line):
                        block["depth"] += 1
                    elif CPP_ENDIF_RE.match(raw_line):
                        block["depth"] -= 1
                        if block["depth"] == 0:
                            rewrite_blocks.pop()
                    continue

                # Wrapper #if 1 dang active. Neu gap wrapper long ben trong,
                # theo doi no rieng de co the bo qua mot nhanh #if 0 con.
                if rewrite_if:
                    value, kind = rewrite_if.groups()
                    rewrite_blocks.append({
                        "active": kind == "evaluated" and value == "1",
                        "depth": 1,
                    })
                    continue

                if CPP_IF_RE.match(raw_line):
                    block["depth"] += 1
                    continue

                if CPP_ENDIF_RE.match(raw_line):
                    block["depth"] -= 1
                    if block["depth"] == 0:
                        rewrite_blocks.pop()
                    continue

            elif rewrite_if:
                value, kind = rewrite_if.groups()
                rewrite_blocks.append({
                    "active": kind == "evaluated" and value == "1",
                    "depth": 1,
                })
                continue

            m = MARKER_RE.match(raw_line)
            if m:
                line_no = int(m.group(1))
                filename = m.group(2)
                current_file = filename
                current_line = line_no
                continue

            # Dong noi dung binh thuong
            if current_file is not None and current_file not in IGNORED_FILES:
                survived.setdefault(current_file, set()).add(current_line)

            if current_line is not None:
                current_line += 1

    return survived


def classify_original_lines(original_path: Path):
    """
    Doc file goc, tra ve dict: { line_number (1-based): "CODE"|"BLANK"|"COMMENT" }

    Xu ly:
    - Block comment /* ... */ co the trai nhieu dong.
    - Line comment // (don gian, khong xu ly truong hop // nam trong string
      chua ky tu dac biet - du dung cho muc dich uoc luong LOC).
    """
    result = {}
    in_block_comment = False

    with open(original_path, "r", encoding="utf-8", errors="replace") as f:
        for i, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            if not line and not in_block_comment:
                result[i] = "BLANK"
                continue

            code_chars = 0
            j = 0
            n = len(line)
            was_in_comment_at_start = in_block_comment

            while j < n:
                if in_block_comment:
                    end = line.find("*/", j)
                    if end == -1:
                        j = n
                    else:
                        in_block_comment = False
                        j = end + 2
                    continue

                if line.startswith("/*", j):
                    in_block_comment = True
                    j += 2
                    continue

                if line.startswith("//", j):
                    # Phan con lai cua dong la comment -> dung
                    break

                # Ky tu code thuc su
                if not line[j].isspace():
                    code_chars += 1
                j += 1

            if code_chars > 0:
                result[i] = "CODE"
            elif was_in_comment_at_start or in_block_comment or line.startswith("//") or line.startswith("/*"):
                result[i] = "COMMENT"
            else:
                result[i] = "BLANK"

    return result


def match_target_file(survived: dict, target_path: Path):
    """
    Marker filename trong file .i co the la duong dan tuyet doi, tuong doi,
    hoac chi la basename, tuy compiler duoc goi nhu the nao. Ham nay co
    gang tim key phu hop nhat trong dict `survived` ung voi target_path.
    """
    target_name = target_path.name

    # 1. Khop chinh xac tuyet doi/tuong doi
    for key in survived:
        if Path(key).resolve() == target_path.resolve():
            return key

    # 2. Khop theo basename
    candidates = [key for key in survived if Path(key).name == target_name]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(f"[CANH BAO] Co nhieu file trung ten '{target_name}' trong marker: {candidates}", file=sys.stderr)
        return candidates[0]

    return None


def main():
    ap = argparse.ArgumentParser(description="Tinh LOC hieu dung bang cach map nguoc line marker ve file goc")
    ap.add_argument("preprocessed_file", type=Path, help="File .i sinh ra tu preprocessor")
    ap.add_argument("original_file", type=Path, help="File .c goc tuong ung")
    ap.add_argument("--dump-survived", type=Path, default=None,
                     help="Ghi ra 1 file .c moi, giu nguyen dong song sot, thay dong bi cat bang dong trong (de review bang diff)")
    args = ap.parse_args()

    if not args.preprocessed_file.exists():
        sys.exit(f"Khong tim thay file: {args.preprocessed_file}")
    if not args.original_file.exists():
        sys.exit(f"Khong tim thay file: {args.original_file}")

    survived_by_file = parse_markers(args.preprocessed_file)
    target_key = match_target_file(survived_by_file, args.original_file)

    if target_key is None:
        sys.exit(
            f"Khong tim thay marker nao tro ve file goc '{args.original_file.name}'. "
            f"Cac file xuat hien trong .i: {list(survived_by_file.keys())}"
        )

    survived_lines = survived_by_file[target_key]
    classification = classify_original_lines(args.original_file)

    total_lines = len(classification)
    total_code = sum(1 for v in classification.values() if v == "CODE")
    total_comment = sum(1 for v in classification.values() if v == "COMMENT")
    total_blank = sum(1 for v in classification.values() if v == "BLANK")

    survived_code = sum(
        1 for ln in survived_lines
        if classification.get(ln) == "CODE"
    )
    survived_total = sum(1 for ln in survived_lines if ln in classification)

    print("=" * 60)
    print(f"File .c Python thuc su dang doc : {args.original_file.resolve()}")
    print(f"Path compiler ghi trong marker  : {target_key}")
    print("  (Path marker chi la metadata trong file .i; Python khong mo file tai path nay.)")
    print("-" * 60)
    print(f"Tong so dong file goc          : {total_lines}")
    print(f"  - CODE                       : {total_code}")
    print(f"  - COMMENT                    : {total_comment}")
    print(f"  - BLANK                      : {total_blank}")
    print("-" * 60)
    print(f"So dong 'song sot' sau preproc  : {survived_total}")
    print(f"  --> LOC hieu dung (CODE only) : {survived_code}")
    if total_code > 0:
        pct = 100.0 * survived_code / total_code
        print(f"  --> Ty le con lai so voi file goc: {pct:.1f}%")
    print("=" * 60)

    if args.dump_survived:
        with open(args.original_file, "r", encoding="utf-8", errors="replace") as f:
            original_lines = f.readlines()

        out_lines = []
        for i, line in enumerate(original_lines, start=1):
            if i in survived_lines:
                out_lines.append(line)
            else:
                out_lines.append("\n")  # giu so dong de de diff, noi dung bi xoa

        args.dump_survived.write_text("".join(out_lines), encoding="utf-8")
        print(f"Da ghi file review (dong bi loai bo duoc thay bang dong trong): {args.dump_survived}")


if __name__ == "__main__":
    main()
