/*
 * TESTCASE BO 4: Directive thieu tham so / bieu thuc rong / ngoac khong can bang
 * Seed macro: FEATURE_A duoc define (khong gia tri), FEATURE_B KHONG duoc define
 *
 * Nhom nay tap trung vao cac loi cu phap THAT SU (khong phai edge-case hop le)
 * de dam bao parser KHONG crash, va bao loi ro rang thay vi am tham bo qua
 * hoac (nguy hiem hon) coi nhu dieu kien = true/false mot cach tuy tien.
 */

/* ---- 4.1: #ifdef KHONG co ten macro theo sau ----------------------------- */
/* LOI CU PHAP THAT: "#ifdef" doi hoi 1 identifier ngay sau. Neu dong nay
 * trong bo tu roi, hoac chi co khoang trang, day la loi. */
#ifdef
    int code_4_1_ifdef_no_arg = 1;
#endif

/* ---- 4.2: #ifndef KHONG co ten macro theo sau ---------------------------- */
#ifndef
    int code_4_2_ifndef_no_arg = 1;
#endif

/* ---- 4.3: #if voi bieu thuc RONG hoan toan ------------------------------- */
#if
    int code_4_3_if_empty = 1;
#endif

/* ---- 4.4: #if () - ngoac rong, khong co bieu thuc ben trong -------------- */
#if ()
    int code_4_4_if_empty_parens = 1;
#endif

/* ---- 4.5: du 1 dau dong ngoac, khong lien quan continuation -------------- */
#if ((FEATURE_A) || FEATURE_B))
    int code_4_5_extra_closing_paren = 1;
    /* EXPECT: LOI CU PHAP - dem ngoac: mo 2, dong 3, thua 1. Day la ban
     * "1 dong" cua testcase 3.2 (khong co backslash), de kiem tra parser
     * co xu ly dung KE CA KHI khong co line continuation. */
#endif

/* ---- 4.6: thieu dau ngoac dong ------------------------------------------- */
#if (FEATURE_A
    int code_4_6_missing_closing_paren = 1;
#endif

/* ---- 4.7: #elif sau khi da co #else (thu tu directive sai) -------------- */
/* Theo chuan C, #elif KHONG duoc phep xuat hien SAU #else trong cung 1
 * khoi #if. Day la loi cu phap ve THU TU directive, khac voi loi bieu thuc. */
#if defined(FEATURE_A)
    int code_4_7_if_branch = 1;
#else
    int code_4_7_else_branch = 1;
#elif defined(FEATURE_B)
    int code_4_7_elif_after_else_invalid = 1;
#endif

/* ---- 4.8: #endif du thua, khong co #if tuong ung ------------------------- */
int code_4_8_before_dangling_endif = 1;
#endif

/* ---- 4.9: thieu #endif o cuoi file (mo block nhung khong dong) ---------- */
/* Luu y: dong nay CO CHU Y de lai #if khong co #endif tuong ung, nham
 * kiem tra parser phat hien duoc "unterminated #if block" khi het file
 * (hoac het pham vi file dang xet trong 1 file .i lon hon) thay vi
 * im lang bo qua. */
#if defined(FEATURE_A)
    int code_4_9_unterminated_if_block = 1;
