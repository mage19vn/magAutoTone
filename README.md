# magAutoTone

**MagAutoTone** là ứng dụng hỗ trợ phân tích âm nhạc chuyên nghiệp. Phần mềm cho phép bạn dễ dàng kéo thả file âm thanh/video để phân tích nhịp độ (BPM), tông nhạc (Key) và tách riêng biệt các thành phần (Vocals, Bass, Drums, Other) dựa trên công nghệ AI tiên tiến.

---

## 🚀 Tính năng nổi bật
1. **Phân tích BPM & Key:** Tự động nhận diện nhịp độ và cung chứa của bản nhạc.
2. **Tách nhạc (Stem Separation):** Dùng AI (Demucs) để bóc tách bài hát thành 4 track riêng lẻ: Giọng hát, Trống, Bass, và Nhạc cụ khác.
3. **Giao diện hiện đại (Dynamic UI):** Giao diện Dark-mode sang trọng, mượt mà. Đặc biệt hỗ trợ **Tự động đổi màu toàn bộ ứng dụng (Theme Color)** theo mã HEX hoặc chọn từ bảng màu có sẵn.
4. **Auto-Updater:** Tích hợp tính năng tự động tìm kiếm, tải xuống và chép đè bản cập nhật mới nhất từ GitHub Releases cực kỳ thông minh.
5. **Hồ sơ cá nhân:** Hiển thị tên người dùng trên giao diện chính. (Yêu cầu mã Key bảo mật để đổi tên).

---

## 📖 Hướng dẫn sử dụng

### 1. Phân tích Audio/Video
- **Bước 1:** Tại màn hình chính, bạn có thể **Kéo & Thả (Drag & Drop)** một file âm thanh hoặc video trực tiếp vào khung lớn ở giữa. Hoặc click chuột vào đó để mở hộp thoại duyệt file.
- **Bước 2:** Ngay sau khi chọn file, MagAutoTone sẽ tự động phân tích và hiển thị BPM cũng như Key của bản nhạc lên màn hình. Biểu đồ sóng âm (Waveform) cũng sẽ được vẽ.

### 2. Tách nhạc (Stem Separation)
- **Bước 1:** Sau khi phân tích file thành công, bạn **Click chuột phải** vào bất kỳ vị trí trống nào trên giao diện.
- **Bước 2:** Chọn **"🪄 Tách Stem (Demucs)"** trên menu vừa hiện ra.
- **Bước 3:** Chờ đợi AI xử lý. Kết quả (các file âm thanh độc lập) sẽ được xuất ra thư mục gốc chứa file ban đầu (hoặc thư mục bạn đã chỉ định trong Cài đặt).

### 3. Cài đặt & Tuỳ chỉnh (Settings)
Nhấp vào biểu tượng bánh răng **⚙️** ở góc phải trên cùng để mở Cài đặt:
- **Thư mục xuất tệp:** Thay đổi nơi lưu các file nhạc sau khi tách.
- **Định dạng Audio:** Lựa chọn định dạng xuất ra (`.wav`, `.mp3`, `.flac`).
- **Màu chủ đạo:** Chọn nhanh 1 màu từ 5 màu có sẵn, hoặc click nút "🌈 Khác" để pha màu HEX tuỳ ý theo bảng màu nâng cao.
- **Cập nhật phần mềm:** Ấn "Kiểm tra" để hệ thống tự động tìm và tải bản vá lỗi mới nhất.

### 4. Đổi tên người dùng (Bảo mật)
- Trong phần Cài đặt, dưới mục **👤 Người dùng**, bạn sẽ thấy tên hiển thị hiện tại.
- Để đổi tên, click **"Đổi tên"**.
- Điền tên mới và **Mã Key bảo mật**. *(Mã Key này là chuỗi mã số bí mật bảo vệ quyền riêng tư, nếu nhập sai hệ thống sẽ từ chối việc đổi tên).*

---

## 🛠 Cài đặt từ Mã nguồn (Dành cho Developer)

**Yêu cầu:** Python 3.9+

```bash
# Clone repository
git clone https://github.com/mage19vn/magAutoTone.git
cd magAutoTone

# Cài đặt thư viện
pip install -r requirements.txt

# Chạy ứng dụng
python src/main.py
```
*(Lưu ý: Đối với tính năng bóc tách, `demucs` và `torch` sẽ tự tải model AI về máy tính ở lần chạy đầu tiên).*

## 📦 Build file thực thi (.zip / .exe)
Thay vì dùng dòng lệnh pyinstaller phức tạp, bạn chỉ cần chạy tool tích hợp sẵn:
```bash
python build.py
```
Hệ thống sẽ tự động build ra file `.exe` ẩn console, đính kèm đầy đủ thư viện đồ hoạ và tự động nén lại thành file `magAutoTone.zip` lưu trong thư mục `dist/`.
