# `prune_macros.py` — Thuat toan chi tiet

Tai lieu mo ta logic tung buoc cua [prune_macros.py](prune_macros.py) (v2).

---

## 1. Muc dich

Script lay **ground truth** tu file `.i` (output cua `clang -E -frewrite-includes`
hoac ARM Compiler 6) de biet nhanh `#if/#elif` nao **thuc su duoc compile** cho mot
build config cu the, roi **xoa cac nhanh chet** trong file `.cpp/.h` goc, dong thoi
**giu nguyen 100% format / comment / whitespace** cua nhanh song.

### Y tuong cot loi

Voi `-frewrite-includes`, Clang in ra **CA HAI nhanh** (true va false) duoi dang raw
text kem line marker day du. Tin hieu duy nhat phan biet la **chu so `0`/`1` ngay sau
`#if` / `#elif`**:

```c
#if 1 /* evaluated by -frewrite-includes */
# 42 "foo.cpp"
```

Trich tu `clang/lib/Frontend/Rewrite/InclusionRewriter.cpp`:

```cpp
OS << (elif ? "#elif " : "#if ") << (isTrue ? "1" : "0")
   << " /* evaluated by -frewrite-includes */" << MainEOL;
```

> **Bai hoc tu v1:** thuat toan cu dua vao "co line marker + co noi dung ngay sau
> => nhanh song" la **SAI**, vi ca hai nhanh deu co marker va noi dung.

---

## 2. Cac regex chu chot

| Ten | Pattern | Dung de |
|---|---|---|
| `LINE_MARKER_RE` | `^#\s+(\d+)\s+"((?:[^"\\]\|\\.)*)"\s*(.*)$` | Bat line marker `# N "file"` |
| `DIRECTIVE_RE` | `^\s*#\s*(if\|ifdef\|ifndef\|elif\|else\|endif)\b(.*)$` | Nhan dien directive khi parse file goc |
| `EVAL_RE` | `^\s*#\s*(if\|elif)\s+([01])\s*/\*\s*evaluated by -frewrite-includes` | Ground truth trong `.i` |
| `MACRO_DEFINED_RE` | `^\s*#\s*(if\|elif)\s+defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$` | Dang don gian `defined(X)` |
| `MACRO_NOTDEFINED_RE` | `^\s*#\s*(if\|elif)\s+!\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$` | Dang don gian `!defined(X)` |
| `IFDEF_RE` / `IFNDEF_RE` | `^\s*#\s*ifdef\|ifndef\s+([A-Za-z_]\w*)\s*$` | Lay ten macro cua `#ifdef/#ifndef` |

---

## 3. Thuat toan tung buoc

### Buoc 0 — Nap input & resolve ten file

- Doc `--cpp-file` thanh `lines[]` voi `newline=''` (giu nguyen CRLF/LF goc).
- [`resolve_target_filename()`](prune_macros.py#L423-L447): neu `--target-name`
  khong khop chinh xac ten trong line marker cua `.i`, fallback so khop theo
  **basename** (chuan hoa `\` -> `/`).
  - Dung 1 ung vien -> dung ung vien do.
  - 0 hoac >1 ung vien -> in toan bo danh sach filename co trong `.i` roi `exit(1)`.

### Buoc 1 — Trich ground truth `#if/#elif` tu `.i`

Ham [`parse_i_eval_truths()`](prune_macros.py#L78-L110). Quet tuan tu, dung 1 bien
trang thai `pending`:

1. Gap dong khop `EVAL_RE` -> `pending = (chu_so == '1')`, sang dong tiep.
2. Dong **ngay sau** phai la line marker `# N "file"`:
   - **Dung** -> than nhanh bat dau o dong `N` cua file goc, suy ra dong cua chinh
     directive la **`N - 1`**. Ghi `truths[(file, N-1)] = pending`.
   - **Sai** (hiem, vd `ShowLineMarkers` bi tat) -> bo qua entry (`pending = None`),
     nhung van thu match dong hien tai voi `EVAL_RE`.

**Ket qua:** `truths = {(filename, dong_directive_1based): bool}` — day la
**GROUND TRUTH THAT SU**, khong phai suy doan.

> **Gia dinh:** directive nam gon tren 1 dong (khong co `\` noi dong).

### Buoc 2 — Parse file goc thanh cay khoi dieu kien

#### 2a. Comment-aware scan

[`compute_line_start_in_code()`](prune_macros.py#L143-L202) quet o cap **ky tu**,
theo doi state:

- block comment `/* */`
- string literal `"..."` (co xu ly escape `\`)
- char literal `'...'` (co xu ly escape `\`)
- line comment `//` -> `break` het dong

Tra ve `list[bool]`: **dau moi dong** co dang o code binh thuong hay khong. Muc dich:
khong nham `#ifdef` nam trong block comment thanh directive that.

> **Gioi han:** khong xu ly raw string C++11 `R"(...)"` nhieu dong.

#### 2b. Xay cay bang stack

[`parse_conditional_tree()`](prune_macros.py#L205-L255):

| Directive | Hanh dong |
|---|---|
| `#if` / `#ifdef` / `#ifndef` | flush doan code dang gom -> tao `Group` + `Branch` dau tien -> append `('group', grp)` vao output hien tai -> **push** stack |
| `#elif` / `#else` | dong `content_end` cua branch truoc -> tao `Branch` moi -> doi output dich cua stack top |
| `#endif` | dong branch cuoi -> set `endif_line_idx` -> **pop** stack |

**Cau truc du lieu:**

```python
@dataclass
class Branch:
    directive_line_idx: int   # index 0-based cua dong #if/#elif/#else
    content_start: int        # index dong dau tien thuoc noi dung nhanh
    content_end: int = None   # index dong directive ke tiep (exclusive)
    children: list = []       # cac item long ben trong

@dataclass
class Group:
    branches: list = []
    endif_line_idx: int = None
```

Output la danh sach item long nhau, moi item la `('code', start, end)` hoac
`('group', Group)`.

**Diem quan trong:** sau moi directive, `code_start = i + 1`, nen **dong directive
khong bao gio nam trong item `'code'`** => directive tu dong bi xoa khi render.

**Loi cau truc** (`#elif` khong co `#if`, `#endif` thua, thieu `#endif`) -> raise
`ValueError`.

### Buoc 3 — Suy luan macro cho `#ifdef` / `#ifndef`

**Van de:** Clang **khong** annotate `#ifdef/#ifndef` (khong co case rieng trong
switch cua `InclusionRewriter`, roi vao `default` -> copy nguyen van bat ke true/false)
=> `.i` **khong cho tin hieu true/false nao** cho hai directive nay.

**Giai phap:** [`build_macro_truth_table()`](prune_macros.py#L299-L331) duyet toan bo
cay, voi moi branch:

- Neu `(file, dong)` co trong `truths` **VA** dong directive co dang **don gian**:
  - `#if defined(X)` / `#elif defined(X)` -> `macro_truth[X] = val`
  - `#if !defined(X)` / `#elif !defined(X)` -> `macro_truth[X] = not val`
- Dung `setdefault` => **lan gap dau tien thang**.

**Gia dinh:** trong 1 lan build, trang thai dinh nghia cua macro `X` khong doi.
Script **khong** xu ly `#undef` xen giua.

> **Quirk trong code:** sau khi match `defined(X)` co `continue`, nen
> [`walk(branch.children)`](prune_macros.py#L329) bi bo qua => macro nam **long ben
> trong** mot nhanh `#if defined(X)` se khong duoc thu thap vao bang.

### Buoc 4 — Resolve tung group

[`resolve_group()`](prune_macros.py#L334-L399) duyet moi branch cua group:

| Loai directive | Cach quyet dinh |
|---|---|
| `if` / `elif` | Tra `truths[(file, dong)]`. Co & `True` -> ghi nhan `true_idx`. **Khong co key** -> them vao `unresolved` |
| `ifdef X` | Tra `macro_truth[X]`. `True` -> `true_idx`. Khong co `X` -> `unresolved` |
| `ifndef X` | Tra `macro_truth[X]`. **`False`** -> `true_idx`. Khong co `X` -> `unresolved` |
| `else` | Khong xet o day — xu ly bang loai tru o duoi |

**Ket luan (theo thu tu uu tien):**

1. Co bat ky `unresolved` nao -> tra `'UNRESOLVED'` (an toan hon la doan bay).
2. Co `true_idx` -> tra index do.
   *(Vong lap ghi de nen neu co nhieu nhanh true, nhanh **cuoi cung** thang.)*
3. Khong nhanh nao true **va** branch cuoi la `#else` -> chon `#else`
   (logic loai tru cua chinh preprocessor).
4. Con lai -> `None` = **ca group bi xoa**.

### Buoc 5 — Render output

[`render_items()`](prune_macros.py#L402-L416), de quy:

| Item | Hanh vi |
|---|---|
| `('code', s, e)` | Copy nguyen xi `lines[s:e]` |
| `('group', grp)` -> `'UNRESOLVED'` | Copy raw `lines[#if_dau : #endif+1]` — **giu nguyen tat ca**, ke ca group long ben trong |
| `('group', grp)` -> `choice is not None` | **Chi** de quy vao `branch.children` cua nhanh song => directive `#if/#elif/#else/#endif` bien mat, noi dung giu nguyen byte-for-byte |
| `('group', grp)` -> `None` | Khong xuat gi ca |

Ghi file bang `writelines()` voi `newline=''` -> bao toan line ending goc.

### Buoc 6 — Bao cao

1. In `Da ghi: <output>  (X / Y dong con lai)`.
2. Neu co `--defines-file`: [`export_defines_file()`](prune_macros.py#L274-L296)
   xuat:
   - Macro `True` -> `#define X`
   - Macro `False` -> `/* #undef X */` (comment, chi de audit)
3. Neu `unresolved` khong rong: in canh bao kem so dong + ly do, yeu cau kiem tra
   thu cong.

---

## 4. So do luong

```
   .i file                          .cpp/.h goc
      |                                  |
      v                                  v
[Buoc 1] parse_i_eval_truths      [Buoc 2a] compute_line_start_in_code
      |                                  |
      | truths                           v
      | {(file,line): bool}       [Buoc 2b] parse_conditional_tree
      |                                  |
      |                                  | tree: [('code',s,e) | ('group',Group)]
      |                                  |
      +---------------+------------------+
                      |
                      v
          [Buoc 3] build_macro_truth_table
                      |
                      | macro_truth {name: bool}
                      v
          [Buoc 4+5] render_items / resolve_group
                      |
        +-------------+-------------+
        v                           v
   output file              unresolved warnings
```

---

## 5. Cac che do CLI

| Che do | Dieu kien | Hanh vi |
|---|---|---|
| `--list-files` | chi can `--i-file` | Liet ke moi filename trong line marker cua `.i` roi thoat |
| `--explain-line N` | can `--cpp-file` | Audit 1 dong: thuoc branch nao, SONG / DEAD / UNRESOLVED, kem "bang chung" (annotation `.i` hay suy luan macro) |
| `--defines-file` **khong** `--output` | can `--cpp-file` | Chi chay Buoc 1-3 va xuat bang macro, khong prune file nao |
| Binh thuong | can `--cpp-file` + `--output` | Chay full Buoc 0-6 |

### Vi du

```bash
# Liet ke filename co trong .i
python prune_macros.py --i-file main.i --list-files

# Prune 1 file
python prune_macros.py --i-file main.i --cpp-file main.c --output main.filtered.c

# Prune + xuat danh sach macro suy luan duoc
python prune_macros.py --i-file main.i --cpp-file main.c \
                       --output main.filtered.c --defines-file defines.h

# Audit dong 123
python prune_macros.py --i-file main.i --cpp-file main.c --explain-line 123
```

---

## 6. Gioi han can nho

1. Chi prune **1 file** moi lan chay.
2. Dieu kien phuc tap (vd `#if defined(A) && defined(B)`) resolve duoc cho **chinh no**
   (nho annotation trong `.i`), nhung **khong** tach duoc tung macro rieng le de dua
   vao `macro_truth` phuc vu `#ifdef/#ifndef`.
3. `#undef` xen giua -> ket qua sai cho `#ifdef/#ifndef`. Script khong xu ly.
4. Raw string C++11 nhieu dong `R"(...)"` co the pha comment-aware scan.
5. Directive noi dong bang `\` co the lam lech mapping `N - 1` o Buoc 1.
6. **BAT BUOC**: build lai `-E` tren file output va diff voi `.i` goc truoc khi dua
   vao codebase that. Day la buoc bat buoc, khong phai tuy chon.
