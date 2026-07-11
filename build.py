import os
import subprocess
import sys
import zipfile

def build():
    print("Starting magAutoTone build process...")
    
    # Đảm bảo PyInstaller đã được cài đặt
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
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
    
    print(f"Running command: {' '.join(command)}")
    print("Please wait, packaging AI libraries (Torch/Demucs) can take several minutes...")
    
    # Chạy lệnh build
    try:
        subprocess.check_call(command)
        
        # Nén thành file zip
        print("\nCompressing into ZIP file...")
        zip_path = os.path.join("dist", "magAutoTone.zip")
        exe_path = os.path.join("dist", "magAutoTone.exe")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(exe_path, arcname="magAutoTone.exe")
            
        print("\n" + "="*50)
        print("BUILD & COMPRESS SUCCESSFUL! Check the 'dist' folder for magAutoTone.zip")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")

if __name__ == "__main__":
    build()
