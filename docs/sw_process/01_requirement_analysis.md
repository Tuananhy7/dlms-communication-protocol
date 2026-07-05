# 1. Phân Tích Yêu Cầu (Requirement Analysis)

## A. Các Component nhỏ

### Metrology
- Độ chính xác: Class 0.5S / 1.0.
- Tính toán điện năng RMS.

### Communication
- Giao thức đọc xa: DLMS/COSEM, Modbus.
- Kênh truyền: NB-IoT, RF Mesh, PLC.

### Power & Battery
- Chế độ ngủ: Sleep mode.
- Xử lý mất lưới đột ngột: Last Gasp.

### Security
- Chống gian lận: Tamper.
- Mã hóa: AES-128 / AES-256.

### OTA
- Cập nhật phần mềm từ xa an toàn.
- Tự động quay về bản cũ nếu lỗi: Fallback.

## B. Khái niệm

Chuyển hóa tiêu chuẩn đo lường IEC và mong muốn của khách hàng thành tài liệu kỹ thuật SRS.

SRS cần mô tả rõ phần mềm phải làm gì, từ đó làm căn cứ cho lập trình và kiểm thử.

## C. Step by step triển khai

### 1. Nghiên cứu tiêu chuẩn
- Đọc kỹ tài liệu IEC liên quan đến đo lường.
- Đọc tài liệu DLMS/COSEM liên quan đến truyền thông.

### 2. Định nghĩa trạng thái (States)
Xác định các chế độ hoạt động chính:
- Normal: Chạy lưới.
- Power-down: Mất lưới.
- Tamper: Bị gian lận.

### 3. Viết SRS
Viết yêu cầu theo dạng đo lường được.

Ví dụ:
- Khi mất lưới, thiết bị phải phát tín hiệu cảnh báo trong vòng 500 ms.

### 4. Họp Review
- Chốt yêu cầu với đội phần cứng (HW).
- Chốt yêu cầu với đội đảm bảo chất lượng (QA).
