import streamlit as st

st.set_page_config(
    page_title="Webapps - Quản lý Doanh nghiệp",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 HỆ THỐNG QUẢN LÝ DOANH NGHIỆP")
st.markdown("---")

st.markdown("""
### Chào mừng đến với hệ thống quản lý doanh nghiệp!

Ứng dụng này cung cấp các tính năng quản lý tổng thể các hoạt động doanh nghiệp.

#### 📋 Menu chức năng:

1. **Quản lý Hóa đơn** - Quản lý danh mục hóa đơn từ PDF/ảnh
2. **Lấy thông tin CCCD** - Trích xuất thông tin nhân viên từ CCCD

Vui lòng chọn menu từ sidebar để bắt đầu.
""")

st.sidebar.title("📑 MENU")
st.sidebar.markdown("""
- [🏠 Trang chủ](#)
- [📄 Quản lý Hóa đơn](/pages/Quan_ly_Hoa_don)
- [🆔 Lấy thông tin CCCD](/pages/Lay_thong_tin_CCCD)
""")

st.markdown("---")
st.markdown("**Phiên bản:** 1.0 | **Ngày tạo:** 17/01/2026")
