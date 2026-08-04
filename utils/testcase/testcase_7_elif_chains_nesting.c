/*
 * TESTCASE BO 7: Chuoi #elif va cac khoi long nhau (nested) nhieu tang
 * Macro duoc #define ngay trong file (self-contained).
 *
 * Rule quan trong nhat can test o bo nay (hay bi lam sai nhat khi tu viet
 * parser): trong 1 nhanh #if/#elif dang o TRANG THAI BI BO QUA (skip-mode -
 * vi dieu kien cua no hoac cua khoi cha da la false, hoac 1 nhanh phia truoc
 * trong cung chuoi elif da duoc chon), preprocessor CHUAN chi quet cac dong
 * bat dau bang # de dem do sau long nhau #if/#ifdef/#ifndef...#endif cho
 * CAN BANG - no KHONG HE danh gia/parse bieu thuc dieu kien cua cac #elif
 * hay #if nam trong vung bi skip. Nghia la 1 bieu thuc bi loi cu phap nam
 * trong nhanh khong duoc chon SE KHONG GAY LOI GI CA.
 */

/* ---- 7.1: chuoi if/elif/elif/else - chi nhanh gan cuoi la true ----------- */
#define LEVEL 3

#if LEVEL == 1
    int code_7_1_branch_level1 = 1;
#elif LEVEL == 2
    int code_7_1_branch_level2 = 1;
#elif LEVEL == 3
    int code_7_1_branch_level3 = 1;        /* EXPECT: SONG SOT (LEVEL == 3) */
#elif LEVEL == 4
    int code_7_1_branch_level4 = 1;
#else
    int code_7_1_branch_else = 1;
#endif

/* ---- 7.2: nhanh dau tien true -> cac elif phia sau (KE CA LOI CU PHAP)
 *           trong vung bi skip TUYET DOI KHONG duoc gay loi ---------------- */
#define PICK_FIRST 1
#if PICK_FIRST == 1
    int code_7_2_first_branch_taken = 1;   /* EXPECT: SONG SOT */
#elif ((( invalid syntax here that should NEVER be parsed )))
    int code_7_2_should_never_be_reached = 1;
    /* EXPECT: khoi nay bi skip HOAN TOAN. Bieu thuc #elif ((( ... o tren la
     * loi cu phap RO RANG (ngoac khong can bang, token la), NHUNG vi nhanh
     * #if PICK_FIRST == 1 da duoc chon TRUOC do trong cung chuoi if/elif,
     * nen bieu thuc nay KHONG DUOC DANH GIA. Parser NEU bao loi cu phap tai
     * day la SAI - day la 1 loi rat pho bien khi tu viet preprocessor:
     * quen rang skip-mode chi can dem # de can bang, khong can parse dung
     * bieu thuc dieu kien. */
#endif

/* ---- 7.3: long 3 tang #ifdef, chi hang cuoi cung dinh nghia moi song sot */
#define OUTER_ENABLE
#define MIDDLE_ENABLE
/* INNER_ENABLE KHONG duoc define */

#ifdef OUTER_ENABLE
    int code_7_3_outer_level = 1;          /* EXPECT: SONG SOT */
    #ifdef MIDDLE_ENABLE
        int code_7_3_middle_level = 1;     /* EXPECT: SONG SOT */
        #ifdef INNER_ENABLE
            int code_7_3_inner_level = 1;  /* EXPECT: BI LOAI (INNER_ENABLE chua define) */
        #else
            int code_7_3_inner_else = 1;   /* EXPECT: SONG SOT */
        #endif
    #endif
#endif

/* ---- 7.4: skip-inside-skip - tang ngoai false thi TOAN BO tang trong,
 *           du co bao nhieu loi cu phap, cung khong duoc dong den ---------- */
#define OUTER_DISABLED_CHECK 0
#if OUTER_DISABLED_CHECK
    int code_7_4_outer_never_taken = 1;

    /* Toan bo cum duoi day co CHU Y viet sai/loi de kiem tra parser co
     * "lo" di vao danh gia hay khong khi no dang nam trong vung bi skip
     * boi dieu kien #if OUTER_DISABLED_CHECK (= 0) o tren. */
    #ifdef
        int code_7_4_malformed_ifdef_inside_skip = 1;
    #endif

    #if ((( totally broken +++ )))
        int code_7_4_malformed_if_inside_skip = 1;
    #endif
#else
    int code_7_4_outer_else_taken = 1;     /* EXPECT: SONG SOT */
#endif

/* ---- 7.5: ket hop #ifdef long voi #if defined o cac tang khac nhau ------ */
#define COMBO_A
#define COMBO_B

#ifdef COMBO_A
    #if defined(COMBO_B) && !defined(COMBO_C_NOT_EXIST)
        int code_7_5_deep_combo = 1;       /* EXPECT: SONG SOT */
    #else
        int code_7_5_deep_combo_else = 1;
    #endif
#endif
