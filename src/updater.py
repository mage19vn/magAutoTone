import os
import sys
import json
import urllib.request
import subprocess
import zipfile

CURRENT_VERSION = "v1.0.2"
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
            callback("Đang thiết lập quá trình cài đặt...")

        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        
        if not current_exe or not current_exe.endswith('.exe'):
            if callback: callback("Bạn đang chạy từ Source Code. Bỏ qua tự động cập nhật.")
            return

        exe_name = os.path.basename(current_exe)
        
        bat_path = "update_script.bat"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
:: Đợi ứng dụng hiện tại đóng lại hoàn toàn
timeout /t 3 /nobreak >nul

:: Đảm bảo ứng dụng cũ đã tắt
taskkill /f /im "{exe_name}" >nul 2>&1

:: Xóa file exe cũ
del "{exe_name}"

:: Dùng PowerShell để giải nén file ZIP
powershell Expand-Archive -Path "{temp_zip}" -DestinationPath "." -Force

:: Nếu file trong ZIP có tên là magAutoTone.exe nhưng người dùng đã đổi tên file đang chạy, ta sẽ đổi tên lại cho khớp
if not "{exe_name}"=="magAutoTone.exe" (
    if exist "magAutoTone.exe" (
        ren "magAutoTone.exe" "{exe_name}"
    )
)

:: Xóa file ZIP tải về
del "{temp_zip}"

:: Mở ứng dụng mới
start "" "{exe_name}"

:: Tự xóa file bat này
del "%~f0"
""")
        
        subprocess.Popen([bat_path], shell=True)
        sys.exit(0)
    except Exception as e:
        print("Lỗi khi tải bản cập nhật:", e)
        if callback:
            callback(f"Lỗi tải cập nhật: {e}")
