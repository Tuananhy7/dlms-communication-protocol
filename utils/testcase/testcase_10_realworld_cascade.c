/*
 * TESTCASE BO 10: Cac pattern thuc te trong code nhung (STM32/HAL style) va
 * mo hinh cascade macro giong dung scenario ban mo ta o yeu cau ban dau
 * (define product A se tu dong "keo theo" B, C, roi B, C lai keo theo D, E).
 * Macro duoc #define ngay trong file (self-contained, khong can seed ngoai).
 */

/* ---- 10.1: chon 1 trong nhieu bien the chip cung dong (OR chain dai) ---- */
#define STM32F103xC
#if defined(STM32F103xB) || defined(STM32F103xC) || defined(STM32F103xD) || defined(STM32F103xE)
    int code_10_1_device_variant_or_chain = 1;
    /* EXPECT: SONG SOT (STM32F103xC duoc define). Pattern nay xuat hien RAT
     * nhieu trong file .h cua HAL/CMSIS - can dam bao parser xu ly dung
     * chuoi || dai voi nhieu hon 2 toan hang. */
#endif

/* ---- 10.2: ket hop AND + NOT giua 2 driver loai tru lan nhau ------------ */
#define USE_HAL_DRIVER
/* USE_LL_DRIVER KHONG duoc define - HAL va LL thuong loai tru nhau */
#if defined(USE_HAL_DRIVER) && !defined(USE_LL_DRIVER)
    int code_10_2_hal_not_ll = 1;          /* EXPECT: SONG SOT */
#endif

/* ---- 10.3: gate theo phien ban compiler (so sanh so nguyen lon) --------- */
#define __ARMCC_VERSION 6190001
#if defined(__ARMCC_VERSION) && (__ARMCC_VERSION >= 6010050)
    int code_10_3_compiler_version_gate = 1;
    /* EXPECT: SONG SOT (6190001 >= 6010050). Pattern nay hay dung de bat/tat
     * mot doan code chi tuong thich voi tu 1 phien ban toolchain tro len -
     * can dam bao parser doc dung so nguyen lon (7 chu so) khong bi tran
     * hoac parse nham thanh nhieu token so. */
#endif

/* ---- 10.4: mo hinh CASCADE dung y het scenario goc cua ban -------------- */
/* define PRODUCT_A se tu dong "mo khoa" FEATURE_B va FEATURE_C (thong qua
 * 1 khoi #ifdef PRODUCT_A dinh nghia ca 2). Sau do, moi FEATURE_B va
 * FEATURE_C lai TIEP TUC tu dong mo khoa them FEATURE_D va FEATURE_E
 * (thong qua 2 khoi #ifdef rieng biet, o vi tri XA HON trong file). Day
 * chinh la yeu cau cot loi ban mo ta: "define macro A, B, C co the tu
 * enable define cho C, D, E" - test nay xac nhan parser phai xu ly TUAN
 * TU (single-pass, propagate #define ve phia truoc) dung nhu 1 preprocessor
 * that, KHONG duoc dung 1 tap macro "tinh san" co dinh tu dau file. */
#define PRODUCT_A

#ifdef PRODUCT_A
    #define FEATURE_B
    #define FEATURE_C
    int code_10_4_product_a_root = 1;      /* EXPECT: SONG SOT */
#endif

/* ... gia dinh o day co hang tram dong code khac nam giua ... */

#ifdef FEATURE_B
    #define FEATURE_D
    int code_10_4_feature_b_triggers_d = 1; /* EXPECT: SONG SOT */
#endif

#ifdef FEATURE_C
    #define FEATURE_E
    int code_10_4_feature_c_triggers_e = 1; /* EXPECT: SONG SOT */
#endif

/* Kiem tra cuoi cung: ca FEATURE_D va FEATURE_E deu phai "song sot" duoc
 * toi day, DU KHONG CO NOI NAO trong file define truc tiep 2 macro nay -
 * chung chi ton tai gian tiep qua 2 tang cascade (A -> B,C -> D,E). */
#if defined(FEATURE_D) && defined(FEATURE_E)
    int code_10_4_final_cascade_check = 1; /* EXPECT: SONG SOT - day la
                                               phep thu quan trong nhat cua
                                               ca 10 bo testcase. */
#endif

/* ---- 10.5: gate theo dialect chuan C (__STDC_VERSION__) ----------------- */
#define __STDC_VERSION__ 201112L
#if __STDC_VERSION__ >= 201112L
    int code_10_5_c11_dialect_gate = 1;    /* EXPECT: SONG SOT (C11 tro len) */
#endif

/* ---- 10.6: PHAN CHOI (negative control) - PRODUCT_B khong duoc define,
 *            toan bo cascade rieng cua no phai bi loai HOAN TOAN ----------- */
/* Khong co #define PRODUCT_B o day. */
#ifdef PRODUCT_B
    #define FEATURE_X_FROM_B
    int code_10_6_product_b_root = 1;
#endif

#ifdef FEATURE_X_FROM_B
    int code_10_6_should_never_survive = 1;
    /* EXPECT: BI LOAI. Vi PRODUCT_B chua bao gio duoc define, khoi #ifdef
     * PRODUCT_B o tren khong duoc thuc thi, nen FEATURE_X_FROM_B cung
     * KHONG BAO GIO duoc #define - ca 2 dong code_10_6 deu phai bi loai.
     * Day la phep thu "phu dinh" quan trong: dam bao parser KHONG lo dinh
     * nghia macro (false positive) khi khoi #ifdef cha cua no chua bao gio
     * duoc kich hoat. */
#endif
