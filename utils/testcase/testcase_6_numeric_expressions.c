/*
 * TESTCASE BO 6: Bieu thuc so hoc / so sanh trong #if
 * Tat ca macro can thiet duoc #define ngay trong file nay (self-contained).
 *
 * Chuan C (6.10.1): bieu thuc #if la 1 "integer constant expression".
 * Sau khi macro-expand, MOI identifier CON LAI (khong con la macro nao nua,
 * ke ca ten macro function-like khong duoc goi dung cu phap) se duoc THAY
 * THE BANG 0 truoc khi danh gia. Day la nguon loi ngam rat pho bien: go sai
 * ten macro (typo) se KHONG gay loi bien dich, ma am tham thanh dieu kien
 * so sanh voi 0.
 */

/* ---- 6.1: bieu thuc so hoc thuan tuy, khong lien quan macro nao --------- */
#if 1 + 1 == 2
    int code_6_1_pure_arithmetic = 1;      /* EXPECT: SONG SOT */
#endif

/* ---- 6.2: version-check kieu MAJOR.MINOR, pattern rat pho bien ---------- */
#define VERSION_MAJOR 2
#define VERSION_MINOR 5
#if (VERSION_MAJOR * 100 + VERSION_MINOR) >= 205
    int code_6_2_version_check_gte = 1;    /* EXPECT: SONG SOT (2*100+5=205 >= 205) */
#endif

/* ---- 6.3: toan tu bitwise AND de kiem tra 1 bit co bat khong ------------ */
#define FLAGS 0x05  /* 0b0101 */
#if (FLAGS & 0x04)
    int code_6_3_bitwise_and_flag_set = 1; /* EXPECT: SONG SOT (0x05 & 0x04 = 0x04, khac 0) */
#endif

/* ---- 6.4: toan tu dich bit (shift) --------------------------------------- */
#define BASE_VALUE 1
#if (BASE_VALUE << 3) == 8
    int code_6_4_left_shift = 1;           /* EXPECT: SONG SOT (1 << 3 = 8) */
#endif

/* ---- 6.5: toan tu ba ngoi (ternary) trong bieu thuc #if ------------------ */
#if (1 ? 10 : 20) == 10
    int code_6_5_ternary_operator = 1;     /* EXPECT: SONG SOT */
#endif

/* ---- 6.6: GOTCHA QUAN TRONG - identifier khong ton tai duoc thay bang 0 - */
/* "UNDEFINED_MACRO_XYZ" chua tung duoc #define o bat ky dau nao trong file.
 * Theo chuan, no van HOP LE ve cu phap: sau macro-expand khong con gi de thay
 * the, no duoc coi la mot identifier "con lai" va duoc THAY BANG 0. Bieu
 * thuc thuc te tro thanh "#if 0 == 0" -> TRUE. Day la loi go nham ten macro
 * (typo) rat kho phat hien vi KHONG co canh bao/loi bien dich nao ca. */
#if UNDEFINED_MACRO_XYZ == 0
    int code_6_6_undefined_identifier_as_zero = 1;
    /* EXPECT: SONG SOT (theo dung chuan C), NHUNG day la truong hop parser
     * NEN canh bao rieng: "macro 'UNDEFINED_MACRO_XYZ' chua duoc dinh nghia,
     * dang duoc coi ngam la 0 - kiem tra lai co phai do go nham ten khong".
     * Day la diem khac biet quan trong voi #ifdef/#ifndef: #ifdef se tra ve
     * false ro rang, con #if dùng ten macro so voi gia tri thi lai "hop le
     * ngam" va de gay hieu lam. */
#endif

/* ---- 6.7: identifier khong ton tai dung truc tiep nhu bool (khong so sanh) */
#if UNDEFINED_MACRO_ABC
    int code_6_7_undefined_identifier_bare = 1;
    /* EXPECT: BI LOAI. UNDEFINED_MACRO_ABC -> 0 -> #if 0 -> false.
     * Doi lap voi 6.6, o day ket qua "dung mong doi" (bi loai) nhung LY DO
     * dan den ket qua lai la ngam dinh, khong phai vi macro "khong duoc bat"
     * theo nghia #ifdef. */
#endif

/* ---- 6.8: chia cho 0 trong bieu thuc hang so ----------------------------- */
/* Day la LOI THAT SU tai thoi diem preprocess (khong phai runtime). Cac
 * compiler that (gcc/armclang) se bao loi "division by zero in #if".
 * Parser PHAI phat hien va bao loi ro rang, TUYET DOI KHONG duoc crash
 * (chia so nguyen cho 0 trong Python se nem ZeroDivisionError neu ban
 * dung eval() truc tiep - day la ly do vi sao KHONG nen dung eval() tho
 * de danh gia bieu thuc #if). */
#if (10 / (1 - 1)) > 0
    int code_6_8_division_by_zero = 1;
    /* Da verify bang gcc that: gcc bao "error: division by zero in #if"
     * NHUNG van tiep tuc bien dich nhu the dieu kien = true (hanh vi phuc
     * hoi sau loi nay KHONG duoc chuan hoa giua cac compiler - dung de
     * kiem tra parser cua ban co CRASH hay khong khi gap chia-cho-0, chu
     * khong phai de kiem tra ket qua true/false "dung"). */
#endif

/* ---- 6.9: hang so hex lon, kiem tra parser doc dung so hoc ---------------- */
#if 0xFFFFFFFF > 0
    int code_6_9_large_hex_constant = 1;   /* EXPECT: SONG SOT */
#endif

/* ---- 6.10: ket hop macro rong (object-like khong gia tri) trong so sanh - */
#define FEATURE_EMPTY
#if FEATURE_EMPTY == 0
    int code_6_10_empty_macro_in_comparison = 1;
    /* EXPECT: LOI CU PHAP THAT SU. FEATURE_EMPTY duoc define nhung KHONG CO
     * GIA TRI (replacement list rong). Sau khi macro-expand, dong tro thanh
     * "#if  == 0" (thieu toan hang ben trai). Day la LOI, KHAC voi truong
     * hop 6.6/6.7 (macro CHUA TUNG duoc define -> thay 0; con day la macro
     * DA duoc define nhung voi noi dung RONG -> bien mat hoan toan, khong
     * con gi de thay the ca). Parser can phan biet ro 2 truong hop nay. */
#endif
