#!/usr/bin/env python3
"""
prune_macros.py  (v2 - critical fix over v1)
=======================================================
Purpose: Cross-reference a .i file (preprocessed output, ARM Compiler 6 / clang -E
-frewrite-includes) against the original .cpp/.h file, to strip out
#if/#ifdef/#ifndef/#elif/#else branches that are NOT compiled for a given
product, while PRESERVING 100% of the formatting, comments, and whitespace
of the surviving branch.

=== LESSON FROM v1 (important, read before trusting the results) ===
Originally (v1) the algorithm relied on: "has a line marker (# N "file") +
has content right after it in .i" => considered 'alive'. This is WRONG.
Verified directly against Clang source code
(lib/Frontend/Rewrite/InclusionRewriter.cpp, the function handling
tok::pp_if/tok::pp_elif):

    OS << (elif ? "#elif " : "#if ") << (isTrue ? "1" : "0")
       << " /* evaluated by -frewrite-includes */" << MainEOL;

Clang prints BOTH branches (true and false) of every #if/#elif as RAW text
(complete with a full line marker) - they differ ONLY in the 0/1 right
after "#if"/"#elif" - THAT is the ONLY reliable signal, NOT whether there
is a marker/content or not (both branches have them).

=== THE CORRECT ALGORITHM (v2) ===
  1. Scan .i, find every line of the form:
         #if 0|1 /* evaluated by -frewrite-includes */
         #elif 0|1 /* evaluated by -frewrite-includes */
     The line RIGHT AFTER it (marker "# N "file"") tells us the first line
     of the branch body in the ORIGINAL file -> so the line of the
     #if/#elif directive itself is N-1. Store into dict
     {(file, directive_line): True/False}. This is the ACTUAL GROUND TRUTH
     for #if/#elif.

  2. IMPORTANT: Clang has NO special handling for #ifdef/#ifndef (no
     dedicated case in InclusionRewriter's switch - falls into default,
     just copies verbatim regardless of true/false). This means for
     #ifdef/#ifndef, .i gives NO reliable true/false signal at all.
     => For #ifdef X / #ifndef X, the algorithm tries to INFER via
     correlation: if somewhere in the SAME FILE there is a "#if defined(X)"
     or "#elif defined(X)" (giving the macro X's value) already determined
     true/false in step 1, reuse that value (whether macro X is defined
     does not change throughout a single build, except when there is an
     intervening #undef - the script does NOT handle that rare case).
     If NO correlation is found -> DO NOT GUESS, keep both the
     #ifdef/#endif and the content inside as-is in the output, with a
     clear warning at the end for the user to check manually.
     Use --defines-file <path> to EXPORT the list of inferred macros
     (defined=true) to a file, for tracking/auditing or manual
     cross-checking.

     THE ONLY EXCEPTION inferred WITHOUT needing #if defined(X) correlation:
     the classic "include guard" pattern #ifndef X / #define X (see
     function is_include_guard) - because #define X sits right inside the
     #ifndef X branch, it cannot by itself affect the outcome of its own
     check, so we infer that X was definitely NOT defined earlier IN THIS
     FILE. Unlike ordinary inferred macros (WRITTEN INTO macro_truth then
     the directive is DELETED as a normally resolved group), the include
     guard is handled SEPARATELY: resolve_group returns it via a dedicated
     'GUARD' sentinel: NO warning, but the #ifndef/#endif lines are KEPT
     (not deleted) - only the content INSIDE continues to be recursively
     pruned as normal. Reason for keeping rather than deleting: a header
     often wraps its ENTIRE body in a single include guard; if this
     directive were fully deleted (as with a normally "resolved" group)
     that would be harmless content-wise, but treating it as an ordinary
     inferred macro and getting it WRONG (e.g. the macro name coincidentally
     matches some other, more complex condition) is far riskier than just
     keeping these 2 harmless directive lines.

     A SECOND EXCEPTION (same 'GUARD' sentinel): #ifdef/#ifndef with a
     macro name in KNOWN_BUILTIN_MACROS (currently: __cplusplus) - this is
     a macro predefined by the COMPILER, not by the codebase, so it can
     NEVER be correlated via "#if defined(X)" elsewhere (since #ifdef X is
     the ONLY way to test it). If the group has just 1 simple branch
     (#ifdef __cplusplus / #endif, no #else), handle it like an include
     guard: keep the directive, no warning, still recurse into the
     content. If the group has multiple branches (e.g. an #else), no
     branch can be chosen to recurse into -> return 'SILENT_UNRESOLVED':
     keep the WHOLE GROUP as-is (like UNRESOLVED) but WITHOUT a warning
     (since this is a KNOWN, expected case).

  3. Parse the original .cpp/.h file into a conditional-block tree (like
     v1, comment-aware to avoid mistaking an #ifdef inside /* */ for a real
     one). A directive spanning multiple physical lines joined by a
     trailing '\\' is GROUPED into a single logical block (see
     directive_end_line_idx/directive_full_text) - both when cross-checking
     ground truth (.i annotates at the LAST PHYSICAL line of the directive,
     not the first) and when splitting out the branch body (continuation
     lines are not counted as code).

  4. For each group (#if/.../#endif), use the result of steps 1+2 to pick
     exactly 1 surviving branch, delete the other branches AND delete the
     directive.

=== THINGS TO KEEP IN MIND ===
  - Only processes 1 target .cpp/.h file at a time.
  - ALWAYS rebuild (-E) the output file and diff it against the original
    .i to confirm before using it in the real codebase - this is a
    MANDATORY step, not optional.
  - Complex conditions (e.g. "#if defined(A) && defined(B)") CANNOT be
    broken down into individual macros for #ifdef correlation - only the
    simple forms are supported: defined(X), !defined(X), or a bare macro
    after ifdef/ifndef.
  - An include guard is only recognized when the group has just 1
    #ifndef branch (no #elif/#else) AND the first content line is a
    #define of the same name. Does NOT require being TOP-LEVEL - an
    include guard nested inside another condition is still recognized
    under the same criteria. If it does not match both conditions, it
    still falls back to the normal handling path (may end up UNRESOLVED
    and warn as before).
"""

import re
import sys
import os
from dataclasses import dataclass, field

LINE_MARKER_RE = re.compile(r'^#\s+(\d+)\s+"((?:[^"\\]|\\.)*)"\s*(.*)$')
DIRECTIVE_RE = re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)$')
EVAL_RE = re.compile(r'^\s*#\s*(if|elif)\s+([01])\s*/\*\s*evaluated by -frewrite-includes')


# ---------------------------------------------------------------------------
# STEP 1: Read ground-truth true/false for each #if/#elif from the real annotation
# ---------------------------------------------------------------------------

def parse_i_eval_truths(i_path):
    """
    Returns dict {(filename, directive_line_1based): bool}
    Based directly on Clang's "evaluated by -frewrite-includes" annotation -
    this is GROUND TRUTH, not a guess.
    """
    truths = {}
    pending = None  # bool waiting for the confirming line marker

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
                    # No marker found right after (rare - e.g. ShowLineMarkers
                    # disabled). Skip, this entry cannot be recorded.
                    pending = None

            m2 = EVAL_RE.match(line)
            if m2:
                pending = (m2.group(2) == '1')
                continue

    return truths


def list_filenames_in_i(i_path):
    """Debug helper: list every filename that appears in .i's line markers"""
    names = set()
    with open(i_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        for raw in f:
            m = LINE_MARKER_RE.match(raw.rstrip('\r\n'))
            if m:
                names.add(m.group(2))
    for n in sorted(names):
        print(n)


# ---------------------------------------------------------------------------
# STEP 3: Parse .cpp/.h into a conditional-block tree (comment-aware)
# ---------------------------------------------------------------------------

@dataclass
class Branch:
    directive_line_idx: int          # 0-based index of the #if/#elif/#else line
    content_start: int               # index of the first line belonging to the branch's content
    content_end: int = None          # index of the next directive line (exclusive)
    children: list = field(default_factory=list)


@dataclass
class Group:
    branches: list = field(default_factory=list)
    endif_line_idx: int = None


def compute_line_start_in_code(lines):
    """
    Scans the whole file at the character level, tracking block comments
    /* */, strings, and char literals. Returns list[bool]: whether the
    START of each line is in normal code or not - to avoid mistaking an
    #ifdef sitting inside a comment for a real one.
    Limitation: does not handle multi-line C++11 raw strings R"(...)"
    (rare in embedded code).
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
    Returns the (0-based) index of the LAST PHYSICAL line belonging to
    this directive, counting lines joined by a trailing '\\' (line
    continuation). If the directive spans only 1 line, returns start_idx
    itself.

    IMPORTANT: when an #if/#elif/#ifdef/#ifndef spans multiple physical
    lines via '\\', Clang/-frewrite-includes COLLAPSES the whole thing
    into a single "#if 0/1 ..." annotation line in .i, then COPIES
    CONTENT STARTING FROM THE LAST LINE of the original directive (not
    the first "#if"/"#elif" line). So the ground truth from Step 1
    (body_line - 1) points to the LAST line of the directive, and every
    place that cross-checks truths[] must use this line, not
    directive_line_idx (the first line) - otherwise it will be off and
    incorrectly report "no evaluated entry found in .i".
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
                    raise ValueError(f"#{kind} has no matching #if at line {i+1}")
                grp, _ = stack[-1]
                grp.branches[-1].content_end = i
                branch = Branch(directive_line_idx=i, content_start=end_idx + 1)
                grp.branches.append(branch)
                stack[-1] = (grp, branch.children)
            elif kind == 'endif':
                if not stack:
                    raise ValueError(f"stray #endif at line {i+1}")
                grp, _ = stack.pop()
                grp.branches[-1].content_end = i
                grp.endif_line_idx = i
            code_start = end_idx + 1
            i = end_idx
        i += 1

    flush_code(n)
    if stack:
        raise ValueError("Missing #endif - check the file again, there may be an #if inside a string/comment causing a false match")
    return root


# ---------------------------------------------------------------------------
# STEP 2 + 4: Correlate macro names for #ifdef/#ifndef, then resolve + render
# ---------------------------------------------------------------------------

# Optional trailing comment suffix (/* ... */ or // ...) after a directive -
# a very common idiom (e.g. "#ifndef X /* X */", "#endif // X") that the
# simple directive regexes still need to recognize; they can't require $
# right after the macro name.
TRAILING_COMMENT_SUFFIX = r'\s*(?:/\*.*\*/\s*|//.*)?$'

MACRO_DEFINED_RE = re.compile(r'^\s*#\s*(if|elif)\s+defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?' + TRAILING_COMMENT_SUFFIX)
MACRO_NOTDEFINED_RE = re.compile(r'^\s*#\s*(if|elif)\s+!\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?' + TRAILING_COMMENT_SUFFIX)
IFDEF_RE = re.compile(r'^\s*#\s*ifdef\s+([A-Za-z_]\w*)' + TRAILING_COMMENT_SUFFIX)
IFNDEF_RE = re.compile(r'^\s*#\s*ifndef\s+([A-Za-z_]\w*)' + TRAILING_COMMENT_SUFFIX)

# Macros predefined by the COMPILER/LANGUAGE itself, NOT macros of the
# codebase - so they can never be correlated via "#if defined(X)"
# elsewhere in the file (since #ifdef X is the ONLY way C/C++ code tests
# for its existence; nobody "#define __cplusplus"). Its actual value
# depends on the language/compiler used to build this file (e.g.
# __cplusplus is only defined when compiling as C++), which is OUTSIDE
# the STATIC inference scope of a single file. When an #ifdef/#ifndef
# with a macro name in this list is encountered with no other evidence,
# the script does NOT warn (since this is a KNOWN case, not an inference
# failure), and still KEEPS the directive (safe, same as an include guard).
KNOWN_BUILTIN_MACROS = {'__cplusplus'}
DIRECTIVE_KIND_RE = re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else)\b')
DEFINE_NAME_RE = re.compile(r'^\s*#\s*define\s+([A-Za-z_]\w*)\b')


def directive_kind(line):
    m = DIRECTIVE_KIND_RE.match(line)
    return m.group(1) if m else None


def directive_full_text(lines, start_idx, end_idx):
    """
    Joins the physical lines from start_idx to end_idx (inclusive) into a
    single logical string, stripping the '\\' continuation character and
    newline, used to match the simple condition regexes (defined(X),
    ifdef X...) when a directive spans multiple physical lines.
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
    Recognizes the classic "include guard" pattern of a header file:
        #ifndef X
        #define X
        ...
        #endif
    (no #elif/#else). This is the MOST COMMON idiom in C/C++ headers,
    recognized by EVERY compiler.

    Why this inference is safe: Clang does not annotate #ifdef/#ifndef
    (see the file's top docstring), so normally the script has NO
    evidence at all for #ifndef X unless X has appeared elsewhere as
    #if defined(X)/#elif defined(X). But with exactly this pattern, the
    #define X line sits RIGHT INSIDE the #ifndef X branch - meaning,
    within the scope of this file, X could ONLY have been defined at
    that very line. Since #define X comes AFTER the #ifndef X check
    point, it cannot affect the outcome of its own check => at the
    moment #ifndef is evaluated, X is CERTAINLY NOT defined by ANYTHING
    earlier IN THIS FILE => the #ifndef branch is always the live branch.
    (Rare case: X was already -D'd from an external compiler flag, or
    this header was already included earlier in the same translation
    unit - both fall outside the scope of the single file this script
    processes.)

    NOTE: unlike the normal macro-inference path (writing the value into
    macro_truth and letting resolve_group pick the live branch and
    DELETE the directive), an include guard is handled SEPARATELY:
    resolve_group returns the 'GUARD' sentinel and render_items KEEPS
    the #ifndef/#endif lines (does not delete them), only recursing
    normally into the content INSIDE. Reason: a header typically wraps
    its ENTIRE body in a single include guard - fully deleting this
    directive (as with a normally "resolved" group) would be harmless
    content-wise, but treating it as an ordinary inferred macro and
    getting it WRONG (e.g. the macro name happens to coincide with some
    other, more complex condition) is far riskier than just keeping
    these 2 harmless directive lines.
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
    Exports the list of macros inferred via #if defined(X)/
    #elif defined(X) correlation in the original file, cross-checked
    against the "evaluated by -frewrite-includes" annotation in .i.
    - Macro TRUE (defined)      -> written as "#define X"
    - Macro FALSE (not defined) -> written as a comment "/* #undef X */"
      for tracking/audit purposes, has no effect when read back.
    This file can be used as a reference or shared between different
    runs on the same codebase/build config.
    """
    defined = sorted(m for m, v in macro_truth.items() if v)
    undefined = sorted(m for m, v in macro_truth.items() if not v)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("/* Exported by prune_macros.py - macros inferred from .i (-frewrite-includes) */\n")
        f.write("/* Macros DEFINED (evaluated = 1): */\n")
        for m in defined:
            f.write(f"#define {m}\n")
        f.write("\n/* Macros NOT defined (evaluated = 0), for reference only: */\n")
        for m in undefined:
            f.write(f"/* #undef {m} */\n")
    print(f"Exported defines-file: {output_path}  ({len(defined)} macros defined, {len(undefined)} macros undefined)")
    return output_path


def build_macro_truth_table(tree, lines, target_fname, truths):
    """
    Walks the whole tree; for every #if/#elif branch with a SIMPLE form
    "defined(X)" or "!defined(X)" AND with ground-truth from step 1,
    infers whether X is defined or not. Returns dict {macro_name: bool}.
    Used to resolve #ifdef/#ifndef later (a macro with the same name has
    the same defined-state throughout a single build, except for an
    intervening #undef - not handled here).

    NOTE: an include guard (#ifndef X / #define X) does NOT go through
    this table - it is recognized separately by resolve_group via
    is_include_guard() and handled with the 'GUARD' sentinel (directive
    kept, still recurses into content).
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
    Returns the index of the 'live' branch in grp.branches, or None if
    no branch is live (e.g. #if false, no #else), or 'UNRESOLVED' if
    there is an #ifdef/#ifndef branch that cannot be determined -> in
    that case KEEP the whole group AS-IS (safer than guessing), or
    'GUARD' if this is a classic include guard (#ifndef X / #define X)
    or the group has just 1 #ifdef/#ifndef branch whose macro name is
    in KNOWN_BUILTIN_MACROS (see is_include_guard) - both cases produce
    NO warning, and render_items will KEEP the #ifdef|#ifndef/#endif
    lines but still recurse into the content to keep pruning normally.
    If the group has multiple branches (has an #else) and still cannot
    be resolved because of a builtin macro, returns 'SILENT_UNRESOLVED'
    - keeps the WHOLE GROUP (cannot pick a branch to recurse into) but
    also produces NO warning.
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
        # The ground truth in .i points to the LAST PHYSICAL line of the
        # directive (see directive_end_line_idx), not the first line - a
        # directive joined across multiple lines by '\' must be
        # cross-checked using end_idx + 1.
        key = (target_fname, end_idx + 1)
        display_text = line.strip() if end_idx == branch.directive_line_idx else full_text

        if kind in ('if', 'elif'):
            if key in truths:
                if truths[key]:
                    true_idx = idx
                continue
            else:
                has_unresolved = True
                unresolved.append((start_line_1based, display_text, 'no evaluated entry found in .i'))
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
                                    f"cannot infer macro '{macro}' - .i does not annotate #ifdef, and no correlating #if defined({macro}) was found in this file"))
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
                                    f"cannot infer macro '{macro}' - .i does not annotate #ifndef, and no correlating #if defined({macro}) was found in this file"))
            continue

        # kind == 'else': has no condition of its own, handled by
        # elimination below (nothing to do here)

    if has_unresolved:
        return 'UNRESOLVED'

    if true_idx is not None:
        return true_idx

    # No if/elif/ifdef/ifndef branch was true -> if there is a trailing
    # #else, that's the live branch (same elimination logic the
    # preprocessor itself uses).
    last_line = lines[grp.branches[-1].directive_line_idx]
    if directive_kind(last_line) == 'else':
        return len(grp.branches) - 1

    if has_silent_unresolved:
        # Only branches that could not be resolved due to a builtin
        # macro (e.g. __cplusplus) remain - no warning. If the group has
        # just 1 simple branch (e.g. "#ifdef __cplusplus / #endif"), it's
        # safe to KEEP the directive and still recurse into the content
        # (same as GUARD). If there are multiple branches (e.g. an
        # #else), no branch can be chosen to recurse into -> keep the
        # WHOLE GROUP, no warning.
        if len(grp.branches) == 1:
            return 'GUARD'
        return 'SILENT_UNRESOLVED'

    return None  # no branch is live, the whole group is dropped


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
                # Include guard or a known builtin #ifdef/#ifndef macro
                # (e.g. __cplusplus): keep the #ifdef|#ifndef/#endif
                # lines, still recurse into the content inside to keep
                # pruning normally.
                branch = grp.branches[0]
                directive_end = directive_end_line_idx(lines, branch.directive_line_idx)
                out.extend(lines[branch.directive_line_idx:directive_end + 1])
                render_items(branch.children, lines, target_fname, truths, macro_truth, unresolved, out)
                out.extend(lines[grp.endif_line_idx:grp.endif_line_idx + 1])
            elif choice is not None:
                branch = grp.branches[choice]
                render_items(branch.children, lines, target_fname, truths, macro_truth, unresolved, out)


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def resolve_target_filename(i_path, target_fname_in_i, truths):
    """
    If the name does not match EXACTLY (case-sensitive), try to find it by:
      1. Full path, CASE-INSENSITIVE.
      2. Basename (normalized '\\' -> '/'), also CASE-INSENSITIVE.
    Why steps 1+2 need to be case-insensitive: Windows filesystems are
    case-insensitive, so .i (line markers usually auto-generated by the
    preprocessor, often lowercase like "main.c") and the --cpp-file the
    user passes in (which may be uppercase, e.g. "MAIN.c") often point to
    the SAME physical file despite differing in case.
    """
    all_files = set(f for (f, _) in truths.keys())
    # Also add filenames from plain markers (the case where the file has
    # no #if/#elif at all - e.g. a pure declaration header).
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

    print("NO MATCHING filename found in .i. Filenames present in .i:")
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

    print(f"Written: {output_path}  ({len(out)} / {len(lines)} lines remaining)")

    if defines_file:
        export_defines_file(macro_truth, defines_file)

    if unresolved:
        print()
        print(f"!!! WARNING: {len(unresolved)} #ifdef/#ifndef/#if block(s) could NOT be inferred, KEPT AS-IS in the output, you need to check manually:")
        for line_no, text, reason in unresolved:
            print(f"  Line {line_no}: {text}")
            print(f"    -> {reason}")

    return output_path


def explain_line(cpp_path, i_path, target_fname_in_i, line_no):
    """
    Audit: tells you which branch a given (1-based) line in the original
    file belongs to, and how that branch was resolved as live/dead/
    unresolved.
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
                    return None  # outside every group, always live
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
        print(f"Line {line_no}: OUTSIDE every #if/#ifdef block (unconditional code) -> ALWAYS LIVE.")
        return

    grp, bi, branch, path = result
    choice = resolve_group(grp, lines, target_fname_in_i, truths, macro_truth, unresolved)
    line_text = lines[branch.directive_line_idx].rstrip('\r\n')
    end_idx = directive_end_line_idx(lines, branch.directive_line_idx)
    full_text = directive_full_text(lines, branch.directive_line_idx, end_idx)
    span = f"{branch.directive_line_idx+1}-{end_idx+1}" if end_idx != branch.directive_line_idx else f"{branch.directive_line_idx+1}"
    print(f"Line {line_no} belongs to branch: {line_text.strip()}  (directive at line {span})")

    if choice == 'UNRESOLVED':
        print("CONCLUSION: UNRESOLVED - could not be inferred, the script will KEEP this block as-is.")
        for ln, txt, reason in unresolved:
            print(f"  Line {ln}: {txt}\n    -> {reason}")
        return
    elif choice == 'GUARD':
        print("CONCLUSION: GUARD (classic include guard, or a known builtin #ifdef/#ifndef")
        print("  macro like __cplusplus) - the directive is KEPT, not deleted, no warning;")
        print("  content inside is still pruned normally.")
        return
    elif choice == 'SILENT_UNRESOLVED':
        print("CONCLUSION: SILENT_UNRESOLVED (a known builtin macro like __cplusplus, but the")
        print("  group has multiple branches so no single branch can be chosen to recurse into)")
        print("  - the WHOLE GROUP is kept as-is, no warning.")
        return
    elif choice == bi:
        print("CONCLUSION: LIVE (this branch was chosen).")
    else:
        print("CONCLUSION: DEAD (a DIFFERENT branch in the same group is the live one).")

    key = (target_fname_in_i, end_idx + 1)
    if key in truths:
        print(f"Evidence: 'evaluated by -frewrite-includes' annotation at .i line {end_idx+1} => {'1 (true)' if truths[key] else '0 (false)'}")
    else:
        kind = directive_kind(line_text)
        if kind in ('ifdef', 'ifndef'):
            m = IFDEF_RE.match(full_text) or IFNDEF_RE.match(full_text)
            macro = m.group(1) if m else None
            if macro in macro_truth:
                print(f"Evidence: inferred via macro name '{macro}' (found #if defined({macro}) elsewhere in the file, value: {macro_truth[macro]})")
            else:
                print(f"Evidence: NONE - macro '{macro}' does not appear as #if defined(...) anywhere else in this file.")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--i-file', required=True, help='.i file (preprocessed output, -frewrite-includes)')
    ap.add_argument('--cpp-file', help='Original .cpp/.h file to prune')
    ap.add_argument('--target-name', help='Filename as used in .i line markers (default = --cpp-file)')
    ap.add_argument('--output', help='Output file')
    ap.add_argument('--list-files', action='store_true', help='List filenames present in .i, then exit')
    ap.add_argument('--explain-line', type=int, help='Audit one specific (1-based) line in --cpp-file')
    ap.add_argument('--defines-file', help='OUTPUT path: export the list of inferred macros (defined=true, via cross-checking #if defined(X) in --cpp-file against the "evaluated by -frewrite-includes" annotation in .i)')
    args = ap.parse_args()

    if args.list_files:
        list_filenames_in_i(args.i_file)
        sys.exit(0)

    if args.explain_line is not None:
        if not args.cpp_file:
            ap.error('--cpp-file is required when using --explain-line')
        target = args.target_name or args.cpp_file
        explain_line(args.cpp_file, args.i_file, target, args.explain_line)
        sys.exit(0)

    if args.defines_file and not args.output:
        # defines-file-only mode, does not prune any file.
        if not args.cpp_file:
            ap.error('--cpp-file is required when using --defines-file')
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
        ap.error('--cpp-file and --output are required (unless using --list-files/--explain-line/--defines-file standalone)')

    target = args.target_name or args.cpp_file
    prune_file(args.cpp_file, args.i_file, target, args.output, args.defines_file)
