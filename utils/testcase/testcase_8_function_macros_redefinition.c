/*
 * TESTCASE BO 8: Macro function-like trong #if, va quy tac define-lai (redefinition)
 * Macro duoc #define ngay trong file (self-contained).
 */

/* ---- 8.1: function-like macro duoc GOI DUNG cu phap (co dau ngoac + tham so) */
#define ADD_ONE(x) ((x) + 1)
#if ADD_ONE(2) > 2
    int code_8_1_function_macro_called_correctly = 1;
    /* EXPECT: SONG SOT. ADD_ONE(2) duoc macro-expand thanh ((2) + 1) = 3,
     * bieu thuc tro thanh "#if 3 > 2" -> true. Function-like macro CO the
     * dung trong #if, mien la duoc GOI dung cu phap (ten macro theo sau boi
     * dau '(' ngay lap tuc, khong co khoang trang lam sai lech - thuc ra co
     * khoang trang giua ten va '(' van hop le, chi can khong bi ngat dong
     * boi token khac). */
#endif

/* ---- 8.2: GOTCHA - ten function-like macro dung KHONG kem dau ngoac goi -- */
#define IS_ENABLED(x) 1
#if IS_ENABLED > 0
    int code_8_2_function_macro_name_without_call = 1;
    /* EXPECT: BI LOAI (theo dung chuan, nhung ly do rat de bi hieu nham).
     * Vi "IS_ENABLED" xuat hien KHONG co dau '(' theo ngay sau, day KHONG
     * duoc coi la 1 loi goi ham macro - theo chuan C, function-like macro
     * CHI duoc thay the khi ten cua no duoc theo sau boi '('. Neu khong,
     * ten macro giu nguyen dang identifier "IS_ENABLED" chua duoc thay the,
     * roi theo rule o Bo 6 (6.6/6.7), no bi thay bang 0 vi khong con la
     * "macro co the thay the duoc" trong ngu canh nay -> "#if 0 > 0" -> false.
     * Day la 1 trong nhung loi PHO BIEN NHAT khi lap trinh vien nham lan
     * cach dung function-like macro trong dieu kien bien dich. */
#endif

/* ---- 8.3: define lai macro VOI GIA TRI GIONG HET (hop le, khong loi) ---- */
#define REPEAT_VALUE 100
#define REPEAT_VALUE 100
#if REPEAT_VALUE == 100
    int code_8_3_identical_redefinition = 1;
    /* EXPECT: SONG SOT, VA KHONG duoc bao loi/canh bao. Theo chuan C 6.10.3p2,
     * define lai 1 macro voi noi dung THUC SU GIONG HET (tung token, tung
     * khoang trang tuong duong) la HOP LE, khong phai vi pham. */
#endif

/* ---- 8.4: define lai macro VOI GIA TRI KHAC (VI PHAM chuan, phai canh bao) */
#define CONFLICT_VALUE 1
#define CONFLICT_VALUE 2
    /* EXPECT: day la VI PHAM chuan C that su (6.10.3p2) - "redefinition of
     * macro CONFLICT_VALUE with a different replacement list". Cac compiler
     * that (gcc/armclang) se canh bao/loi tai day. Parser NEN phat hien va
     * bao loi ngay tai dong #define thu 2, KHONG duoc am tham lay gia tri
     * moi nhat (2) ma khong canh bao gi - vi day thuong la dau hieu 2 header
     * xung dot dinh nghia macro (rat hay gap khi gop nhieu thu vien/module). */
#if CONFLICT_VALUE == 2
    int code_8_4_after_conflicting_redefinition = 1;
    /* Du parser co the van lay gia tri sau cung (2, theo hanh vi thuc te cua
     * hau het compiler khi ha xuong warning thay vi error), NHUNG bat buoc
     * phai co canh bao rieng cho viec redefinition khac gia tri o dong tren. */
#endif

/* ---- 8.5: #undef roi define lai voi gia tri khac (HOP LE, khong loi) ----- */
#define RETRY_VALUE 1
#undef RETRY_VALUE
#define RETRY_VALUE 2
#if RETRY_VALUE == 2
    int code_8_5_undef_then_redefine = 1;
    /* EXPECT: SONG SOT, KHONG loi. #undef truoc khi #define lai la cach lam
     * DUNG chuan de thay doi gia tri macro, khac han voi 8.4 (define chong
     * len nhau ma khong #undef truoc). */
#endif

/* ---- 8.6: macro chain nhieu tang thuan object-like (A -> B -> C -> 1) --- */
/* Day chinh la mo hinh "macro noi duoi nhau" ban mo ta o yeu cau ban dau:
 * define macro nay se tu dong keo theo cac macro khac thong qua 1 chuoi
 * object-like macro tro toi nhau. */
#define CHAIN_A CHAIN_B
#define CHAIN_B CHAIN_C
#define CHAIN_C 1
#if CHAIN_A == 1
    int code_8_6_multi_level_macro_chain = 1;
    /* EXPECT: SONG SOT. Preprocessor phai de-quy macro-expand: CHAIN_A ->
     * CHAIN_B -> CHAIN_C -> 1, roi moi danh gia "#if 1 == 1". Parser PHAI
     * ho tro macro-expand NHIEU TANG (khong chi 1 buoc thay the), day la
     * yeu cau bat buoc de dung dan cho bai toan macro "noi duoi" cua ban. */
#endif
