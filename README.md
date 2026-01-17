# Webapps - Hệ thống Quản lý Doanh nghiệp

Hệ thống quản lý tổng thể các hoạt động doanh nghiệp được xây dựng bằng Streamlit Python.

## Tính năng

### 1. Quản lý Hóa đơn
- Nhập hóa đơn từ file PDF hoặc ảnh
- Tự động trích xuất thông tin từ hóa đơn sử dụng OCR
- Lưu thông tin vào file Excel: `QLCP_PiARC_01.2026.xlsx`, sheet `HD_MV`

### 2. Lấy thông tin CCCD
- Nhập ảnh mặt trước và mặt sau của CCCD
- Tự động trích xuất thông tin nhân viên từ CCCD
- Lưu thông tin vào file Excel: `1. DS NV_CN và HĐLĐ_29.12.25v1.xlsx`

## Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Tesseract OCR (cần cài đặt riêng)

### Cài đặt Tesseract OCR

**Windows:**
1. Tải Tesseract từ: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt Tesseract
3. Thêm đường dẫn vào biến môi trường PATH, hoặc uncomment dòng cấu hình trong code:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-vie
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

### Cài đặt Python packages

```bash
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ chạy tại `http://localhost:8501`

## Cấu trúc dự án

```
.
├── app.py                          # Trang chủ
├── pages/
│   ├── Quan_ly_Hoa_don.py         # Module Quản lý Hóa đơn
│   └── Lay_thong_tin_CCCD.py      # Module Lấy thông tin CCCD
├── requirements.txt                # Dependencies
├── README.md                       # Tài liệu
└── [File Excel mẫu]                # File Excel để lưu dữ liệu
```

## Sử dụng

1. **Quản lý Hóa đơn:**
   - Chọn menu "Quản lý Hóa đơn" từ sidebar
   - Upload file PDF hoặc ảnh hóa đơn
   - Kiểm tra và chỉnh sửa thông tin đã trích xuất
   - Nhấn "Lưu hóa đơn vào Excel"

2. **Lấy thông tin CCCD:**
   - Chọn menu "Lấy thông tin CCCD" từ sidebar
   - Upload ảnh mặt trước và mặt sau của CCCD
   - Nhấn "Trích xuất thông tin"
   - Kiểm tra và chỉnh sửa thông tin
   - Nhấn "Lưu vào Excel"

## Lưu ý

- OCR có thể không chính xác 100%, vui lòng kiểm tra và chỉnh sửa thông tin trước khi lưu
- File Excel sẽ được tạo tự động nếu chưa tồn tại
- Đảm bảo có đủ quyền đọc/ghi file trong thư mục dự án

## Phiên bản

- Version: 1.0
- Ngày tạo: 17/01/2026
