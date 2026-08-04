/*
 * TESTCASE BO 9: Macro tu tham chieu (self-referential), gia tri khong phai
 * so, va cac "bay" ve token hoa / comment trong bieu thuc #if
 * Macro duoc #define ngay trong file (self-contained).
 */

/* ---- 9.1: macro tu tham chieu truc tiep (A dinh nghia bang chinh no) ---- */
#define SELF_REF SELF_REF
#if SELF_REF == 0
    int code_9_1_self_referential_macro = 1;
    /* EXPECT: SONG SOT, nhung ly do rat tinh vi. Theo chuan C (6.10.3.4),
     * khi macro-expand SELF_REF, ban than ten "SELF_REF" xuat hien LAI trong
     * chinh phan thay the cua no SE KHONG duoc thay the them lan nua (con
     * goi la "blue painting" / "hide set") de tranh de-quy vo han. Ket qua
     * cuoi cung con lai la token "SELF_REF" (khong the thay the them), sau
     * do theo rule "identifier con lai -> 0", no thanh 0. Bieu thuc tro
     * thanh "#if 0 == 0" -> true. Parser BAT BUOC phai phat hien va CHAN
     * vong lap macro tu tham chieu (dung 1 "expansion stack"/hide-set),
     * neu khong se bi TREO (infinite loop) khi co gang expand mai mai. */
#endif

/* ---- 9.2: macro tham chieu vong qua lai (mutual recursion A<->B) -------- */
#define MUTUAL_A MUTUAL_B
#define MUTUAL_B MUTUAL_A
#if MUTUAL_A == 0
    int code_9_2_mutual_recursive_macros = 1;
    /* EXPECT: SONG SOT (tuong tu 9.1 ve mat ket qua: token con lai khong
     * the tiep tuc thay the -> 0 -> true). Day la test QUAN TRONG HON 9.1
     * vi vong lap xay ra giua 2 macro khac nhau (A goi B, B goi lai A),
     * kho phat hien hon truong hop tu tham chieu don gian. Neu parser chi
     * kiem tra "macro co dang duoc expand co xuat hien lai chinh no khong"
     * ma khong theo doi CA CHUOI cac macro dang duoc expand (hide-set day
     * du), se bi treo o day. */
#endif

/* ---- 9.3: macro RONG dung trong bieu thuc so hoc (thieu toan hang) ------ */
#define BLANK_MACRO
#if BLANK_MACRO == 0
    int code_9_3_blank_macro_arithmetic = 1;
    /* EXPECT: LOI CU PHAP THAT SU (giong 6.10, nhac lai o day de nhan manh:
     * day la loi RAT hay gap khi 1 file config.h define san mot macro RONG
     * lam "placeholder" roi file khac lai dung no trong phep so sanh so). */
#endif

/* ---- 9.4: gia tri macro la chuoi ky tu (string literal) dung trong #if -- */
#define DEVICE_NAME "STM32F103"
#if DEVICE_NAME == "STM32F103"
    int code_9_4_string_literal_comparison = 1;
    /* EXPECT: LOI CU PHAP THAT SU. Chuan C quy dinh bieu thuc #if BAT BUOC
     * la "integer constant expression" - string literal KHONG duoc phep
     * xuat hien trong bieu thuc #if duoi bat ky hinh thuc nao (kho co the
     * "so sanh 2 chuoi" nhu ngon ngu script khac). Cac compiler that se
     * bao loi "token is not valid in preprocessor expressions" hoac tuong
     * tu. Parser PHAI bao loi ro rang, KHONG duoc co gang so sanh chuoi
     * theo kieu Python/JS. */
#endif

/* ---- 9.5: defined() ap dung cho KET QUA cua 1 macro invocation (UB) ----- */
#define CONCAT_HELPER(a, b) a##b
#if defined(CONCAT_HELPER(FEAT, URE_A))
    int code_9_5_defined_on_macro_result_UB = 1;
    /* EXPECT: LOI CU PHAP THAT SU (da verify bang gcc that: "missing ')'
     * after 'defined'"). Ly do: toan hang cua defined() phai la 1 identifier
     * DUY NHAT (co the boc trong 1 cap ngoac) - preprocessor KHONG macro-
     * expand phan ben trong defined(...) truoc khi kiem tra dang thuc nay.
     * Vi vay no doc "CONCAT_HELPER" nhu la TEN identifier can kiem tra, roi
     * gap ngay "(FEAT, URE_A))" con du lai ma khong khop cu phap mong doi
     * (chi mong 1 dau ')' ngay sau identifier) -> loi "missing ')' after
     * defined". Ghi chu: chuan C (6.10.1p1) that ra dung tu "unspecified"
     * cho truong hop defined xuat hien tu ket qua macro-expand cua MOT macro
     * KHAC (vd macro A expand ra chuoi chua chu "defined"); con truong hop
     * cu the o day - GOI TRUC TIEP 1 function-like macro lam toan hang cho
     * defined() - don gian la SAI CU PHAP ngay tu dau vi defined khong nhan
     * dang "goi ham" la mot identifier hop le. Parser can bao loi cu phap
     * ro rang o day, khong duoc co gang "doan" ket qua. */
#endif

/* ---- 9.6: comment /* * / nam giua cac token trong cung 1 dong #if ------- */
#define FEATURE_X
#define FEATURE_Y
#if defined(FEATURE_X) /* ghi chu giai thich */ && defined(FEATURE_Y)
    int code_9_6_comment_between_tokens = 1;
    /* EXPECT: SONG SOT. Comment /* ... * / (viet co chu y them dau cach o
     * day de tranh ket thuc comment cua chinh doan huong dan nay) chi don
     * gian duoc thay bang 1 khoang trang trong giai doan tien xu ly truoc
     * ca buoc tokenize (translation phase 3), hoan toan khong anh huong den
     * logic. Parser can dam bao buoc "strip comment" chay TRUOC buoc tach
     * token, khong duoc de comment lam vo tinh dinh vao 1 token nao do. */
#endif
