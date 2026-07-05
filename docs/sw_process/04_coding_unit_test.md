# 4. Lập Trình & Kiểm Thử Đơn Vị (Coding & Unit Test)

## A. Các Component nhỏ

### Source Code
- Mã nguồn C / C++.

### Coding Standard
- Quy tắc code an toàn.
- Ví dụ: MISRA C.

### Static Analysis
Công cụ quét lỗi tự động:
- Polyspace
- SonarQube

### Unit Test Framework
Bộ code giả lập để test hàm:
- Unity
- Google Test

## B. Khái niệm

Viết code hoàn chỉnh cho vi điều khiển và tách riêng từng hàm hoặc module để kiểm tra tính đúng đắn của logic thuật toán.

## C. Step by step triển khai

### 1. Code chuẩn MISRA C
Một số nguyên tắc quan trọng:
- Không dùng cấp phát động như `malloc`.
- Dùng `volatile` cho biến được thay đổi trong ngắt.
- Dùng kiểu dữ liệu cố định kích thước như `uint8_t`, `uint16_t`, `uint32_t`.

### 2. Quét Code Tĩnh (Static Analysis)
Chạy công cụ kiểm tra tự động trên máy tính để phát hiện sớm lỗi.

Các lỗi thường cần kiểm tra:
- Tràn mảng.
- Chia cho 0.
- Ép kiểu sai.
- Truy cập con trỏ không hợp lệ.

### 3. Viết Unit Test (UT)
Sử dụng kỹ thuật Mock / Stub để giả lập dữ liệu ngoại vi.

Ví dụ:
- Giả lập dữ liệu ADC đầu vào để test hàm tính dòng điện RMS.
- Giả lập EEPROM để test hàm ghi / đọc dữ liệu.
- Giả lập module truyền thông để test xử lý lỗi kết nối.

### 4. Đo Code Coverage
Đảm bảo các bài test chạy qua ít nhất 80% các nhánh logic.

Các nhánh cần được bao phủ:
- `if / else`
- `switch / case`
- Điều kiện lỗi
- Điều kiện biên
