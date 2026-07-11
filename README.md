# AutoTone Desktop App

Ứng dụng phân tích âm nhạc (BPM, Key) và tách Stem (Vocals, Bass, Drums, Other) từ file Audio và Video.

## Cài đặt (Installation)

1. Cài đặt Python 3.9+ (khuyến nghị 3.10 hoặc 3.11).
2. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
   *Lưu ý: Đối với `demucs`, bạn có thể cần cài đặt phiên bản PyTorch hỗ trợ CUDA (GPU) nếu muốn tách stem nhanh hơn.*

## Sử dụng (Usage)

Chạy ứng dụng:
```bash
python src/main.py
```

## Đóng gói ứng dụng (Building Executable)

Để đóng gói thành file `.exe` bằng PyInstaller và khắc phục lỗi `FileNotFoundError` khi chạy file exe (do đường dẫn tài nguyên):

```bash
pyinstaller --noconfirm --onedir --windowed --add-data "src;src" src/main.py
```
Hoặc nếu muốn build 1 file `.exe` duy nhất (có thể load chậm lúc mở):
```bash
pyinstaller --noconfirm --onefile --windowed --add-data "src;src" src/main.py
```

*Lưu ý về Demucs:* Demucs sẽ tải model AI về máy ở lần chạy đầu tiên. Khi đóng gói PyInstaller, model sẽ lưu tại thư mục mặc định của hệ thống (`~/.cache/torch/hub/checkpoints/`).
