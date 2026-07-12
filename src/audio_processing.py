import os
import librosa
import numpy as np
import tempfile
from moviepy import VideoFileClip
import matplotlib
matplotlib.use('Agg') # Backend cho headless plotting
import matplotlib.pyplot as plt

class AudioAnalyzer:
    def __init__(self):
        # Các khoá (Key) theo chuẩn Krumhansl-Schmuckler
        self.key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.last_y = None
        self.last_sr = None

    def is_video(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv']

    def extract_audio(self, video_path: str) -> str:
        """
        Trích xuất âm thanh từ file video và lưu ra file tạm.
        """
        temp_audio_path = os.path.join(tempfile.gettempdir(), "extracted_audio.wav")
        try:
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(temp_audio_path, logger=None)
            video.close()
            return temp_audio_path
        except Exception as e:
            raise Exception(f"Lỗi khi trích xuất âm thanh từ video: {e}")

    def analyze(self, file_path: str, progress_callback=None, color="#1f6aa5"):
        """
        Phân tích file âm thanh, trả về BPM, Key và đường dẫn ảnh Waveform.
        """
        # Nếu là video, trích xuất audio trước
        if self.is_video(file_path):
            if progress_callback:
                progress_callback("Đang trích xuất âm thanh từ video...")
            audio_path = self.extract_audio(file_path)
        else:
            audio_path = file_path

        if progress_callback:
            progress_callback("Đang tải dữ liệu âm thanh (librosa)...")

        try:
            # Tải audio
            y, sr = librosa.load(audio_path, sr=22050)
            self.last_y = y
            self.last_sr = sr
            
            # Tính thời lượng
            duration_secs = len(y) / sr
            minutes = int(duration_secs // 60)
            seconds = int(duration_secs % 60)
            duration_str = f"{minutes}:{seconds:02d}"
            
            if progress_callback:
                progress_callback("Đang tính toán BPM (Nhịp điệu)...")
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Tempo có thể là mảng, lấy giá trị đầu
            bpm = tempo[0] if isinstance(tempo, np.ndarray) else tempo

            if progress_callback:
                progress_callback("Đang tính toán Key (Tông nhạc)...")
            
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key, scale = self._estimate_key(chroma)
            musical_key = f"{key} {scale}"

            if progress_callback:
                progress_callback("Đang tạo biểu đồ sóng âm (Waveform)...")
            waveform_img = self.generate_waveform_image(color)

            return {
                "bpm": round(float(bpm), 2),
                "key": musical_key,
                "duration": duration_str,
                "waveform": waveform_img
            }

        except Exception as e:
            raise Exception(f"Lỗi phân tích âm thanh: {str(e)}")

    def _estimate_key(self, chroma):
        """
        Dự đoán key và scale từ chromagram.
        """
        chroma_vals = np.sum(chroma, axis=1)
        # Krumhansl-Schmuckler profiles
        maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        min_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        maj_corrs = [np.corrcoef(chroma_vals, np.roll(maj_profile, i))[0, 1] for i in range(12)]
        min_corrs = [np.corrcoef(chroma_vals, np.roll(min_profile, i))[0, 1] for i in range(12)]
        
        maj_max = max(maj_corrs)
        min_max = max(min_corrs)
        
        if maj_max > min_max:
            key_idx = maj_corrs.index(maj_max)
            scale = "Major"
        else:
            key_idx = min_corrs.index(min_max)
            scale = "Minor"
            
        return self.key_names[key_idx], scale

    def generate_waveform_image(self, color="#1f6aa5") -> str:
        """
        Vẽ waveform từ dữ liệu đã cache và lưu vào file ảnh tạm thời, trả về đường dẫn.
        """
        if self.last_y is None or self.last_sr is None:
            raise Exception("Chưa có dữ liệu âm thanh để vẽ.")
            
        plt.figure(figsize=(8, 2.5))
        plt.plot(np.linspace(0, len(self.last_y)/self.last_sr, num=len(self.last_y)), self.last_y, color=color, linewidth=1.2, alpha=0.9)
        plt.axis("off")
        plt.tight_layout(pad=0)
        
        temp_img = os.path.join(tempfile.gettempdir(), "waveform.png")
        plt.savefig(temp_img, transparent=True)
        plt.close()
        
        return temp_img
