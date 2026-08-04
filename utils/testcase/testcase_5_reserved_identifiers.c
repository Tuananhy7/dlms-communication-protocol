/*
 * TESTCASE BO 5: Include-guard / macro dat ten bang identifier RESERVED
 * Seed macro: FEATURE_A duoc define (khong gia tri), FEATURE_B KHONG duoc define
 *
 * Theo chuan C (ISO/IEC 9899, dieu 7.1.3 "Reserved identifiers"):
 *   - Identifier bat dau bang dau gach duoi VA theo sau la chu HOA, hoac
 *     bat dau bang 2 dau gach duoi lien tiep (__FOO) -> RESERVED O MOI PHAM VI,
 *     danh rieng cho compiler/thu vien chuan, code cua nguoi dung KHONG duoc dung.
 *   - Identifier bat dau bang 1 dau gach duoi va theo sau la chu THUONG (_foo)
 *     -> RESERVED O FILE SCOPE (bien toan cuc, macro, ten struct/tag...).
 *   - Identifier bat dau bang 1 dau gach duoi + chu HOA (_FOO) -> cung RESERVED
 *     (thuoc nhom dau tien: gach duoi + chu hoa).
 *
 * "Issue AAV" trong cac dong duoi day la nhan (label) noi bo cua ban de danh
 * dau vi tri phat hien vi pham naming convention nay - script/parser NEN co
 * kha nang phat hien VA CANH BAO cac define/include-guard dung ten reserved,
 * DU cho co hay khong co comment danh dau di kem, vi trong thuc te code that
 * (500k LOC) se KHONG PHAI luc nao cung duoc gan comment nhac nho san.
 */

/* ---- 5.1: __FEATURE_A - reserved (2 dau gach duoi lien tiep), CO comment  */
#ifndef __FEATURE_A /* issue AAV */
#define __FEATURE_A
    int code_5_1_double_underscore_with_comment = 1;
    /* EXPECT: ve mat LOGIC dieu kien van danh gia binh thuong (macro chua
     * duoc define nen #ifndef = true, code song sot). NHUNG parser/linter
     * NEN phat sinh CANH BAO rieng: "ten macro '__FEATURE_A' vi pham quy tac
     * dinh danh reserved cua chuan C" - day la 1 loai canh bao KHAC voi
     * ket qua song-sot/bi-loai cua #ifdef resolution. */
#endif

/* ---- 5.2: _FEATURE_A - reserved (1 gach duoi + chu hoa), CO comment ----- */
#ifndef _FEATURE_A /* issue AAV */
#define _FEATURE_A
    int code_5_2_single_underscore_upper_with_comment = 1;
    /* EXPECT: tuong tu 5.1 - can canh bao rieng ve naming, khong lien quan
     * gia tri true/false cua dieu kien. */
#endif

/* ---- 5.3: __FEATURE_A - reserved, KHONG co comment danh dau ------------- */
#ifndef __FEATURE_A
    int code_5_3_double_underscore_no_comment = 1;
    /* EXPECT: __FEATURE_A DA duoc #define tai block 5.1 phia tren (macro
     * chain trong cung 1 file) -> dieu kien #ifndef nay la FALSE.
     * -> code_5_3 PHAI BI LOAI. Day la phep thu quan trong: parser phai
     * nho trang thai #define tu block truoc do (single-pass, tuan tu),
     * DONG THOI van phai phat hien duoc canh bao naming du khong co comment. */
#endif

/* ---- 5.4: _FEATURE_A - reserved, KHONG co comment danh dau -------------- */
#ifndef _FEATURE_A
    int code_5_4_single_underscore_no_comment = 1;
    /* EXPECT: _FEATURE_A DA duoc #define tai block 5.2 -> dieu kien FALSE
     * -> code_5_4 PHAI BI LOAI (tuong tu ly do o 5.3). */
#endif

/* ---- 5.5: doi chung - include guard dat ten DUNG chuan (khong reserved) - */
#ifndef FEATURE_A_GUARD_H
#define FEATURE_A_GUARD_H
    int code_5_5_correct_naming_no_warning = 1;
    /* EXPECT: song sot, VA KHONG duoc phat sinh canh bao naming (day la
     * truong hop dung de dam bao parser khong bao dong gia - false positive
     * tren nhung ten hop le). */
#endif
