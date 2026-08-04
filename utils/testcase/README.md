# Bộ testcase kiểm tra parser #ifdef / #if defined

## Seed macro dùng chung cho cả 5 file

```
-DFEATURE_A          (object-like, không giá trị)
                      (FEATURE_B KHÔNG được define)
```

Testcase 2 có dùng thêm `FEATURE_A_VAL` / `FEATURE_B_VAL` — đây là seed
**riêng chỉ cho block 2.2**, giả định `FEATURE_A_VAL=1`, `FEATURE_B_VAL=0`,
để test biểu thức số học thay vì `defined()`.

## Cách dùng

Chạy parser của bạn trên từng file với seed set ở trên, rồi so khớp với
cột "EXPECT" ghi trong comment ngay tại từng block. Mỗi dòng code test đều
có tên biến duy nhất dạng `code_X_Y_...` để bạn `grep` nhanh xem dòng đó có
xuất hiện trong output "đã lọc" hay không.

## Tổng hợp theo nhóm lỗi cần xử lý

| Bộ | Chủ đề | Loại kết quả mong đợi |
|----|--------|------------------------|
| 1 | Cú pháp `defined` (rỗng, có/không ngoặc, sai hoa-thường) | Có case phải **báo lỗi cú pháp** (1.1, 1.8), không được âm thầm coi là false |
| 2 | `&&` `||` với macro bọc ngoặc không qua `defined()` | Cảnh báo "macro rỗng dùng trong biểu thức số"; test đúng độ ưu tiên toán tử (2.6) |
| 3 | Line continuation (`\` cuối dòng) | Phải gộp dòng trước khi tokenize; test cả trường hợp có khoảng trắng sau `\` (3.5 — hành vi không chuẩn) |
| 4 | Directive thiếu tham số / ngoặc lệch / thứ tự sai | Toàn bộ phải là **lỗi cú pháp cứng**, không suy đoán; 4.9 test cả trường hợp thiếu `#endif` cuối file |
| 5 | Include-guard đặt tên reserved identifier (`__FOO`, `_FOO`) | Cảnh báo naming riêng biệt với kết quả true/false; test macro chain xuyên block (5.3, 5.4 phụ thuộc `#define` ở 5.1, 5.2) |

## Bộ 6-10 (mở rộng) — đã verify bằng `gcc -E` thật

Toàn bộ EXPECT trong 5 file dưới đây đã được đối chiếu trực tiếp với
`gcc -E -P` (không phải suy đoán lý thuyết) để đảm bảo đúng hành vi chuẩn C:

| Bộ | Chủ đề | Điểm mấu chốt cần parser xử lý đúng |
|----|--------|--------------------------------------|
| 6 | Biểu thức số học, so sánh | **Identifier chưa từng define bị thay bằng `0`** (không phải lỗi!) — nguồn gốc bug do gõ nhầm tên macro cực khó phát hiện; chia cho 0 phải bắt được, không crash |
| 7 | Chuỗi `#elif`, lồng nhiều tầng | **Skip-mode không được evaluate/parse biểu thức** — 1 nhánh `#elif` lỗi cú pháp nặng nằm sau nhánh đã được chọn sẽ **không hề gây lỗi** (đã verify: gcc không báo gì) |
| 8 | Function-like macro, redefinition | Macro function-like chỉ được gọi khi có `(` theo ngay sau tên; define lại với giá trị khác → warning thật; macro chain nhiều tầng (A→B→C→1) phải expand đệ quy |
| 9 | Tự tham chiếu, giá trị không phải số | Macro tự tham chiếu / tham chiếu vòng phải có cơ chế chống lặp vô hạn (hide-set); string literal trong `#if` là lỗi cứng; `defined()` áp lên kết quả gọi macro là lỗi cú pháp |
| 10 | Pattern thực tế STM32/HAL + cascade | Test lại đúng scenario gốc: define product A → tự kéo theo B, C → B, C tự kéo theo D, E, xử lý tuần tự (single-pass), có cả negative control (10.6) đảm bảo không "lỡ" enable macro khi nhánh cha chưa từng được kích hoạt |

## Lưu ý quan trọng khi tích hợp vào script `count_loc_from_markers.py`

Các file test này viết ở dạng "trực tiếp" (không qua `.i` preprocessed),
nên khi test parser thật (phần xử lý `#if defined` trong file `.i` từ
`-frewrite-includes` mà bạn upload), bạn cần:

1. Verify riêng phần **evaluator biểu thức** (`defined`, `&&`, `||`, `!`,
   ngoặc, line-continuation) bằng 5 file này trước — đây là phần lõi hay
   sai nhất.
2. Sau khi evaluator chạy đúng trên cả 5 bộ, mới ráp vào pipeline đọc
   line-marker (`# N "file"`) của file `.i` thật, vì lúc đó còn thêm độ
   phức tạp của wrapper `#if defined(__CLANG_REWRITTEN_INCLUDES)` do
   `-frewrite-includes` tự sinh ra (cần loại trừ riêng, không tính là
   code thật của file gốc).
