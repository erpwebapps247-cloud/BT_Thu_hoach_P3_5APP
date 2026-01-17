import streamlit as st
from PIL import Image
import pytesseract
import re
import json
from datetime import datetime

# Import OpenAI (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Đọc API key từ config (nếu có)
try:
    from config import OPENAI_API_KEY as DEFAULT_API_KEY
except ImportError:
    DEFAULT_API_KEY = None

st.set_page_config(
    page_title="Tạo mới HĐLD CN",
    page_icon="📝",
    layout="wide"
)

st.title("📝 TẠO MỚI HỢP ĐỒNG LAO ĐỘNG CÔNG NHÂN")
st.markdown("---")
st.markdown("**Hướng dẫn:** Upload ảnh mặt trước và mặt sau CCCD để tự động tạo hợp đồng lao động")

# Cấu hình tesseract (nếu cần)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

TEMPLATE_FILE = "HDLD_Mau.txt"

def extract_text_with_ocr(image):
    """Trích xuất text từ ảnh sử dụng OCR cơ bản"""
    try:
        text = pytesseract.image_to_string(image, lang='vie+eng')
        return text
    except Exception as e:
        st.error(f"Lỗi khi đọc OCR: {str(e)}")
        return ""

def extract_cccd_with_openai(text_front, text_back, api_key):
    """Sử dụng OpenAI API để trích xuất thông tin từ text OCR CCCD"""
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Bạn là chuyên gia trích xuất thông tin từ CCCD (Căn cước công dân) Việt Nam. Hãy phân tích text OCR sau đây và trích xuất thông tin theo định dạng JSON.

MẶT TRƯỚC (OCR Text):
{text_front}

MẶT SAU (OCR Text):
{text_back}

Hãy trích xuất các thông tin sau từ CCCD:
1. Số CCCD: Số 12 chữ số (ví dụ: 080188012880) - LƯU Ý: Đọc chính xác từng chữ số, đặc biệt là năm (ví dụ: 1988 không phải 1980)
2. Họ và tên: Tên đầy đủ
3. Ngày sinh: Format DD/MM/YYYY (ví dụ: 01/01/1988)
4. Giới tính: Nam hoặc Nữ
5. Quốc tịch: Thường là "Việt Nam"
6. Quê quán: Địa chỉ quê quán (có thể trên nhiều dòng, lấy toàn bộ)
7. Nơi thường trú: Địa chỉ thường trú (có thể trên nhiều dòng, lấy toàn bộ)
8. Ngày cấp: Format DD/MM/YYYY
9. Nơi cấp: Cơ quan cấp CCCD (ví dụ: "Công an thành phố Hồ Chí Minh")

QUAN TRỌNG:
- Số CCCD: Phải chính xác 12 chữ số, đặc biệt đọc đúng năm sinh (1988 không phải 1980)
- Quê quán và Nơi thường trú: Có thể xuất hiện trên nhiều dòng hoặc không thẳng hàng với label. Hãy đọc toàn bộ địa chỉ, bao gồm cả các dòng phía dưới label.
- Ngày sinh: Đọc chính xác tất cả các chữ số, đặc biệt là năm (1988 không phải 1980)
- Giữ nguyên dấu tiếng Việt

Trả về JSON với format:
{{
    "Số CCCD": "080188012880",
    "Họ và tên": "Nguyễn Văn A",
    "Ngày sinh": "01/01/1988",
    "Giới tính": "Nam",
    "Quốc tịch": "Việt Nam",
    "Quê quán": "Xã ABC, Huyện XYZ, Tỉnh DEF",
    "Nơi thường trú": "Số 123 Đường ABC, Phường XYZ, Quận DEF, TP. Hồ Chí Minh",
    "Ngày cấp": "01/01/2020",
    "Nơi cấp": "Công an thành phố Hồ Chí Minh"
}}

Chỉ trả về JSON, không có text thêm."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia trích xuất thông tin từ CCCD Việt Nam. Trả về kết quả dưới dạng JSON chính xác."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Loại bỏ markdown code blocks nếu có
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON
        data = json.loads(result_text)
        return data
        
    except json.JSONDecodeError as e:
        st.warning(f"Cảnh báo: Không thể parse JSON từ OpenAI. Lỗi: {str(e)}")
        st.text(f"Response: {result_text}")
        return None
    except Exception as e:
        st.error(f"Lỗi khi gọi OpenAI API: {str(e)}")
        return None

def extract_cccd_info(image_front, image_back):
    """Trích xuất thông tin từ ảnh CCCD mặt trước và sau (phương pháp regex)"""
    info = {
        'Số CCCD': '',
        'Họ và tên': '',
        'Ngày sinh': '',
        'Giới tính': '',
        'Quốc tịch': '',
        'Quê quán': '',
        'Nơi thường trú': '',
        'Ngày cấp': '',
        'Nơi cấp': ''
    }
    
    try:
        text_front = extract_text_with_ocr(image_front)
        text_back = extract_text_with_ocr(image_back)
        
        full_text = text_front + "\n" + text_back
        
        # Trích xuất số CCCD
        so_no_pattern = r'(?:Số|SO)\s*[/\\]\s*No\.?\s*[:]'
        so_no_match = re.search(so_no_pattern, text_front, re.IGNORECASE)
        if so_no_match:
            text_after_label = text_front[so_no_match.end():]
            number_match = re.search(r'\s*(\d{12})(?:\s|$|\n|[^\d])', text_after_label[:50])
            if number_match:
                info['Số CCCD'] = number_match.group(1)
        
        # Trích xuất Họ và tên
        ten_patterns = [
            r'(?:Họ\s+và\s+tên|HO\s+VA\s+TEN|Full\s+name)[:]\s*([A-ZÀ-Ỹ\s]+?)(?:\n|$)',
            r'(?:Họ\s+tên)[:]\s*([A-ZÀ-Ỹ\s]+?)(?:\n|$)',
        ]
        for pattern in ten_patterns:
            match = re.search(pattern, text_front, re.IGNORECASE | re.MULTILINE)
            if match:
                info['Họ và tên'] = match.group(1).strip()
                break
        
        # Trích xuất Ngày sinh
        ngay_sinh_patterns = [
            r'(?:Ngày\s+sinh|NGAY\s+SINH|Date\s+of\s+birth)[:]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
            r'(?:Ngày\s+sinh)[:].*?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
        ]
        for pattern in ngay_sinh_patterns:
            match = re.search(pattern, text_front, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                info['Ngày sinh'] = match.group(1).replace('-', '/').replace('.', '/')
                break
        
        # Trích xuất Giới tính
        if re.search(r'Giới\s+tính[:]\s*Nam|GIOI\s+TINH[:]\s*NAM', text_front, re.IGNORECASE):
            info['Giới tính'] = "Nam"
        elif re.search(r'Giới\s+tính[:]\s*Nữ|GIOI\s+TINH[:]\s*NU', text_front, re.IGNORECASE):
            info['Giới tính'] = "Nữ"
        
        # Trích xuất Quốc tịch
        quoc_tich_match = re.search(r'(?:Quốc\s+tịch|QUOC\s+TICH|Nationality)[:]\s*([A-ZÀ-Ỹ\s]+)', text_front, re.IGNORECASE)
        if quoc_tich_match:
            info['Quốc tịch'] = quoc_tich_match.group(1).strip()
        
        # Trích xuất Quê quán (multi-line)
        que_quan_match = re.search(r'(?:Quê\s+quán|QUE\s+QUAN|Place\s+of\s+origin)[:]\s*', text_front, re.IGNORECASE)
        if que_quan_match:
            start_pos = que_quan_match.end()
            remaining_text = text_front[start_pos:start_pos+500]
            lines = remaining_text.split('\n')
            que_quan_parts = []
            for line in lines[:5]:
                line = line.strip()
                if line and not re.match(r'^(Nơi|NOI|Permanent|Address)', line, re.IGNORECASE):
                    que_quan_parts.append(line)
                else:
                    break
            if que_quan_parts:
                info['Quê quán'] = ', '.join(que_quan_parts).strip(', ')
        
        # Trích xuất Nơi thường trú (multi-line)
        thuong_tru_match = re.search(r'(?:Nơi\s+thường\s+trú|NOI\s+THUONG\s+TRU|Permanent\s+address)[:]\s*', text_back or text_front, re.IGNORECASE)
        if thuong_tru_match:
            start_pos = thuong_tru_match.end()
            source_text = (text_back if text_back else text_front)
            remaining_text = source_text[start_pos:start_pos+500]
            lines = remaining_text.split('\n')
            thuong_tru_parts = []
            for line in lines[:5]:
                line = line.strip()
                if line and not re.match(r'^(Ngày|NGAY|Date|Quê|QUE)', line, re.IGNORECASE):
                    thuong_tru_parts.append(line)
                else:
                    break
            if thuong_tru_parts:
                info['Nơi thường trú'] = ', '.join(thuong_tru_parts).strip(', ')
        
        # Trích xuất Ngày cấp
        ngay_cap_match = re.search(r'(?:Ngày\s+cấp|NGAY\s+CAP|Date\s+of\s+issue)[:]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})', text_back or text_front, re.IGNORECASE)
        if ngay_cap_match:
            info['Ngày cấp'] = ngay_cap_match.group(1).replace('-', '/').replace('.', '/')
        
        # Trích xuất Nơi cấp
        noi_cap_match = re.search(r'(?:Nơi\s+cấp|NOI\s+CAP|Place\s+of\s+issue)[:]\s*([A-ZÀ-Ỹ0-9\s,\.]+)', text_back or text_front, re.IGNORECASE)
        if noi_cap_match:
            info['Nơi cấp'] = noi_cap_match.group(1).strip()
        
        return info
        
    except Exception as e:
        st.error(f"Lỗi khi trích xuất thông tin: {str(e)}")
        return info

def process_cccd_extraction(image_front, image_back, use_openai, api_key):
    """Xử lý trích xuất thông tin CCCD"""
    try:
        text_front = extract_text_with_ocr(image_front)
        text_back = extract_text_with_ocr(image_back)
        
        if use_openai and api_key and OPENAI_AVAILABLE:
            with st.spinner("🤖 Đang sử dụng OpenAI để trích xuất thông tin..."):
                openai_data = extract_cccd_with_openai(text_front, text_back, api_key)
                if openai_data:
                    return openai_data
                else:
                    st.info("ℹ️ Sử dụng phương pháp OCR thông thường")
                    return extract_cccd_info(image_front, image_back)
        else:
            return extract_cccd_info(image_front, image_back)
            
    except Exception as e:
        st.error(f"Lỗi khi xử lý OCR: {str(e)}")
        return None

def create_labor_contract(cccd_data, template_file=TEMPLATE_FILE):
    """Tạo hợp đồng lao động từ template và dữ liệu CCCD"""
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()
        
        today = datetime.now()
        current_day = today.strftime("%d")
        current_month = today.strftime("%m")
        current_year = today.strftime("%Y")
        
        contract = template
        
        ho_ten = cccd_data.get('Họ và tên', '')
        ngay_sinh = cccd_data.get('Ngày sinh', '')
        gioi_tinh = cccd_data.get('Giới tính', '')
        quoc_tich = cccd_data.get('Quốc tịch', '')
        so_cccd = cccd_data.get('Số CCCD', '')
        ngay_cap = cccd_data.get('Ngày cấp', '')
        noi_cap = cccd_data.get('Nơi cấp', '')
        que_quan = cccd_data.get('Quê quán', '')
        thuong_tru = cccd_data.get('Nơi thường trú', '')
        
        xung_ho = "Ông/bà"
        if gioi_tinh and "Nam" in gioi_tinh:
            xung_ho = "Ông"
        elif gioi_tinh and "Nữ" in gioi_tinh:
            xung_ho = "Bà"
        
        replacements = {
            '[Nguoi_LD]': ho_ten,
            '[Ngay_sinh]': ngay_sinh,
            '[Gioi_tinh]': gioi_tinh,
            '[Quoc_tich]': quoc_tich,
            '[So_CCCD]': so_cccd,
            '[Ngay_cap]': ngay_cap,
            '[Noi_cap]': noi_cap,
            '[Que_quan]': que_quan,
            '[DC_LH]': thuong_tru if thuong_tru else que_quan,
            'Ông/bà :': f'{xung_ho}:',
            'Hôm nay ngày ... tháng ... năm 2020': f'Hôm nay ngày {current_day} tháng {current_month} năm {current_year}',
            '...': 'Tp. Hồ Chí Minh',
        }
        
        for placeholder, value in replacements.items():
            contract = contract.replace(placeholder, value)
        
        return contract
    except Exception as e:
        st.error(f"Lỗi khi tạo hợp đồng: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

def generate_pdf_contract(contract_text, output_file):
    """Tạo file PDF từ nội dung hợp đồng với hỗ trợ tiếng Việt"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        import os
        
        font_name = 'Helvetica'
        try:
            font_paths = [
                "C:/Windows/Fonts/times.ttf",
                "C:/Windows/Fonts/timesbd.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font_base_name = os.path.splitext(os.path.basename(font_path))[0]
                        pdfmetrics.registerFont(TTFont(font_base_name, font_path))
                        if 'times' in font_base_name.lower():
                            font_name = font_base_name
                            break
                    except:
                        continue
        except:
            pass
        
        doc = SimpleDocTemplate(output_file, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        styles = getSampleStyleSheet()
        
        normal_style = ParagraphStyle(
            'Normal_VN',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            encoding='utf-8'
        )
        
        title_style = ParagraphStyle(
            'Title_VN',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            encoding='utf-8'
        )
        
        lines = contract_text.split('\n')
        story = []
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*cm))
                continue
            
            line_html = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if line.isupper() and len(line) < 100 and any(keyword in line for keyword in ['CỘNG HÒA', 'HỢP ĐỒNG', 'NGƯỜI LAO ĐỘNG', 'NGƯỜI SỬ DỤNG']):
                para = Paragraph(line_html, title_style)
            else:
                para = Paragraph(line_html, normal_style)
            
            story.append(para)
            story.append(Spacer(1, 0.2*cm))
        
        doc.build(story)
        return True
    except Exception as e:
        st.error(f"Lỗi khi tạo PDF: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False

# Main UI
st.markdown("### **Cấu hình nâng cao (OpenAI API - Tùy chọn)**")
use_openai = st.checkbox("Sử dụng OpenAI API để trích xuất thông tin chính xác hơn", value=True)
api_key = None
if use_openai:
    if not OPENAI_AVAILABLE:
        st.error("⚠️ Thư viện OpenAI chưa được cài đặt. Vui lòng chạy: pip install openai")
    else:
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Nhập API key của bạn từ https://platform.openai.com/api-keys",
            value=st.session_state.get('openai_api_key', DEFAULT_API_KEY or '')
        )
        if api_key:
            st.session_state['openai_api_key'] = api_key

col1, col2 = st.columns(2)

with col1:
    st.subheader("Mặt trước CCCD")
    image_front_file = st.file_uploader(
        "Chọn ảnh mặt trước",
        type=['png', 'jpg', 'jpeg'],
        key="front_hdld"
    )
    if image_front_file:
        image_front = Image.open(image_front_file)
        st.image(image_front, caption="Mặt trước CCCD", use_container_width=True)

with col2:
    st.subheader("Mặt sau CCCD")
    image_back_file = st.file_uploader(
        "Chọn ảnh mặt sau",
        type=['png', 'jpg', 'jpeg'],
        key="back_hdld"
    )
    if image_back_file:
        image_back = Image.open(image_back_file)
        st.image(image_back, caption="Mặt sau CCCD", use_container_width=True)

if image_front_file and image_back_file:
    if st.button("📝 Tạo hợp đồng lao động (PDF)", type="primary", use_container_width=True):
        with st.spinner("Đang trích xuất thông tin từ CCCD..."):
            cccd_info = process_cccd_extraction(image_front, image_back, use_openai, api_key)
        
        if cccd_info:
            # Kiểm tra thông tin tối thiểu
            if not cccd_info.get('Họ và tên') or not cccd_info.get('Số CCCD'):
                st.warning("⚠️ Không thể trích xuất đầy đủ thông tin. Vui lòng kiểm tra lại ảnh CCCD.")
                st.json(cccd_info)
            else:
                st.success("✅ Đã trích xuất thông tin thành công!")
                
                # Hiển thị thông tin đã trích xuất
                with st.expander("📋 Thông tin đã trích xuất (Kiểm tra)", expanded=True):
                    st.write(f"**Họ và tên:** {cccd_info.get('Họ và tên', '')}")
                    st.write(f"**Số CCCD:** {cccd_info.get('Số CCCD', '')}")
                    st.write(f"**Ngày sinh:** {cccd_info.get('Ngày sinh', '')}")
                    st.write(f"**Giới tính:** {cccd_info.get('Giới tính', '')}")
                    st.write(f"**Quốc tịch:** {cccd_info.get('Quốc tịch', '')}")
                    st.write(f"**Quê quán:** {cccd_info.get('Quê quán', '')}")
                    st.write(f"**Nơi thường trú:** {cccd_info.get('Nơi thường trú', '')}")
                    st.write(f"**Ngày cấp:** {cccd_info.get('Ngày cấp', '')}")
                    st.write(f"**Nơi cấp:** {cccd_info.get('Nơi cấp', '')}")
                
                with st.spinner("Đang tạo hợp đồng lao động..."):
                    contract_text = create_labor_contract(cccd_info)
                    
                    if contract_text:
                        safe_name = "".join(c for c in cccd_info.get('Họ và tên', '') if c.isalnum() or c in (' ', '-', '_')).strip()
                        pdf_filename = f"HDLD_{safe_name}_{cccd_info.get('Số CCCD', '')}.pdf"
                        
                        if generate_pdf_contract(contract_text, pdf_filename):
                            st.success(f"✅ Đã tạo hợp đồng lao động: {pdf_filename}")
                            st.balloons()
                            
                            with open(pdf_filename, "rb") as pdf_file:
                                st.download_button(
                                    label="📥 Tải xuống hợp đồng (PDF)",
                                    data=pdf_file,
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True
                                )
        else:
            st.error("❌ Không thể trích xuất thông tin từ CCCD. Vui lòng thử lại hoặc kiểm tra chất lượng ảnh.")

elif image_front_file or image_back_file:
    st.warning("⚠️ Vui lòng upload cả 2 ảnh (mặt trước và mặt sau)")
