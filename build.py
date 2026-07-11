import os
import subprocess
import sys
import zipfile
import json
import re
import shutil

VERSION_FILE = 'version.json'
MAIN_FILE = os.path.join('src', 'main.py')

def main():
    print("=== BẮT ĐẦU QUÁ TRÌNH BUILD MAGAUTOTONE ===")
    
    # 1. Đọc phiên bản hiện tại
    if not os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({"version": "v1.0.0", "changes": ""}, f, indent=2)
            
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    current_version = data.get("version", "v1.0.0")
    print(f"Phiên bản hiện tại: {current_version}")
    
    # 2. Nhập phiên bản mới
    new_version = input(f"Nhập phiên bản mới (Enter để tự động tăng): ").strip()
    
    if not new_version:
        # Tự động tăng phiên bản (vd: v1.0.0 -> v1.0.1)
        # Loại bỏ chữ 'v' nếu có
        pure_ver = current_version.lstrip('v')
        parts = pure_ver.split('.')
        if len(parts) == 3 and parts[-1].isdigit():
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = "v" + '.'.join(parts)
        else:
            new_version = current_version + "-1"
    
    if not new_version.startswith('v'):
        new_version = 'v' + new_version
            
    print(f"Đang cập nhật lên phiên bản: {new_version}")
    
    # 3. Cập nhật version.json
    data["version"] = new_version
    changes = input("Nhập nội dung thay đổi cho bản cập nhật này (Enter để bỏ qua): ").strip()
    if changes:
        data["changes"] = changes
        
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    # 4. Cập nhật CURRENT_VERSION trong src/main.py và updater.py
    for py_file in [MAIN_FILE, os.path.join('src', 'updater.py')]:
        with open(py_file, 'r', encoding='utf-8') as f:
            code = f.read()
        new_code = re.sub(
            r'CURRENT_VERSION\s*=\s*["\'][^"\']*["\']', 
            f'CURRENT_VERSION = "{new_version}"', 
            code
        )
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(new_code)
            
    # Xoá cache cũ để tránh lỗi PyInstaller base_library.zip
    print("Đang dọn dẹp thư mục build/dist cũ...")
    for path in ['build', 'dist']:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)

    # 5. Build file .exe
    print("Đang build file exe bằng PyInstaller...")
    try:
        import PyInstaller
    except ImportError:
        print("Chưa cài đặt PyInstaller. Đang cài đặt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",           
        "--onefile",             
        "--name", "magAutoTone", 
        "--collect-data", "tkinterdnd2", 
        "--collect-data", "customtkinter",
        "--collect-data", "librosa",
        "--hidden-import", "tkinterdnd2",
        "--hidden-import", "librosa",
        "--hidden-import", "demucs",
        "--hidden-import", "torch",
        "--hidden-import", "torchaudio",
        "--clean",               
        MAIN_FILE
    ]
    
    print(f"Running command: {' '.join(command)}")
    print("Please wait, packaging AI libraries (Torch/Demucs) can take several minutes...")
    
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
        return

    # 6. Git Push
    print("\nBạn có muốn đẩy mã nguồn lên GitHub không? (y/n): ", end="")
    choice = input().strip().lower()
    if choice == 'y':
        try:
            print("Đang commit và đẩy lên GitHub...")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Update to version {new_version}\n\n{changes}"], check=True)
            subprocess.run(["git", "push"], check=True)
            print(f"XONG! Đã đẩy mã nguồn lên nhánh main.")
            
            print("\n" + "!"*50)
            print("LƯU Ý CUỐI CÙNG:")
            print(f"Hãy vào trang GitHub của bạn, tạo một Release mới với tag là '{new_version}'")
            print("Và tải file 'dist/magAutoTone.zip' lên phần Assets của Release đó để người dùng nhận được cập nhật nhé!")
            print("!"*50)
            
        except subprocess.CalledProcessError as e:
            print(f"Lỗi Git. Quá trình đẩy lên GitHub thất bại.")
    else:
        print(f"XONG! Đã hoàn tất đóng gói phiên bản {new_version}")

if __name__ == "__main__":
    main()
