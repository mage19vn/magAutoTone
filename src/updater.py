import os
import sys
import json
import urllib.request
import subprocess

CURRENT_VERSION = "v1.0.0"
REPO_URL = "https://api.github.com/repos/mage19vn/magAutoTone/releases/latest"

def check_for_updates():
    try:
        req = urllib.request.Request(REPO_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name")
            
            if latest_version and latest_version != CURRENT_VERSION:
                assets = data.get("assets", [])
                if assets:
                    download_url = assets[0]["browser_download_url"]
                    return latest_version, download_url
    except Exception as e:
        print("Update check error:", e)
    return None, None

def download_and_install_update(download_url, callback=None):
    try:
        temp_exe = "magAutoTone_update.exe"
        
        if callback:
            callback("Đang tải bản cập nhật...")
            
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_exe, 'wb') as out_file:
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
            callback("Đang cài đặt...")

        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        
        if not current_exe or not current_exe.endswith('.exe'):
            if callback: callback("Bạn đang chạy từ Source Code. Bỏ qua tự động cập nhật.")
            return

        exe_name = os.path.basename(current_exe)
        
        bat_path = "update_script.bat"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 /nobreak >nul
del "{exe_name}"
ren "{temp_exe}" "{exe_name}"
start "" "{exe_name}"
del "%~f0"
""")
        
        subprocess.Popen([bat_path], shell=True)
        sys.exit(0)
    except Exception as e:
        print("Lỗi khi tải bản cập nhật:", e)
        if callback:
            callback(f"Lỗi tải cập nhật: {e}")
