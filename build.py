import os
import subprocess
import sys

def build():
    print("Bắt đầu tiến trình Build magAutoTone ra file .exe...")
    
    # Đảm bảo PyInstaller đã được cài đặt
    try:
        import PyInstaller
    except ImportError:
        print("Chưa cài đặt PyInstaller. Đang cài đặt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Đường dẫn đến file chính
    main_script = os.path.join("src", "main.py")
    
    # Xây dựng lệnh gọi PyInstaller
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",           # Ẩn console khi chạy
        "--onefile",             # Gói gọn thành 1 file .exe duy nhất
        "--name", "magAutoTone", # Tên file exe đầu ra
        "--collect-data", "tkinterdnd2", # Yêu cầu bắt buộc của thư viện kéo thả
        "--collect-data", "customtkinter",
        "--collect-data", "librosa",
        "--hidden-import", "tkinterdnd2",
        "--hidden-import", "librosa",
        "--hidden-import", "demucs",
        "--hidden-import", "torch",
        "--hidden-import", "torchaudio",
        "--clean",               # Xóa cache cũ trước khi build
        main_script
    ]
    
    print(f"Đang chạy lệnh: {' '.join(command)}")
    print("Vui lòng kiên nhẫn chờ đợi, quá trình build các thư viện AI nặng như Torch và Demucs có thể mất vài phút...")
    
    # Chạy lệnh build
    try:
        subprocess.check_call(command)
        print("\n" + "="*50)
        print("BUILD THÀNH CÔNG! File magAutoTone.exe nằm trong thư mục 'dist'")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"\nLỗi trong quá trình build: {e}")

if __name__ == "__main__":
    build()
