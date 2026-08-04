/*
 * TESTCASE BO 3: Line continuation (backslash + newline) trong bieu thuc #if
 * Seed macro: FEATURE_A duoc define (khong gia tri), FEATURE_B KHONG duoc define
 *
 * Preprocessor chuan coi 1 dong logic la toan bo chuoi cac dong vat ly noi voi
 * nhau bang '\' o cuoi dong (khong co ky tu nao khac sau '\', ke ca space/tab
 * - neu co trailing whitespace sau '\' thi mot so compiler van chap nhan (GCC
 * warning) nhung mot so thi bao loi). Parser can GOM cac dong lai truoc khi
 * tokenize, khong duoc xu ly tung dong vat ly rieng le.
 */

/* ---- 3.1: && bi ngat dong bang backslash, thut le bang tab -------------- */
#if (FEATURE_A) && \
	(FEATURE_B)
    int code_3_1_and_continuation_tab = 1;
    /* EXPECT: phai duoc GOM thanh "#if (FEATURE_A) && (FEATURE_B)" truoc khi
     * danh gia. Ve mat gia tri giong testcase 2.1 (macro rong dung trong bieu
     * thuc so -> can canh bao, khong am tham false). */
#endif

/* ---- 3.2: || bi ngat dong, co du them dau ngoac dong khong can bang ----- */
#if ((FEATURE_A) || \
	FEATURE_B))
    int code_3_2_or_continuation_extra_paren = 1;
    /* EXPECT: LOI CU PHAP that su (thua 1 dau ')' o cuoi). Sau khi gom dong,
     * bieu thuc la "((FEATURE_A) || FEATURE_B))" - dem ngoac: mo 2, dong 3
     * -> khong can bang. Parser PHAI bao loi "unbalanced parentheses", KHONG
     * duoc bo qua dau ')' du hoac im lang danh gia mot phan bieu thuc. */
#endif

/* ---- 3.3: bi ngat dong, thieu 1 dau ngoac dong o cuoi -------------------- */
#if (FEATURE_A) || \
	FEATURE_B)
    int code_3_3_or_continuation_missing_open = 1;
    /* EXPECT: LOI CU PHAP. Sau khi gom dong: "(FEATURE_A) || FEATURE_B)".
     * Dem ngoac: mo 1, dong 2 -> du 1 dau dong, khong can bang.
     * Parser PHAI bao loi ro rang, chi ra vi tri (dong goc + noi dung) de
     * nguoi dung de dang tim va sua trong file that. */
#endif

/* ---- 3.4: line continuation hop le, dung defined(), nhieu dong ---------- */
#if defined(FEATURE_A) && \
    !defined(FEATURE_B) && \
    defined(FEATURE_A)
    int code_3_4_valid_multiline_defined = 1;  /* EXPECT: SONG SOT (true && true && true) */
#endif

/* ---- 3.5: backslash o cuoi dong nhung co trailing space sau backslash --- */
/* CANH BAO: dong duoi day co 1 khoang trang SAU dau '\' truoc khi xuong dong.
 * Ve mat ky thuat day la hanh vi "undefined/khong khuyen khich" - mot so
 * compiler van noi dong (co warning), mot so coi '\' khong con hieu luc noi
 * dong nua vi khong phai ky tu cuoi cung tren dong. Parser NEN it nhat canh
 * bao truong hop nay thay vi am tham xu ly sai. */
#if defined(FEATURE_A) && \ 
    defined(FEATURE_A)
    int code_3_5_trailing_space_after_backslash = 1;
#endif
