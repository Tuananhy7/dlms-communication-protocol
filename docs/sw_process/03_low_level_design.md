# 3. Thiết Kế Chi Tiết (Low-Level Design - LLD)

## A. Các Component nhỏ

### Detailed Specs
- Mô tả chi tiết logic cho từng file `.c` và `.h`.

### Finite State Machine (FSM)
Sơ đồ chuyển trạng thái cho các quy trình như:
- Quy trình kết nối mạng.
- Quy trình OTA.
- Quy trình xử lý Tamper.

### Data Structures
Định nghĩa các kiểu cấu trúc dữ liệu.

Ví dụ:
- `struct` lưu chỉ số điện.
- `struct` lưu trạng thái thiết bị.
- `struct` lưu cấu hình truyền thông.

## B. Khái niệm

Cụ thể hóa kiến trúc SAD thành thuật toán, lưu đồ logic và nguyên mẫu hàm API chi tiết.

Mục tiêu là để lập trình viên có thể nhìn vào tài liệu LLD và triển khai code trực tiếp.

## C. Step by step triển khai

### 1. Thiết kế FSM
Vẽ chi tiết logic xử lý.

Ví dụ luồng xử lý Tamper:

```text
Tamper flag ON -> Ghi log EEPROM -> Nháy LED -> Khóa màn hình
```

### 2. Vẽ lưu đồ thuật toán (Flowchart)
Cụ thể hóa thuật toán tính giá điện theo khung giờ TOU.

Ví dụ:
- Xác định thời điểm hiện tại.
- Kiểm tra khung giờ biểu giá.
- Tính điện năng tiêu thụ.
- Áp dụng giá tương ứng.
- Cập nhật dữ liệu billing.

### 3. Định nghĩa API
Viết sẵn tên hàm, đầu vào và đầu ra.

Ví dụ:

```c
int8_t EEPROM_Write(uint32_t addr, uint8_t *buf, uint16_t len);
```

### 4. Phân bổ bộ nhớ
Quy hoạch cụ thể các vùng nhớ:
- Vùng Flash chứa code chính.
- Vùng Flash chứa code OTA.
- Vùng EEPROM / Flash chứa dữ liệu cấu hình.
- Vùng EEPROM / Flash chứa log sự kiện.
