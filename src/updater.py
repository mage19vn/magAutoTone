import os
import sys
import json
import urllib.request
import subprocess
import zipfile

CURRENT_VERSION = "v1.0.13"
REPO_URL = "https://api.github.com/repos/mage19vn/magAutoTone/releases/latest"

def check_for_updates():
    try:
        req = urllib.request.Request(REPO_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name")
            
            if latest_version and latest_version.lstrip('v') != CURRENT_VERSION.lstrip('v'):
                assets = data.get("assets", [])
                if assets:
                    download_url = assets[0]["browser_download_url"]
                    return latest_version, download_url
    except Exception as e:
        print("Update check error:", e)
    return None, None

def download_and_install_update(download_url, callback=None):
    try:
        temp_zip = "magAutoTone_update.zip"
        
        if callback:
            callback("Đang tải bản cập nhật...")
            
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_zip, 'wb') as out_file:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if callback and total_size > 0:
                    callback(f"Đang tải... {int((downloaded / total_size) * 100)}%")

        if callback:
            callback("Đang giải nén...")

        temp_dir = "update_temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Dùng Python giải nén vào thư mục tạm thay vì file zip để an toàn
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Kiểm tra nếu trong zip chỉ có 1 thư mục gốc (thường thấy khi tải từ Github)
        extracted_items = os.listdir(temp_dir)
        source_dir = temp_dir
        if len(extracted_items) == 1:
            first_item = os.path.join(temp_dir, extracted_items[0])
            if os.path.isdir(first_item):
                source_dir = first_item
                
        if callback:
            callback("Đang cài đặt...")

        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        
        if not current_exe or not current_exe.endswith('.exe'):
            if callback: callback("Bạn đang chạy từ Source Code. Bỏ qua tự động cập nhật.")
            return

        exe_name = os.path.basename(current_exe)
        
        bat_path = "update_script.bat"
        bat_content = f"""@echo off
set _MEIPASS2=
set _MEIPASS=
echo Dang cho ung dung cu thoat hoan toan...
:waitloop
timeout /t 1 /nobreak >nul
del "{exe_name}" 2>nul
if exist "{exe_name}" goto waitloop

xcopy /s /y /e /q "{source_dir}\\*" .

if not "{exe_name}"=="magAutoTone.exe" (
    if exist "magAutoTone.exe" (
        ren "magAutoTone.exe" "{exe_name}"
    )
)

rd /s /q "{temp_dir}"
del "{temp_zip}"
start "" "{exe_name}" --updated
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        # Xoá biến môi trường PyInstaller để tránh lỗi đụng độ cache khi restart
        env = os.environ.copy()
        env.pop('_MEIPASS2', None)
        env.pop('_MEIPASS', None)
        
        subprocess.Popen([bat_path], shell=True, env=env)
        
        # Thoát ứng dụng
        os._exit(0)
    except Exception as e:
        print("Lỗi khi tải bản cập nhật:", e)
        if callback:
            callback(f"Lỗi tải cập nhật: {e}")
