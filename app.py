import os
import sys
import tempfile
import time
import streamlit as st
from PIL import Image
import numpy as np
from processor import VideoBGRemover

# Page configuration
st.set_page_config(
    page_title="AI Video Background Remover",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 20px;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if "remover" not in st.session_state:
    st.session_state.remover = VideoBGRemover()

remover = st.session_state.remover

# Header section
st.markdown('<div class="main-header">🎬 PHẦN MỀM XÓA & THAY THẾ NỀN VIDEO AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Tách nền video tự động bằng trí tuệ nhân tạo (AI), hỗ trợ Phông xanh, Ảnh nền, Video nền & Làm mờ nền</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Cấu hình Xử lý")

# Model selection
model_options = {
    "u2net": "🤖 u2net (Chuẩn xác & Đa năng)",
    "u2net_human_seg": "👤 u2net_human_seg (Tối ưu cho Người)",
    "isnet-general-use": "✨ isnet-general-use (Độ nét cao)",
    "silueta": "⚡ silueta (Siêu nhanh)",
    "u2netp": "🪶 u2netp (Gọn nhẹ)"
}

model_key = st.sidebar.selectbox(
    "Mô hình AI Tách nền:",
    options=list(model_options.keys()),
    format_func=lambda x: model_options[x],
    index=0
)

# Background mode selection
bg_mode_options = {
    "color_green": "🟩 Phông xanh (Green Screen - Mặc định)",
    "color_custom": "🎨 Màu đơn sắc tùy chọn",
    "image": "🖼️ Thay bằng Hình ảnh mới",
    "video": "🎬 Thay bằng Video mới",
    "blur": "🌀 Làm mờ nền gốc (Bokeh)",
    "transparent": "🫥 Nền trong suốt (Chroma Key Green)"
}

bg_choice = st.sidebar.selectbox(
    "Loại nền thay thế:",
    options=list(bg_mode_options.keys()),
    format_func=lambda x: bg_mode_options[x],
    index=0
)

# Dynamic controls based on background selection
bg_color_rgb = (0, 255, 0) # default BGR is (0, 255, 0)
custom_bg_img = None
custom_bg_video_path = None
blur_radius = 15

if bg_choice == "color_green" or bg_choice == "transparent":
    bg_type = "color"
    bg_color_bgr = (0, 255, 0)
elif bg_choice == "color_custom":
    bg_type = "color"
    hex_color = st.sidebar.color_picker("Chọn màu nền:", "#00FF00")
    # Convert hex to BGR
    hex_clean = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
    bg_color_bgr = (b, g, r)
elif bg_choice == "image":
    bg_type = "image"
    img_file = st.sidebar.file_uploader("Tải lên ảnh làm nền (JPG, PNG):", type=["jpg", "jpeg", "png"])
    if img_file:
        pil_bg = Image.open(img_file).convert("RGB")
        custom_bg_img = np.array(pil_bg)
elif bg_choice == "video":
    bg_type = "video"
    vid_file = st.sidebar.file_uploader("Tải lên video làm nền (MP4, MOV):", type=["mp4", "mov", "avi"])
    if vid_file:
        t_bg_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        t_bg_vid.write(vid_file.read())
        t_bg_vid.close()
        custom_bg_video_path = t_bg_vid.name
elif bg_choice == "blur":
    bg_type = "blur"
    bg_color_bgr = (0, 0, 0)
    blur_radius = st.sidebar.slider("Độ mờ nền (Blur Radius):", min_value=5, max_value=51, value=25, step=2)

st.sidebar.markdown("---")
st.sidebar.header("🎨 Tinh chỉnh Viền & Tốc độ")

feather_amount = st.sidebar.slider("Độ mịn viền (Feathering):", min_value=0, max_value=10, value=2, step=1)

resolution_scale = st.sidebar.select_slider(
    "Tỷ lệ độ phân giải xuất (Scale):",
    options=[0.5, 0.75, 1.0],
    value=1.0,
    format_func=lambda x: f"{int(x*100)}%"
)

# Main area: File Upload & Info
uploaded_file = st.file_uploader("📁 Tải lên Video cần xóa nền (MP4, MOV, AVI, MKV):", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    # Save input video to temp file
    temp_input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_input_file.write(uploaded_file.read())
    temp_input_file.close()
    input_video_path = temp_input_file.name

    try:
        info = remover.get_video_info(input_video_path)
        
        # Display video meta details
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kích thước", f"{info['width']} x {info['height']}")
        c2.metric("Số khung hình", f"{info['total_frames']} frames")
        c3.metric("Tốc độ khung hình", f"{info['fps']:.2f} FPS")
        c4.metric("Thời lượng", f"{info['duration']:.1f} giây")

        st.markdown("---")
        st.subheader("👁️ Xem trước Kết quả trên 1 Khung hình (Preview)")
        
        preview_sec = st.slider(
            "Kéo thanh để chọn thời điểm xem trước (giây):", 
            min_value=0.0, 
            max_value=max(0.1, info['duration'] - 0.1), 
            value=min(1.0, info['duration']/2),
            step=0.1
        )

        # Trigger Preview
        if st.button("🔍 Cập nhật Preview", use_container_width=True):
            with st.spinner("Đang AI xử lý frame xem trước..."):
                try:
                    orig_img, proc_img = remover.get_preview_frame(
                        video_path=input_video_path,
                        frame_time_sec=preview_sec,
                        model_name=model_key,
                        bg_type=bg_type,
                        bg_color=bg_color_bgr if 'bg_color_bgr' in locals() else (0, 255, 0),
                        bg_image_rgb=custom_bg_img,
                        blur_radius=blur_radius,
                        feather_amount=feather_amount
                    )
                    
                    col_orig, col_proc = st.columns(2)
                    with col_orig:
                        st.caption("Frame Gốc")
                        st.image(orig_img, use_column_width=True)
                    with col_proc:
                        st.caption("Frame Xóa & Thay Nền AI")
                        st.image(proc_img, use_column_width=True)
                except Exception as e:
                    st.error(f"Lỗi khi xem trước: {e}")

        st.markdown("---")
        st.subheader("🚀 Tiến hành Tách & Xuất Video")

        if st.button("▶️ BẮT ĐẦU XỬ LÝ TOÀN BỘ VIDEO", type="primary", use_container_width=True):
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            m1, m2, m3 = st.columns(3)
            metric_frames = m1.empty()
            metric_speed = m2.empty()
            metric_eta = m3.empty()

            def update_progress(current_frame, total_frames, current_fps, eta):
                percent = min(1.0, current_frame / total_frames) if total_frames > 0 else 0
                progress_bar.progress(percent)
                status_text.text(f"Đang xử lý khung hình {current_frame} / {total_frames} ({percent*100:.1f}%)")
                
                metric_frames.metric("Khung hình đã xử lý", f"{current_frame} / {total_frames}")
                metric_speed.metric("Tốc độ xử lý", f"{current_fps:.1f} FPS")
                metric_eta.metric("Thời gian còn lại (dự kiến)", f"{eta:.1f} s")

            with st.spinner("Hệ thống đang chạy AI tách nền video... Vui lòng đợi trong giây lát."):
                start_time = time.time()
                try:
                    remover.process_video(
                        video_path=input_video_path,
                        output_path=output_file,
                        model_name=model_key,
                        bg_type=bg_type,
                        bg_color=bg_color_bgr if 'bg_color_bgr' in locals() else (0, 255, 0),
                        bg_image_rgb=custom_bg_img,
                        bg_video_path=custom_bg_video_path,
                        blur_radius=blur_radius,
                        feather_amount=feather_amount,
                        scale=resolution_scale,
                        progress_callback=update_progress
                    )
                    
                    elapsed = time.time() - start_time
                    st.success(f"🎉 Xử lý thành công toàn bộ video trong {elapsed:.1f} giây!")
                    
                    # Display result video
                    st.video(output_file)
                    
                    # Download button
                    with open(output_file, "rb") as f:
                        video_bytes = f.read()
                        st.download_button(
                            label="📥 TẢI VIDEO KẾT QUẢ VỀ MÁY",
                            data=video_bytes,
                            file_name="video_removed_bg.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                except Exception as ex:
                    st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {ex}")
                finally:
                    # Clean up temporary background video if used
                    if custom_bg_video_path and os.path.exists(custom_bg_video_path):
                        try:
                            os.remove(custom_bg_video_path)
                        except Exception:
                            pass

    except Exception as err:
        st.error(f"Lỗi khi đọc file video: {err}")
    finally:
        # Clean temp input video
        pass

else:
    st.info("👆 Vui lòng tải lên một file video ở phía trên để bắt đầu.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Phần mềm Xóa Nền Video AI © 2026 - Powered by Streamlit & RemBG</div>", unsafe_allow_html=True)
