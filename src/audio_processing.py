import os
import librosa
import numpy as np
import tempfile
from moviepy import VideoFileClip


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
            
            import scipy.signal
            
            # Trích xuất đường bao nhịp điệu với độ phân giải cao (hop_length=128)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=128)
            
            # Phân tích biểu đồ nhịp độ (tempogram) để tìm BPM chính xác tuyệt đối
            tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr, hop_length=128)
            mean_tempogram = np.mean(tempogram, axis=1)
            bpms = librosa.tempo_frequencies(tempogram.shape[0], sr=sr, hop_length=128)
            
            # Áp dụng bộ lọc Log-Normal Prior (trung tâm 120 BPM) để khử nhiễu octave (nhân đôi/chia đôi nhịp)
            safe_bpms = np.clip(bpms, 1e-5, None)
            prior = np.exp(-0.5 * ((np.log2(safe_bpms) - np.log2(120.0)) / 1.0)**2)
            weighted_tempogram = mean_tempogram * prior
            
            # Tìm các đỉnh (peaks)
            peaks, _ = scipy.signal.find_peaks(weighted_tempogram)
            if len(peaks) > 0:
                best_peak = peaks[np.argmax(weighted_tempogram[peaks])]
                
                # Nội suy Parabol (Parabolic Interpolation) để có số thập phân cực kỳ chính xác
                alpha = weighted_tempogram[best_peak - 1] if best_peak > 0 else weighted_tempogram[best_peak]
                beta = weighted_tempogram[best_peak]
                gamma = weighted_tempogram[best_peak + 1] if best_peak < len(weighted_tempogram) - 1 else weighted_tempogram[best_peak]
                
                if alpha == beta and beta == gamma:
                    exact_bin = float(best_peak)
                else:
                    p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
                    exact_bin = best_peak + p
                    
                bpm = np.interp(exact_bin, np.arange(len(bpms)), bpms)
            else:
                bpm = 120.0

            if progress_callback:
                progress_callback("Đang tính toán Key (Tông nhạc)...")
            
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            key, scale = self._estimate_key(chroma)
            musical_key = f"{key} {scale}"

            # Lấy mảng min/max envelope của waveform để vẽ trên UI
            envelope = self.get_waveform_envelope(num_points=4000)
            
            # Gửi tín hiệu hoàn tất
            if progress_callback:
                progress_callback("Hoàn tất phân tích.")

            if progress_callback:
                progress_callback("Đang tạo tệp phát lại đồng bộ...")
            import soundfile as sf
            import uuid
            playback_path = os.path.join(tempfile.gettempdir(), f"playback_temp_{uuid.uuid4().hex[:8]}.wav")
            sf.write(playback_path, y, sr)

            return {
                "bpm": round(float(bpm), 2),
                "key": musical_key,
                "duration": duration_str,
                "duration_secs": float(duration_secs),
                "waveform_envelope": envelope,
                "playback_file": playback_path
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

    def get_waveform_envelope(self, num_points=4000) -> list:
        """
        Trích xuất đường bao (envelope) của sóng âm dưới dạng tập hợp các điểm (min, max)
        để vẽ nhanh trên Canvas.
        """
        if self.last_y is None or len(self.last_y) == 0:
            return []
            
        y = self.last_y
        
        # Nếu audio ngắn hơn số điểm yêu cầu, ta vẽ luôn y
        if len(y) <= num_points:
            return [(val, val) for val in y]
            
        # Chia mảng thành các chunk đều nhau
        chunk_size = len(y) // num_points
        
        # Để nhanh nhất, reshape mảng thành 2D và lấy min, max theo trục 1
        # Phải cắt bớt phần thừa cuối cùng để chia hết cho chunk_size
        truncated_length = chunk_size * num_points
        y_truncated = y[:truncated_length]
        y_reshaped = y_truncated.reshape((num_points, chunk_size))
        
        mins = np.min(y_reshaped, axis=1)
        maxs = np.max(y_reshaped, axis=1)
        
        # Normalize để max amplitude là 1.0
        max_abs = max(abs(np.min(mins)), abs(np.max(maxs)))
        if max_abs > 0:
            mins = mins / max_abs
            maxs = maxs / max_abs
            
        return list(zip(mins.tolist(), maxs.tolist()))
