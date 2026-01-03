"""
Ứng dụng Lịch Giảng Dạy - Streamlit
Đọc dữ liệu từ file ThongKeTKB*.xlsx (xuất từ th1.py)
Hiển thị dạng Calendar cho giảng viên dễ theo dõi
"""

import streamlit as st
import pandas as pd
import os
import glob
import re
from datetime import datetime
from streamlit_calendar import calendar

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Lịch Giảng Dạy", 
    page_icon="📅",
    layout="wide"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
    <style>
    .fc-event-title {
        font-weight: bold !important;
        font-size: 11px !important;
    }
    .fc-daygrid-event {
        white-space: normal !important;
    }
    .stDialog > div {
        max-width: 700px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MAPPING ĐƠN VỊ ---
DON_VI_COLORS = {
    "Khoa Chính sách công": "#4472C4",
    "Khoa Phát triển nông thôn": "#70AD47",
    "Khoa Quản trị kinh doanh nông nghiệp": "#ED7D31",
    "Trung tâm Kinh tế hợp tác": "#9E480E",
    "Trung tâm Đào tạo nông dân": "#7030A0",
    "Giảng viên mời": "#808080",
}

DON_VI_SHORT = {
    "Khoa Chính sách công": "CSC",
    "Khoa Phát triển nông thôn": "PTNT",
    "Khoa Quản trị kinh doanh nông nghiệp": "QTKDNN",
    "Trung tâm Kinh tế hợp tác": "TT KTHT",
    "Trung tâm Đào tạo nông dân": "TT ĐTND",
}


# ============================================================================
# PHẦN 1: CÁC HÀM XỬ LÝ DỮ LIỆU
# ============================================================================

def tim_file_thongke():
    """Tìm file ThongKeTKB mới nhất trong thư mục"""
    cwd = os.getcwd()
    list_files = glob.glob(os.path.join(cwd, "ThongKeTKB*.xlsx"))
    if not list_files:
        return None
    return max(list_files, key=os.path.getctime)


def chuan_hoa_text(text):
    """
    Chuẩn hóa text để so sánh:
    - Loại bỏ dấu tiếng Việt
    - Chuyển thành chữ thường
    - Loại bỏ khoảng trắng thừa và ký tự đặc biệt
    """
    if not text or pd.isna(text):
        return ""
    
    text = str(text).lower().strip()
    
    # Loại bỏ dấu tiếng Việt
    replacements = {
        'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Loại bỏ ký tự đặc biệt, chỉ giữ chữ và số
    text = re.sub(r'[^\w\s]', '', text)
    # Loại bỏ khoảng trắng thừa
    text = re.sub(r'\s+', '', text)
    
    return text


def trich_xuat_keywords_tu_ten_lop(ten_lop):
    """
    Trích xuất các từ khóa quan trọng từ tên lớp
    VD: "LỚP TẬP HUẤN KIẾN THỨC KỸ NĂNG NGH'41" → ["41", "ngh", "kien", "thuc"]
    """
    if not ten_lop or pd.isna(ten_lop):
        return []
    
    text = str(ten_lop).lower()
    
    # Tìm các số (mã lớp thường có số)
    numbers = re.findall(r'\d+', text)
    
    # Tìm các từ viết tắt (chữ hoa liên tiếp)
    abbreviations = re.findall(r'\b[A-Z]{2,}\b', str(ten_lop))
    
    # Chuẩn hóa text và tách thành từ
    text_normalized = chuan_hoa_text(text)
    
    # Lấy các từ có ý nghĩa (bỏ qua "lop", "tap", "huan", etc.)
    skip_words = {'lop', 'tap', 'huan', 'boi', 'duong', 'theo', 'tieu', 'chuan', 'chu'}
    words = [w for w in re.findall(r'\w+', text_normalized) if w not in skip_words and len(w) >= 3]
    
    # Kết hợp tất cả keywords
    keywords = numbers + [chuan_hoa_text(a) for a in abbreviations] + words[:5]
    
    return [k for k in keywords if k]  # Loại bỏ empty strings


def tim_file_tkb_goc(ma_lop, ten_lop, thu_muc="."):
    """
    Tìm file TKB gốc (PDF/DOCX) dựa trên mã lớp VÀ tên lớp.
    Trả về đường dẫn file nếu tìm thấy.
    CẢI TIẾN: Tìm kiếm thông minh theo cả mã lớp và tên lớp
    """
    # Tìm tất cả file PDF và DOCX trong thư mục
    all_files = []
    for ext in ['*.pdf', '*.PDF', '*.docx', '*.DOCX']:
        all_files.extend(glob.glob(os.path.join(thu_muc, ext)))
    
    # Loại bỏ file ThongKeTKB (không phải TKB gốc)
    all_files = [f for f in all_files if 'ThongKeTKB' not in os.path.basename(f)]
    
    if not all_files:
        return None
    
    # BƯỚC 1: Tìm theo MÃ LỚP (nếu có)
    if ma_lop and not pd.isna(ma_lop):
        ma_lop_str = str(ma_lop).strip()
        if ma_lop_str and ma_lop_str.lower() != 'nan':
            ma_lop_lower = ma_lop_str.lower()
            ma_lop_clean = re.sub(r'[^\w]', '', ma_lop_str).lower()
            
            # Tìm khớp chính xác mã lớp trong tên file
            for file in all_files:
                filename_lower = os.path.basename(file).lower()
                filename_clean = re.sub(r'[^\w]', '', filename_lower)
                
                # Kiểm tra mã lớp có trong tên file
                if ma_lop_lower in filename_lower or ma_lop_clean in filename_clean:
                    return file
    
    # BƯỚC 2: Tìm theo TÊN LỚP (keywords)
    if ten_lop and not pd.isna(ten_lop):
        keywords = trich_xuat_keywords_tu_ten_lop(ten_lop)
        
        if keywords:
            # Tính điểm khớp cho mỗi file
            best_match = None
            best_score = 0
            
            for file in all_files:
                filename = os.path.basename(file)
                filename_normalized = chuan_hoa_text(filename)
                
                # Đếm số keywords khớp
                score = sum(1 for keyword in keywords if keyword in filename_normalized)
                
                if score > best_score:
                    best_score = score
                    best_match = file
            
            # Chỉ trả về nếu có ít nhất 2 keywords khớp
            if best_score >= 2:
                return best_match
    
    return None


def chuan_hoa_ngay(text):
    """Chuẩn hóa ngày từ text thành datetime"""
    if pd.isna(text):
        return None
    
    # Nếu đã là datetime
    if isinstance(text, datetime):
        return text
    
    text_str = str(text)
    
    # Tìm pattern ngày/tháng/năm
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text_str)
    if match:
        try:
            day, month, year = map(int, match.groups())
            return datetime(year, month, day)
        except:
            pass
    
    return None


def doc_file_thongke(filepath):
    """
    Đọc file ThongKeTKB và chuyển thành danh sách events cho calendar.
    CẢI TIẾN: Tìm file TKB theo cả mã lớp và tên lớp
    """
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return []
    
    events = []
    thu_muc = os.path.dirname(filepath)
    
    # Thống kê file TKB
    missing_files = []
    found_files = []
    total_rows = 0
    
    # Các cột cần thiết
    required_cols = ['Tên lớp', 'Thời gian', 'Tên chuyên đề', 'Tên giảng viên']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Thiếu cột '{col}' trong file Excel")
            return []
    
    for idx, row in df.iterrows():
        # Parse ngày
        ngay = chuan_hoa_ngay(row.get('Thời gian'))
        if not ngay:
            continue
        
        total_rows += 1
        
        # Lấy thông tin
        ten_lop = str(row.get('Tên lớp', '')).strip()
        ma_lop = str(row.get('Mã lớp', '')).strip() if pd.notna(row.get('Mã lớp')) else ''
        ten_chuyen_de = str(row.get('Tên chuyên đề', '')).strip()
        ten_gv = str(row.get('Tên giảng viên', '')).strip()
        so_tiet = row.get('Số tiết', 8)
        don_vi = str(row.get('Đơn vị (GV)', '')).strip() if pd.notna(row.get('Đơn vị (GV)')) else 'Giảng viên mời'
        tro_giang = str(row.get('Trợ giảng', '')).strip() if pd.notna(row.get('Trợ giảng')) else ''
        don_vi_tg = str(row.get('vị (trợ giảng)', '')).strip() if pd.notna(row.get('vị (trợ giảng)')) else ''
        
        # Bỏ qua nếu thiếu thông tin quan trọng
        if not ten_gv or ten_gv == 'nan':
            continue
        
        # Tìm file TKB gốc (theo MÃ LỚP và TÊN LỚP)
        file_goc = tim_file_tkb_goc(ma_lop, ten_lop, thu_muc)
        
        # Thống kê
        if file_goc:
            found_files.append({
                'ma_lop': ma_lop,
                'ten_lop': ten_lop[:50],  # Cắt ngắn để hiển thị
                'file': os.path.basename(file_goc)
            })
        else:
            missing_files.append({
                'ma_lop': ma_lop if ma_lop else 'N/A',
                'ten_lop': ten_lop[:50],
                'ten_gv': ten_gv,
                'ngay': ngay.strftime("%d/%m/%Y")
            })
        
        # Màu theo đơn vị
        color = DON_VI_COLORS.get(don_vi, "#808080")
        don_vi_short = DON_VI_SHORT.get(don_vi, don_vi[:10] if don_vi else "")
        
        # Tạo title hiển thị trên calendar
        title = f"{ten_gv}"
        if don_vi_short:
            title = f"[{don_vi_short}] {ten_gv}"
        
        # Tạo event
        event = {
            "title": title,
            "start": ngay.strftime("%Y-%m-%d"),
            "end": ngay.strftime("%Y-%m-%d"),
            "backgroundColor": color,
            "borderColor": color,
            "extendedProps": {
                "ten_gv": ten_gv,
                "ten_lop": ten_lop,
                "ma_lop": ma_lop,
                "ten_chuyen_de": ten_chuyen_de,
                "so_tiet": so_tiet,
                "don_vi": don_vi,
                "tro_giang": tro_giang,
                "don_vi_tg": don_vi_tg,
                "file_goc": file_goc,
                "ngay_str": ngay.strftime("%d/%m/%Y"),
            }
        }
        events.append(event)
    
    # Hiển thị thống kê file TKB
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Tổng buổi dạy", total_rows)
    with col2:
        st.metric("✅ Có file TKB", len(found_files), delta=f"{len(found_files)/total_rows*100:.0f}%" if total_rows > 0 else "0%")
    with col3:
        st.metric("❌ Thiếu file TKB", len(missing_files), delta=f"-{len(missing_files)/total_rows*100:.0f}%" if total_rows > 0 else "0%", delta_color="inverse")
    
    # Hiển thị chi tiết nếu có file thiếu
    if missing_files:
        with st.expander(f"⚠️ Chi tiết {len(missing_files)} file TKB không tìm thấy (click để xem)"):
            st.warning("**Lưu ý:** Tên file TKB nên chứa mã lớp hoặc từ khóa trong tên lớp để dễ tìm kiếm.")
            
            # Hiển thị bảng
            df_missing = pd.DataFrame(missing_files)
            st.dataframe(
                df_missing,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ma_lop": "Mã lớp",
                    "ten_lop": "Tên lớp",
                    "ten_gv": "Giảng viên",
                    "ngay": "Ngày"
                }
            )
            
            st.info("💡 **Gợi ý:** Đổi tên file TKB để chứa mã lớp hoặc từ khóa (VD: `TKB_175_QLBVRK.pdf`, `TKB_XPVPHC_2025.pdf`)")
    
    # Hiển thị file tìm thấy (nếu muốn kiểm tra)
    if found_files and st.checkbox("🔍 Xem danh sách file TKB đã tìm thấy", value=False):
        with st.expander(f"✅ Danh sách {len(found_files)} file TKB tìm thấy"):
            df_found = pd.DataFrame(found_files)
            # Loại bỏ duplicate
            df_found = df_found.drop_duplicates(subset=['file'])
            st.dataframe(
                df_found,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ma_lop": "Mã lớp",
                    "ten_lop": "Tên lớp",
                    "file": "Tên file TKB"
                }
            )
    
    return events


def loc_events(events, filter_gv=None, filter_don_vi=None, filter_lop=None):
    """Lọc events theo các tiêu chí"""
    result = events
    
    if filter_gv and filter_gv != "Tất cả":
        result = [e for e in result if filter_gv.lower() in e['extendedProps']['ten_gv'].lower()]
    
    if filter_don_vi and filter_don_vi != "Tất cả":
        result = [e for e in result if filter_don_vi in e['extendedProps']['don_vi']]
    
    if filter_lop and filter_lop != "Tất cả":
        result = [e for e in result if filter_lop.lower() in e['extendedProps']['ten_lop'].lower()]
    
    return result


# ============================================================================
# PHẦN 2: GIAO DIỆN
# ============================================================================

@st.dialog("📋 Chi tiết buổi giảng")
def show_event_dialog(props):
    """Hiển thị popup chi tiết khi click vào event"""
    st.markdown(f"### 👨‍🏫 {props.get('ten_gv', 'N/A')}")
    st.caption(f"📅 Ngày: **{props.get('ngay_str', '')}**")
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏢 Đơn vị:**")
        don_vi = props.get('don_vi', 'N/A')
        if don_vi and don_vi != 'nan':
            st.info(don_vi)
        else:
            st.info("Giảng viên mời")
        
        st.markdown("**⏱️ Số tiết:**")
        st.warning(f"{props.get('so_tiet', 'N/A')} tiết")
        
        if props.get('tro_giang'):
            st.markdown("**👥 Trợ giảng:**")
            st.write(props.get('tro_giang'))
            if props.get('don_vi_tg'):
                st.caption(f"Đơn vị: {props.get('don_vi_tg')}")
    
    with col2:
        st.markdown("**🏫 Tên lớp:**")
        st.write(props.get('ten_lop', 'N/A'))
        
        if props.get('ma_lop'):
            st.markdown("**🔢 Mã lớp:**")
            st.code(props.get('ma_lop'))
    
    st.divider()
    st.markdown("**📖 Tên chuyên đề:**")
    st.success(props.get('ten_chuyen_de', 'N/A'))
    
    # Nút xem file TKB gốc
    st.divider()
    file_goc = props.get('file_goc')
    if file_goc and os.path.exists(file_goc):
        file_name = os.path.basename(file_goc)
        with open(file_goc, "rb") as f:
            st.download_button(
                label=f"📥 Tải TKB gốc: {file_name}",
                data=f,
                file_name=file_name,
                mime="application/octet-stream"
            )
    else:
        st.caption("📄 Không tìm thấy file TKB gốc")
        if props.get('ma_lop'):
            st.caption(f"💡 Gợi ý: Đặt tên file chứa mã lớp **{props.get('ma_lop')}** hoặc từ khóa trong tên lớp")


def main():
    st.title("📅 Lịch Giảng Dạy")
    
    # --- SIDEBAR: Upload và Filter ---
    with st.sidebar:
        st.header("📂 Nguồn dữ liệu")
        
        # Option 1: Tự động tìm file
        auto_file = tim_file_thongke()
        
        # Option 2: Upload file
        uploaded_file = st.file_uploader(
            "Hoặc upload file ThongKeTKB", 
            type=['xlsx', 'xls']
        )
        
        # Xác định file sử dụng
        if uploaded_file:
            # Lưu file tạm
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_to_use = temp_path
            st.success(f"✅ Đã upload: {uploaded_file.name}")
        elif auto_file:
            file_to_use = auto_file
            st.info(f"📄 Sử dụng: {os.path.basename(auto_file)}")
        else:
            file_to_use = None
            st.warning("⚠️ Không tìm thấy file ThongKeTKB")
        
        st.divider()
        
        # --- FILTER ---
        st.header("🔍 Bộ lọc")
    
    # --- MAIN CONTENT ---
    if not file_to_use:
        st.info("👋 Vui lòng upload file ThongKeTKB hoặc đặt file vào thư mục hiện tại.")
        st.markdown("""
        ### Hướng dẫn:
        1. Chạy `python3 th1.py` để tạo file `ThongKeTKB_*.xlsx`
        2. Upload file hoặc đặt cùng thư mục với app này
        3. Xem lịch giảng dạy theo dạng Calendar
        """)
        return
    
    # Load dữ liệu
    if 'events' not in st.session_state or st.session_state.get('file_path') != file_to_use:
        with st.spinner('Đang tải dữ liệu...'):
            st.session_state.events = doc_file_thongke(file_to_use)
            st.session_state.file_path = file_to_use
    
    events = st.session_state.events
    
    if not events:
        st.warning("Không có dữ liệu lịch giảng.")
        return
    
    # --- SIDEBAR FILTERS (tiếp) ---
    with st.sidebar:
        # Lấy danh sách unique values
        all_gv = sorted(set(e['extendedProps']['ten_gv'] for e in events))
        all_don_vi = sorted(set(e['extendedProps']['don_vi'] for e in events if e['extendedProps']['don_vi']))
        all_lop = sorted(set(e['extendedProps']['ten_lop'] for e in events))
        
        filter_don_vi = st.selectbox(
            "Đơn vị:",
            ["Tất cả"] + all_don_vi
        )
        
        filter_gv = st.selectbox(
            "Giảng viên:",
            ["Tất cả"] + all_gv
        )
        
        filter_lop = st.selectbox(
            "Lớp:",
            ["Tất cả"] + all_lop[:20]  # Giới hạn 20 để không quá dài
        )
        
        st.divider()
        
        # Thống kê nhanh
        st.header("📊 Thống kê")
        filtered_events = loc_events(events, filter_gv, filter_don_vi, filter_lop)
        st.metric("Tổng số buổi dạy", len(filtered_events))
        
        # Thống kê theo đơn vị
        if filter_don_vi == "Tất cả":
            st.markdown("**Theo đơn vị:**")
            for dv in all_don_vi:
                count = len([e for e in filtered_events if e['extendedProps']['don_vi'] == dv])
                if count > 0:
                    short = DON_VI_SHORT.get(dv, dv[:8])
                    st.caption(f"• {short}: {count} buổi")
    
    # --- CALENDAR ---
    filtered_events = loc_events(events, filter_gv, filter_don_vi, filter_lop)
    
    # Cấu hình Calendar
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek"
        },
        "initialView": "dayGridMonth",
        "height": 700,
        "selectable": True,
        "dayMaxEvents": 3,
        "locale": "vi",
        "buttonText": {
            "today": "Hôm nay",
            "month": "Tháng",
            "week": "Tuần",
            "list": "Danh sách"
        }
    }
    
    # Hiển thị Calendar
    calendar_state = calendar(
        events=filtered_events, 
        options=calendar_options, 
        key='teaching_calendar'
    )
    
    # Xử lý khi click vào event
    if calendar_state.get("eventClick"):
        event_data = calendar_state["eventClick"]["event"]
        props = event_data.get("extendedProps", {})
        
        # Gọi dialog popup
        show_event_dialog(props)
    
    # --- LEGEND ---
    st.divider()
    st.markdown("### 🎨 Chú thích màu")
    cols = st.columns(len(DON_VI_COLORS))
    for i, (dv, color) in enumerate(DON_VI_COLORS.items()):
        with cols[i]:
            short = DON_VI_SHORT.get(dv, dv[:10])
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:2px 8px;border-radius:4px;">{short}</span>',
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    main()