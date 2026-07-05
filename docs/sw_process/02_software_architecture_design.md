# 2. Thiết Kế Kiến Trúc (Software Architecture Design - SAD)

## A. Các Component nhỏ

### MCAL Layer
Driver sát chip:
- ADC
- SPI
- UART
- RTC

### Middleware / Service
- Quản lý OS: FreeRTOS.
- Quản lý bộ nhớ: Flash / EEPROM.
- Thư viện mã hóa.

### Protocol Stack
- DLMS Engine.
- TCP/IP Stack.

### Application Layer
- Logic biểu giá: Tariff / TOU.
- Xử lý sự kiện.
- Hiển thị LCD.

## B. Khái niệm

Phân chia phần mềm thành các tầng độc lập và định nghĩa cách các khối lớn giao tiếp với nhau thông qua interface.

Mục tiêu là đảm bảo tính tái sử dụng, đặc biệt khi cần đổi chip hoặc tái sử dụng kiến trúc cho dự án embedded khác.

## C. Step by step triển khai

### 1. Chọn mô hình
Quyết định sử dụng RTOS, ví dụ FreeRTOS, để quản lý đa tác vụ.

### 2. Phân chia Task & Độ ưu tiên

#### Ưu tiên cao
- Đọc ADC / Metrology, chu kỳ khoảng 1 ms.

#### Ưu tiên trung bình
- Xử lý truyền thông DLMS.

#### Ưu tiên thấp
- Quét LCD.
- Xử lý nút nhấn.

### 3. Thiết kế luồng dữ liệu
Vẽ sơ đồ luồng dữ liệu:

```text
Đo lường -> Xử lý -> Lưu EEPROM -> Truyền ra ngoài
```

### 4. Bảo vệ tài nguyên
Dùng Mutex / Semaphore để tránh xung đột khi nhiều task dùng chung tài nguyên.

Ví dụ tài nguyên cần bảo vệ:
- Flash
- EEPROM
- LCD
