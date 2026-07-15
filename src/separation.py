import os
import sys
import subprocess
import threading

class StemSeparator:
    def __init__(self):
        self.process = None
        self.is_running = False

    def separate(self, file_path: str, output_dir: str, output_format: str = "wav", two_stems: bool = False, mp3_bitrate: int = 320, use_gpu: bool = False, progress_callback=None, done_callback=None, error_callback=None):
        """
        Chạy Demucs trên một luồng riêng bằng subprocess để tách stem.
        """
        def run():
            self.is_running = True
            try:
                if progress_callback:
                    progress_callback("Đang khởi tạo Demucs (có thể mất thời gian load model)...")
                
                # Gọi lệnh demucs thông qua python -m demucs
                # htdemucs là model mặc định có tốc độ và chất lượng tốt
                
                # Tối ưu tốc độ: sử dụng multiprocessing của CPU
                import multiprocessing
                cpu_count = max(1, multiprocessing.cpu_count() - 2) # Giữ lại 2 core cho hệ thống
                
                cmd = [
                    sys.executable, "-m", "demucs.separate",
                    "-n", "htdemucs",
                    "-j", str(cpu_count), # Tối ưu hóa đa luồng (multi-core)
                    "--int24", # Tối ưu hóa I/O, file nhẹ hơn so với float32
                    "-o", output_dir,
                ]
                
                # GPU Acceleration
                if use_gpu:
                    cmd.extend(["--device", "cuda"])
                
                if two_stems:
                    cmd.extend(["--two-stems", "vocals"])
                
                if output_format.lower() == "mp3":
                    cmd.append("--mp3")
                    cmd.extend(["--mp3-bitrate", str(mp3_bitrate)])
                elif output_format.lower() == "flac":
                    cmd.append("--flac")
                    
                cmd.append(file_path)

                # Fix UnicodeEncodeError: Force child python process to use utf-8 for stdout
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"

                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )

                last_logs = []
                for line in self.process.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    
                    last_logs.append(line)
                    if len(last_logs) > 5:
                        last_logs.pop(0)
                    
                    if progress_callback:
                        # Phân tích sơ bộ stdout của demucs để báo tiến độ
                        if "Separated tracks" in line:
                            progress_callback("Sắp hoàn thành...")
                        elif "%" in line:
                            progress_callback(f"Đang xử lý: {line}")
                        elif "Downloading" in line:
                            progress_callback("Đang tải AI Model (lần đầu tiên)...")
                
                self.process.wait()
                
                if self.process.returncode == 0:
                    if done_callback:
                        done_callback(output_dir)
                else:
                    if error_callback:
                        err_msg = "\n".join(last_logs) if last_logs else f"Mã lỗi: {self.process.returncode}"
                        error_callback(f"Lỗi khi chạy Demucs:\n{err_msg}")

            except Exception as e:
                if error_callback:
                    error_callback(str(e))
            finally:
                self.is_running = False
                self.process = None

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def cancel(self):
        """
        Huỷ quá trình tách stem.
        """
        if self.is_running and self.process:
            self.process.terminate()
            self.is_running = False
