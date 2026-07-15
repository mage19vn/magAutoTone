import sys
import os

main_path = r'd:\Project_Tool\AutoTone\src\main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'from locales import TRANSLATIONS' not in content:
    content = content.replace('import json', 'import json\nfrom locales import TRANSLATIONS')
    
# Implement self._t
t_func = '''
    def _t(self, key):
        lang = getattr(self, "language", "vi")
        return TRANSLATIONS.get(lang, TRANSLATIONS["vi"]).get(key, key)
        
    def _load_config(self):'''
if 'def _t(self, key):' not in content:
    content = content.replace('    def _load_config(self):', t_func, 1)

translations = {
    '"hoặc click để duyệt  ·  MP3, WAV, FLAC, Video"': 'self._t("drop_hint")',
    '"Kéo thả file âm thanh vào đây"': 'self._t("drop_wait")',
    'f"Đang đói! Đưa file đây{dots}"': 'f"{self._t(\'drop_hungry\')}{dots}"',
    '"🎵 Định dạng"': 'self._t("format")',
    '"🎛️ Chế độ"': 'self._t("mode")',
    '"Nhạc & Vocal (2)"': 'self._t("mode_2")',
    '"Đầy đủ (4)"': 'self._t("mode_4")',
    '"🎨 Màu chủ đạo"': 'self._t("color")',
    '"🌈 Khác"': 'self._t("color_custom")',
    '"👤 Người dùng"': 'self._t("user")',
    '"Đổi tên"': 'self._t("rename")',
    '"⚙️ Tùy chỉnh nâng cao"': 'self._t("advanced")',
    '"Bitrate MP3"': 'self._t("bitrate")',
    '"🚀 Tăng tốc GPU (CUDA)"': 'self._t("gpu")',
    '"📁 Tự tạo thư mục theo tên bài hát"': 'self._t("auto_subfolder")',
    '"📁 Thư mục xuất tệp"': 'self._t("output_dir")',
    '"Thay đổi"': 'self._t("btn_browse")',
    '"Reset"': 'self._t("btn_reset")',
    '"Mặc định: Cùng thư mục file gốc"': 'self._t("default_dir")',
    '"🎧 Tách Nhạc cụ & Vocal"': 'self._t("separate_btn")',
    '"▶ Nghe thử"': 'self._t("play_btn")',
    '"⏸ Dừng"': 'self._t("stop_btn")',
    '"📂 Mở thư mục"': 'self._t("open_folder")',
    '"🔄 Chọn file khác"': 'self._t("choose_other")',
    '"🎛️ Trộn âm"': 'self._t("mix_btn")',
    '"🎛️ Bộ trộn Âm lượng"': 'self._t("mixer_title")',
    '"Nhấn ▶ để nghe riêng từng stem · Kéo thanh trượt để chỉnh âm lượng"': 'self._t("mixer_desc")',
    '"💾 Trộn & Lưu"': 'self._t("mix_save")',
    '"Lỗi"': 'self._t("msg_error")',
    '"Cảnh báo"': 'self._t("msg_warn")',
    '"Thông báo"': 'self._t("msg_info")',
    '"Vui lòng chọn một bài hát trước!"': 'self._t("req_file")',
    '"Đã trả về thiết lập mặc định (Lưu cùng thư mục gốc)."': 'self._t("reset_done")',
    '"Nhập tên mới và mã Key để xác thực"': 'self._t("rename_prompt")',
    '"Tên mới của bạn..."': 'self._t("new_name")',
    '"Mã Key bảo mật"': 'self._t("security_key")',
    '"Xác nhận"': 'self._t("confirm")',
    '"Hủy"': 'self._t("cancel")',
    '"Tên không được để trống!"': 'self._t("name_empty")',
    '"Mã Key không chính xác!"': 'self._t("wrong_key")',
    '"Cập nhật"': 'self._t("update_title")',
    '"Kiểm tra bản cập nhật"': 'self._t("check_update")',
    '"Bạn đang sử dụng phiên bản mới nhất!"': 'self._t("up_to_date")',
    '"THỜI LƯỢNG"': 'self._t("duration")',
    '"Đang phân tích BPM & Key..."': 'self._t("analyzing")',
    '"Đang trích xuất âm thanh từ video..."': 'self._t("extracting")',
    '"Đang tải dữ liệu âm thanh (librosa)..."': 'self._t("loading_data")',
    '"Đang vẽ Waveform..."': 'self._t("drawing")',
    '"⏳ Đang tách..."': 'self._t("separating")',
    '"⏳ Đang trộn..."': 'self._t("mixing")',
    '"⏳ Đang tạo..."': 'self._t("saving")'
}

for k, v in translations.items():
    content = content.replace(k, v)
    
with open(main_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done replacement')
