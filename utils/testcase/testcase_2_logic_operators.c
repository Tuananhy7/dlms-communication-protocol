/*
 * TESTCASE BO 2: Toan tu logic && || voi macro duoc boc trong ngoac don
 * Seed macro: FEATURE_A duoc define (khong gia tri), FEATURE_B KHONG duoc define
 *
 * Luu y quan trong: "(FEATURE_A)" KHONG phai la defined(FEATURE_A). No la
 * bieu thuc so hoc: neu FEATURE_A la macro object-like KHONG CO GIA TRI SO
 * (vd #define FEATURE_A, khong co "1" hay gia tri gi), thi khi thay the vao
 * bieu thuc #if, no se bi thay bang RONG -> loi cu phap, hoac neu preprocessor
 * thay macro khong ton tai/khong co gia tri bang 0. Day la 1 loi rat pho bien
 * trong code nhung (nham "#if (FEATURE_A)" voi "#if defined(FEATURE_A)").
 */

/* ---- 2.1: (FEATURE_A) && (FEATURE_B) - ca hai deu la "gia tri", khong phai defined() */
#if (FEATURE_A) && (FEATURE_B)
    int code_2_1_and_bare_macros = 1;
    /* EXPECT: neu FEATURE_A la object-like macro RONG (#define FEATURE_A
     * khong co gia tri), day la LOI BIEN DICH THAT (preprocessor can gia tri
     * so sau khi macro-expand). Parser NEN canh bao "macro rong dung trong
     * bieu thuc so" thay vi am tham danh gia false. */
#endif

/* ---- 2.2: dung dung ca 2 macro co GIA TRI SO (truong hop hop le) -------- */
#if (FEATURE_A_VAL) && (FEATURE_B_VAL)
    /* Gia dinh rieng cho block nay: FEATURE_A_VAL = 1, FEATURE_B_VAL = 0 */
    int code_2_2_and_numeric_values = 1;   /* EXPECT: BI LOAI (0 && 1 = false ve mat logic;
                                               that ra 1 && 0 = 0 = false) */
#endif

/* ---- 2.3: dung defined() dung cach ket hop && --------------------------- */
#if defined(FEATURE_A) && defined(FEATURE_C_NOT_EXIST)
    int code_2_3_and_correct_defined = 1;  /* EXPECT: BI LOAI (FEATURE_C_NOT_EXIST chua define) */
#else
    int code_2_3_else = 1;                 /* EXPECT: SONG SOT */
#endif

/* ---- 2.4: || voi ca hai nhanh deu false --------------------------------- */
#if defined(FEATURE_C_NOT_EXIST) || defined(FEATURE_D_NOT_EXIST)
    int code_2_4_or_both_false = 1;        /* EXPECT: BI LOAI */
#endif

/* ---- 2.5: || voi mot nhanh true ------------------------------------------ */
#if defined(FEATURE_A) || defined(FEATURE_D_NOT_EXIST)
    int code_2_5_or_one_true = 1;          /* EXPECT: SONG SOT */
#endif

/* ---- 2.6: ket hop && || khong co ngoac phan tach ro rang (uu tien toan tu) */
#if defined(FEATURE_A) && defined(FEATURE_B) || defined(FEATURE_A)
    int code_2_6_mixed_precedence = 1;
    /* EXPECT: SONG SOT. && co do uu tien cao hon ||, nen bieu thuc duoc hieu la:
     * (defined(FEATURE_A) && defined(FEATURE_B)) || defined(FEATURE_A)
     * = (true && false) || true = false || true = true.
     * Parser PHAI cai dat dung thu tu uu tien toan tu, khong duoc xu ly
     * tuan tu tu trai qua phai don gian. */
#endif
