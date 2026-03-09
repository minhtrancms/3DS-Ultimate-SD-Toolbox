# 🚀 3DS Ultimate SD Toolbox (macOS & Windows)

Bạn đau đầu với việc phải tải quá nhiều file rườm rà mỗi lần muốn Format và Reset hoặc mới mua máy Nintendo 3DS? 
Không biết cách khắc phục các lỗi màn hình đen thui sau khi Format máy?
Toolbox này được sinh ra để biến việc đó trở thành quy trình "1-Click To Win" siêu việt! 

## 🔥 Tính năng nổi bật ("Killer Features")
- 🔎 **Cross-Platform Auto Detect**: Hỗ trợ quét thẻ SD tự động cho cả hệ điều hành Windows lẫn macOS (hoạt động đa nền tảng). Nhận diện dung lượng chi tiết.
- 💡 **Format Format FAT32 Checker**: Chống "mù" thẻ, công cụ tự báo lỗi ngăn chặn Format sai dịnh dạng (exFAT/NTFS) đảm bảo 3DS đọc được.
- 🔓 **Luma3DS Auto Installer**: Tự kết nối qua Github API, móc phiên bản Luma3DS v13+ mới nhất xả thẳng vào thẻ.
- 📁 **Cấu trúc Thư mục chuẩn**: Tự động xây dựng rễ `3ds/`, `cias/`, `luma/payloads`, ... theo chuẩn quốc tế.
- 📦 **Tải Apps Cứu Hộ Thiết Yếu**: Tự động tải tất cả công cụ không thể sống thiếu gồm: `FBI`, `hShop (Universal-Updater)`, `Anemone3DS`, `Checkpoint`, `FTPD`, và siêu ứng dụng cứu game ảo `Faketik`.
- ⚙️ **Finalize Setup Ready**: Tích hợp sẵn Script cài đặt TỰ ĐỘNG, thả thẻ nhớ vào máy 3DS bấm phím tắt là tự tuôn ra toàn bộ game và ứng dụng ở màn hình chính!
- 🕹️ **Kéo thả / Copy Game 3DS hàng loạt**: Tha hồ chọn nhiều rổ game `.cia` hoặc `.3ds` quăng thẳng vào thẻ từ Tool.
- ✏️ **Quản lý Thẻ An toàn**: Tool đổi tên (Rename) định dạng FAT32 chuẩn, Eject thoát thẻ chuẩn để khỏi hỏng dữ liệu.

## 💻 Cách cài đặt & Chạy Tool

Bản CLI (Cửa sổ dòng lệnh Terminal) thì không cần cài thêm thư viện nào, hoàn toàn xài module hệ thống thuần Python 3:
```bash
python3 3ds_toolbox_cli.py
```

Bản GUI (Giao diện Cửa sổ) yêu cầu cài thẻ thư viện giao diện PyQt6:
```bash
pip install -r requirements.txt
python3 3ds_toolbox.py
```

> **Lưu ý**: Khuyến cáo dùng thẻ nhớ dưới 64GB format FAT32 (hoặc cao hơn nhưng Format cluster 32kb bằng GUIFormat) để trải nghiệm đạt đỉnh điểm nhất! Chúc bạn hồi sinh 3DS thành công! 🌟
