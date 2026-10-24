# 🎬 Phần Mềm Xóa & Thay Thế Nền Video AI (AI Video Background Remover)

Phần mềm chuyên nghiệp hỗ trợ xóa nền video tự động bằng Trí tuệ Nhân tạo (AI), cho phép thay thế bằng phông xanh, ảnh nền, video nền, làm mờ nền hoặc xuất phông trong suốt.

---

## 🌟 Tính Năng Nổi Bật

- 🤖 **Mô hình AI đa dạng**: Tích hợp các model hàng đầu như `u2net`, `u2net_human_seg`, `isnet-general-use`, `silueta`, `u2netp`.
- 🎨 **Đa dạng tùy chọn nền mới**:
  - 🟩 **Phông xanh (Chroma Key Green)**: Thuận tiện đưa vào các phần mềm edit video (CapCut, Premiere, Camtasia, DaVinci).
  - 🎨 **Màu đơn sắc tùy chọn**: Chọn bất kỳ màu sắc nào với bộ chọn màu HEX.
  - 🖼️ **Ảnh nền tùy chọn**: Tải lên ảnh JPG/PNG để ghép vào đằng sau người/vật thể.
  - 🎬 **Video nền tùy chọn**: Ghép video nền mới chuyển động theo chiều dài video gốc.
  - 🌀 **Làm mờ nền gốc (Blur / Bokeh)**: Tạo hiệu ứng xóa phông mờ chuyên nghiệp.
- 👁️ **Xem trước trực tiếp (Live Preview)**: Chọn bất kỳ giây nào trong video để xem trước kết quả tách nền frame đó trước khi xử lý toàn bộ.
- ⚡ **Tốc độ & Hiệu năng**: Tận dụng GPU CUDA (NVIDIA GeForce RTX) và ONNXRuntime giúp xử lý cực nhanh.
- 🎵 **Giữ nguyên Âm thanh gốc**: Tự động trích xuất và giữ lại track audio gốc của video.
- 📥 **Tải về 1-Click**: Tải trực tiếp video kết quả về máy.

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Chạy bằng file `run.bat` (Nhanh nhất)
1. Double click vào file **`run.bat`** trong thư mục dự án.
2. Giao diện Web GUI sẽ tự động mở ra trên trình duyệt (thường là `http://localhost:8501`).

### Cách 2: Chạy bằng lệnh Terminal / PowerShell
```bash
python -m streamlit run app.py
```

---

## 📁 Cấu Trúc Dự Án

- [app.py](file:///e:/CwAI/CwAI_Remove_bg/app.py): Giao diện người dùng Web GUI trên Streamlit.
- [processor.py](file:///e:/CwAI/CwAI_Remove_bg/processor.py): Engine xử lý AI tách nền, ghép nền & giữ audio.
- [run.bat](file:///e:/CwAI/CwAI_Remove_bg/run.bat): Script khởi động 1-click cho Windows.
- [requirements.txt](file:///e:/CwAI/CwAI_Remove_bg/requirements.txt): Thư viện Python phụ thuộc.
