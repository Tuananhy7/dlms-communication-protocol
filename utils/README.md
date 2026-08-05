# `prune_macros.py` — Detailed Algorithm

Documentation describing the step-by-step logic of [prune_macros.py](prune_macros.py) (v2).

---

## 1. Purpose

The script uses the **ground truth** from the `.i` file (output of `clang -E -frewrite-includes`
or ARM Compiler 6) to accurately determine which `#if/#elif` branches are **actually compiled**
for a specific build config, then **removes the dead branches** in the original `.cpp/.h` file,
while **preserving 100% of the format / comments / whitespace** of the live branch.

### Core idea

With `-frewrite-includes`, Clang prints out **BOTH branches** (true and false) as raw
text with full line markers. The only signal distinguishing them is the **digit `0`/`1`
right after `#if` / `#elif`**:

```c
#if 1 /* evaluated by -frewrite-includes */
# 42 "foo.cpp"
```

Excerpt from `clang/lib/Frontend/Rewrite/InclusionRewriter.cpp`:

```cpp
OS << (elif ? "#elif " : "#if ") << (isTrue ? "1" : "0")
   << " /* evaluated by -frewrite-includes */" << MainEOL;
```

> **Lesson learned from v1:** the old algorithm relied on "has a line marker + has
> content right after => live branch", which is **WRONG**, because both branches
> have a marker and content.

---

## 2. Key regexes

| Name | Pattern | Used for |
|---|---|---|
| `LINE_MARKER_RE` | `^#\s+(\d+)\s+"((?:[^"\\]\|\\.)*)"\s*(.*)$` | Match line marker `# N "file"` |
| `DIRECTIVE_RE` | `^\s*#\s*(if\|ifdef\|ifndef\|elif\|else\|endif)\b(.*)$` | Recognize directives when parsing the original file |
| `EVAL_RE` | `^\s*#\s*(if\|elif)\s+([01])\s*/\*\s*evaluated by -frewrite-includes` | Ground truth in `.i` |
| `MACRO_DEFINED_RE` | `^\s*#\s*(if\|elif)\s+defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$` | Simple `defined(X)` form |
| `MACRO_NOTDEFINED_RE` | `^\s*#\s*(if\|elif)\s+!\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?\s*$` | Simple `!defined(X)` form |
| `IFDEF_RE` / `IFNDEF_RE` | `^\s*#\s*ifdef\|ifndef\s+([A-Za-z_]\w*)\s*$` | Extract the macro name from `#ifdef/#ifndef` |

---

## 3. Step-by-step algorithm

### Step 0 — Load input & resolve filename

- Read `--cpp-file` into `lines[]` with `newline=''` (preserving the original CRLF/LF).
- [`resolve_target_filename()`](prune_macros.py#L423-L447): if `--target-name`
  does not exactly match a name in the `.i` file's line markers, fall back to matching
  by **basename** (normalizing `\` -> `/`).
  - Exactly 1 candidate -> use that candidate.
  - 0 or >1 candidates -> print the full list of filenames present in the `.i` file
    and `exit(1)`.

### Step 1 — Extract ground truth `#if/#elif` from `.i`

Function [`parse_i_eval_truths()`](prune_macros.py#L78-L110). Scans sequentially,
using 1 state variable `pending`:

1. When a line matches `EVAL_RE` -> `pending = (digit == '1')`, move to the next line.
2. The line **right after** must be a line marker `# N "file"`:
   - **Match** -> the branch body starts at line `N` of the original file, so the
     directive's own line is **`N - 1`**. Record `truths[(file, N-1)] = pending`.
   - **No match** (rare, e.g. `ShowLineMarkers` disabled) -> discard the entry
     (`pending = None`), but still try to match the current line against `EVAL_RE`.

**Result:** `truths = {(filename, directive_line_1based): bool}` — this is the
**ACTUAL GROUND TRUTH**, not a guess.

> **Assumption:** the directive fits on a single line (no line continuation via `\`).

### Step 2 — Parse the original file into a conditional block tree

#### 2a. Comment-aware scan

[`compute_line_start_in_code()`](prune_macros.py#L143-L202) scans at the
**character** level, tracking state for:

- block comment `/* */`
- string literal `"..."` (handles `\` escapes)
- char literal `'...'` (handles `\` escapes)
- line comment `//` -> `break` out for the rest of the line

Returns a `list[bool]`: whether **the start of each line** is in normal code or not.
Purpose: avoid mistaking an `#ifdef` inside a block comment for a real directive.

> **Limitation:** does not handle multi-line C++11 raw strings `R"(...)"`.

#### 2b. Build the tree using a stack

[`parse_conditional_tree()`](prune_macros.py#L205-L255):

| Directive | Action |
|---|---|
| `#if` / `#ifdef` / `#ifndef` | flush the code segment being collected -> create `Group` + first `Branch` -> append `('group', grp)` to the current output -> **push** stack |
| `#elif` / `#else` | close `content_end` of the previous branch -> create a new `Branch` -> redirect the output target of the stack top |
| `#endif` | close the last branch -> set `endif_line_idx` -> **pop** stack |

**Data structures:**

```python
@dataclass
class Branch:
    directive_line_idx: int   # 0-based index of the #if/#elif/#else line
    content_start: int        # index of the first line belonging to the branch content
    content_end: int = None   # index of the next directive line (exclusive)
    children: list = []       # nested items inside

@dataclass
class Group:
    branches: list = []
    endif_line_idx: int = None
```

The output is a list of nested items, each item being either `('code', start, end)`
or `('group', Group)`.

**Important point:** after every directive, `code_start = i + 1`, so **the directive
line is never contained in a `'code'` item** => the directive is automatically
dropped when rendering.

**Structural error** (`#elif` without a matching `#if`, extra `#endif`, missing
`#endif`) -> raises `ValueError`.

### Step 3 — Infer macros for `#ifdef` / `#ifndef`

**Problem:** Clang does **not** annotate `#ifdef/#ifndef` (there is no dedicated case
in `InclusionRewriter`'s switch, it falls into `default` -> copies verbatim regardless
of true/false) => the `.i` file gives **no true/false signal** for these two
directives.

**Solution:** [`build_macro_truth_table()`](prune_macros.py#L299-L331) walks the
entire tree, and for each branch:

- If `(file, line)` exists in `truths` **AND** the directive line has a **simple**
  form:
  - `#if defined(X)` / `#elif defined(X)` -> `macro_truth[X] = val`
  - `#if !defined(X)` / `#elif !defined(X)` -> `macro_truth[X] = not val`
- Uses `setdefault` => **first occurrence wins**.

**Assumption:** within a single build, the defined-state of macro `X` does not
change. The script does **not** handle interleaved `#undef`.

> **Quirk in the code:** after matching `defined(X)` there is a `continue`, so
> [`walk(branch.children)`](prune_macros.py#L329) is skipped => a macro nested
> **inside** an `#if defined(X)` branch will not be collected into the table.

### Step 4 — Resolve each group

[`resolve_group()`](prune_macros.py#L334-L399) walks each branch of the group:

| Directive type | Decision method |
|---|---|
| `if` / `elif` | Look up `truths[(file, line)]`. Present & `True` -> record `true_idx`. **No key present** -> add to `unresolved` |
| `ifdef X` | Look up `macro_truth[X]`. `True` -> `true_idx`. No `X` present -> `unresolved` |
| `ifndef X` | Look up `macro_truth[X]`. **`False`** -> `true_idx`. No `X` present -> `unresolved` |
| `else` | Not evaluated here — handled below by exclusion logic |

**Conclusion (in priority order):**

1. If any `unresolved` exists -> return `'UNRESOLVED'` (safer than guessing).
2. If `true_idx` exists -> return that index.
   *(Since the loop overwrites, if multiple branches are true, the **last** one wins.)*
3. No branch is true **and** the last branch is `#else` -> pick `#else`
   (the preprocessor's own exclusion logic).
4. Otherwise -> `None` = **the entire group is removed**.

### Step 5 — Render output

[`render_items()`](prune_macros.py#L402-L416), recursive:

| Item | Behavior |
|---|---|
| `('code', s, e)` | Copy `lines[s:e]` verbatim |
| `('group', grp)` -> `'UNRESOLVED'` | Copy raw `lines[#if_start : #endif+1]` — **keep everything as-is**, including nested groups |
| `('group', grp)` -> `choice is not None` | **Only** recurse into `branch.children` of the live branch => the `#if/#elif/#else/#endif` directives disappear, content is preserved byte-for-byte |
| `('group', grp)` -> `None` | Output nothing |

Writes the file using `writelines()` with `newline=''` -> preserves the original
line endings.

### Step 6 — Report

1. Print `Written: <output>  (X / Y lines remaining)`.
2. If `--defines-file` is given: [`export_defines_file()`](prune_macros.py#L274-L296)
   exports:
   - Macro `True` -> `#define X`
   - Macro `False` -> `/* #undef X */` (comment, for audit purposes only)
3. If `unresolved` is not empty: print a warning with line numbers and reasons,
   requesting manual review.

---

## 4. Data flow diagram

```
   .i file                          original .cpp/.h
      |                                  |
      v                                  v
[Step 1] parse_i_eval_truths      [Step 2a] compute_line_start_in_code
      |                                  |
      | truths                           v
      | {(file,line): bool}       [Step 2b] parse_conditional_tree
      |                                  |
      |                                  | tree: [('code',s,e) | ('group',Group)]
      |                                  |
      +---------------+------------------+
                      |
                      v
          [Step 3] build_macro_truth_table
                      |
                      | macro_truth {name: bool}
                      v
          [Step 4+5] render_items / resolve_group
                      |
        +-------------+-------------+
        v                           v
   output file              unresolved warnings
```

---

## 5. CLI modes

| Mode | Requirement | Behavior |
|---|---|---|
| `--list-files` | only needs `--i-file` | Lists every filename found in the `.i` file's line markers, then exits |
| `--explain-line N` | needs `--cpp-file` | Audits 1 line: which branch it belongs to, LIVE / DEAD / UNRESOLVED, with "evidence" (either `.i` annotation or macro inference) |
| `--defines-file` **without** `--output` | needs `--cpp-file` | Only runs Steps 1-3 and exports the macro table, without pruning any file |
| Normal | needs `--cpp-file` + `--output` | Runs the full Steps 0-6 |

### Examples

```bash
# List filenames present in .i
python prune_macros.py --i-file main.i --list-files

# Prune 1 file
python prune_macros.py --i-file main.i --cpp-file main.c --output main.filtered.c

# Prune + export the list of inferred macros
python prune_macros.py --i-file main.i --cpp-file main.c \
                       --output main.filtered.c --defines-file defines.h

# Audit line 123
python prune_macros.py --i-file main.i --cpp-file main.c --explain-line 123
```

---

## 6. Limitations to keep in mind

1. Prunes only **1 file** per run.
2. Complex conditions (e.g. `#if defined(A) && defined(B)`) can be resolved for
   **the condition itself** (thanks to the `.i` annotation), but individual macros
   **cannot** be extracted separately to feed into `macro_truth` for
   `#ifdef/#ifndef`.
3. Interleaved `#undef` -> incorrect result for `#ifdef/#ifndef`. Not handled by
   the script.
4. Multi-line C++11 raw strings `R"(...)"` can break the comment-aware scan.
5. Directives continued across lines with `\` can throw off the `N - 1` mapping in
   Step 1.
6. **MANDATORY**: rebuild with `-E` on the output file and diff against the
   original `.i` before putting it into the real codebase. This is a required
   step, not optional.
