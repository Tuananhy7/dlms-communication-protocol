/*
 * TESTCASE BO 1: Cac bien the cu phap cua "defined"
 * Seed macro: FEATURE_A duoc define (khong gia tri), FEATURE_B KHONG duoc define
 *
 * Muc dich: kiem tra parser co xu ly dung tat ca cac cach viet defined() khac nhau
 * ma lap trinh vien hay dung, ke ca truong hop rong/khong hop le.
 */

/* ---- 1.1: defined() RONG - khong co ten macro ben trong ----------------- */
/* Day la cu phap KHONG HOP LE theo chuan C. Mot preprocessor that (armclang/gcc)
 * se bao loi "operator 'defined' requires an identifier". Parser cua ban NEN
 * phat hien va bao loi ro rang, KHONG duoc am tham coi la false roi chay tiep. */
#if defined()
    int code_1_1_should_be_syntax_error = 1;
#endif

/* ---- 1.2: defined(MACRO) - cu phap chuan, khong co khoang trang --------- */
#if defined(FEATURE_A)
    int code_1_2_defined_paren_no_space = 1;   /* EXPECT: SONG SOT (FEATURE_A da define) */
#endif

/* ---- 1.3: defined (MACRO) - co khoang trang giua defined va ( ----------- */
#if defined (FEATURE_A)
    int code_1_3_defined_paren_with_space = 1; /* EXPECT: SONG SOT */
#endif

/* ---- 1.4: defined MACRO - khong co dau ngoac, van hop le theo C chuan --- */
#if defined FEATURE_A
    int code_1_4_defined_no_paren = 1;         /* EXPECT: SONG SOT */
#endif

/* ---- 1.5: !defined(MACRO) - phu dinh ------------------------------------ */
#if !defined(FEATURE_B)
    int code_1_5_not_defined_featureB = 1;     /* EXPECT: SONG SOT (FEATURE_B chua define) */
#endif

/* ---- 1.6: !defined(MACRO) voi macro DA duoc define ---------------------- */
#if !defined(FEATURE_A)
    int code_1_6_not_defined_featureA = 1;     /* EXPECT: BI LOAI (FEATURE_A da define) */
#endif

/* ---- 1.7: defined long trong bieu thuc && -------------------------------- */
#if defined(FEATURE_A) && defined(FEATURE_B)
    int code_1_7_and_mixed = 1;                /* EXPECT: BI LOAI (FEATURE_B chua define) */
#else
    int code_1_7_else_branch = 1;              /* EXPECT: SONG SOT */
#endif

/* ---- 1.8: defined viet HOA/thuong khac chuan (nham lan thuong gap) ------ */
/* "Defined" (D hoa) KHONG phai la tu khoa preprocessor hop le.
 * Mot preprocessor that se coi day la mot macro ten "Defined" (thuong khong
 * ton tai) roi ap dung cho FEATURE_A - dan den loi cu phap vi thieu toan tu. */
#if Defined(FEATURE_A)
    int code_1_8_wrong_case_should_error = 1;
#endif
