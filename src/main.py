import os
import sys
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, Menu, colorchooser
import customtkinter as ctk
from PIL import Image

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    messagebox.showerror("Thiếu thư viện", "Vui lòng chạy: pip install tkinterdnd2")
    sys.exit(1)

from audio_processing import AudioAnalyzer
from separation import StemSeparator
from utils import get_resource_path
from updater import check_for_updates, download_and_install_update, CURRENT_VERSION

# Cấu hình giao diện Minimalist
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Đảm bảo Windows hiển thị icon ở Taskbar thay vì icon Python mặc định
if os.name == 'nt':
    import ctypes
    try:
        myappid = f"mage19vn.magAutoTone.{CURRENT_VERSION}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class ToolTip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.enter, add="+")
        self.widget.bind("<Leave>", self.leave, add="+")

    def enter(self, event=None):
        self.unschedule()
        self.id = self.widget.after(400, self.showtip)

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        text = self.text_func() if callable(self.text_func) else self.text_func
        if not text or text == "--" or "..." in text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_attributes("-topmost", True)
        tw.wm_geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(tw, fg_color="#2b2b2b", corner_radius=6, border_width=1, border_color="#555555")
        frame.pack(fill="both", expand=True)
        
        label = ctk.CTkLabel(frame, text=text, text_color="#eeeeee", font=ctk.CTkFont(size=12), justify="left")
        label.pack(padx=10, pady=6)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class AutoToneApp(Tk):
    def __init__(self):
        super().__init__()

        self.title(f"magAutoTone {CURRENT_VERSION}")
        self.geometry("580x660")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(get_resource_path("assets/icon.ico"))
        except Exception:
            pass

        self.analyzer = AudioAnalyzer()
        self.separator = StemSeparator()
        self.selected_file = None
        self.current_theme_color = "#1f6aa5" # Default blue
        self.default_output_dir = "" # Mặc định rỗng -> lưu cùng file gốc
        self.output_format = "WAV" # Định dạng mặc định
        self.two_stems_mode = False # Mặc định tách 4 stems
        self.username = "User_pussyGUY" # Tên mặc định
        
        self.config_path = get_resource_path("config.json")
        self.load_config()

        self.build_ui()
        
        # Tự động kiểm tra bản cập nhật
        threading.Thread(target=self.bg_check_update, daemon=True).start()

    def bg_check_update(self):
        latest_version, download_url = check_for_updates()
        if latest_version and download_url:
            self.after(3000, lambda: self.prompt_update(latest_version, download_url))

    def prompt_update(self, version, download_url):
        ans = messagebox.askyesno("Bản cập nhật mới!", f"Đã có phiên bản {version}.\nBạn có muốn tải và cập nhật ngay không?")
        if ans:
            self.set_status(f"Đang chuẩn bị cập nhật lên {version}...", True)
            threading.Thread(target=download_and_install_update, args=(download_url, self.update_callback), daemon=True).start()

    def manual_check_update(self):
        self.set_status("Đang kiểm tra cập nhật...", True)
        def _check():
            latest_version, download_url = check_for_updates()
            self.after(0, lambda: self.set_status("", False))
            if latest_version and download_url:
                self.after(0, lambda: self.prompt_update(latest_version, download_url))
            else:
                self.after(0, lambda: messagebox.showinfo("Cập nhật", "Bạn đang sử dụng phiên bản mới nhất!"))
        threading.Thread(target=_check, daemon=True).start()

    def update_callback(self, msg):
        self.after(0, lambda: self.set_status(msg, "Đang tải" in msg or "cài đặt" in msg))
        if "Lỗi" in msg:
            self.after(0, lambda: messagebox.showerror("Lỗi Cập nhật", msg))

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.current_theme_color = config.get("current_theme_color", self.current_theme_color)
                    self.default_output_dir = config.get("default_output_dir", self.default_output_dir)
                    self.output_format = config.get("output_format", self.output_format)
                    self.two_stems_mode = config.get("two_stems_mode", self.two_stems_mode)
                    self.username = config.get("username", self.username)
            except Exception as e:
                print(f"Lỗi đọc config: {e}")

    def save_config(self):
        config = {
            "current_theme_color": self.current_theme_color,
            "default_output_dir": self.default_output_dir,
            "output_format": self.output_format,
            "two_stems_mode": self.two_stems_mode,
            "username": self.username
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Lỗi lưu config: {e}")

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        # Không dùng weight cho bất kỳ row nào — layout khóa chặt

        # ------------------- HEADER -------------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(15, 8), sticky="ew", padx=25)
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title with subtle accent dot
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")
        
        accent_dot = ctk.CTkLabel(title_frame, text="●", font=ctk.CTkFont(size=14), text_color=self.current_theme_color)
        accent_dot.pack(side="left", padx=(0, 8))
        self.accent_dot = accent_dot
        
        title_label = ctk.CTkLabel(title_frame, text="MagAutoTone", font=ctk.CTkFont(family="Helvetica", size=28, weight="bold"))
        title_label.pack(side="left")
        
        version_label = ctk.CTkLabel(title_frame, text=f"  {CURRENT_VERSION}", font=ctk.CTkFont(size=11), text_color="#666666")
        version_label.pack(side="left", pady=(5, 0))
        
        # Header action frame for buttons
        header_actions = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_actions.grid(row=0, column=1, sticky="e")
        
        self.lbl_username = ctk.CTkLabel(header_actions, text=self.username, font=ctk.CTkFont(size=13, weight="bold"), text_color="#777777")
        self.lbl_username.grid(row=0, column=0, padx=(0, 12))
        
        btn_help = ctk.CTkButton(header_actions, text="❓", width=36, height=36, corner_radius=18,
                                 fg_color="#2a2a2a", hover_color="#3a3a3a", font=ctk.CTkFont(size=18),
                                 command=self.open_help_window)
        btn_help.grid(row=0, column=1, padx=(0, 6))

        btn_settings = ctk.CTkButton(header_actions, text="⚙️", width=36, height=36, corner_radius=18,
                                   fg_color="#2a2a2a", hover_color="#3a3a3a", font=ctk.CTkFont(size=18),
                                   command=self.open_settings)
        btn_settings.grid(row=0, column=2, padx=0)

        # Separator line
        sep = ctk.CTkFrame(self, height=1, fg_color="#2a2a2a")
        sep.grid(row=1, column=0, sticky="ew", padx=15)

        # ------------------- DYNAMIC DROPZONE -------------------
        self.dropzone = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1e1e", border_width=2, border_color="#333333")
        # Trạng thái ban đầu: to, ở giữa, chiếm hết phần còn lại
        self.dropzone.grid(row=2, column=0, rowspan=4, padx=25, pady=(15, 20), sticky="nsew")
        self.grid_rowconfigure(4, weight=1) # Chỉ expand khi dropzone đang hiện to
        self.dropzone.grid_rowconfigure(0, weight=1)
        self.dropzone.grid_columnconfigure(0, weight=1)
        
        # Inner content for dropzone
        dropzone_inner = ctk.CTkFrame(self.dropzone, fg_color="transparent")
        dropzone_inner.grid(row=0, column=0, padx=10, pady=10)
        
        self.drop_icon = ctk.CTkLabel(dropzone_inner, text="🎵", font=ctk.CTkFont(size=42))
        self.drop_icon.pack(pady=(0, 10))
        
        self.lbl_filename = ctk.CTkLabel(dropzone_inner, text="Kéo thả file âm thanh vào đây", font=ctk.CTkFont(size=16, weight="bold"), text_color="#cccccc")
        self.lbl_filename.pack(pady=(5, 5))
        
        self.lbl_hint = ctk.CTkLabel(dropzone_inner, text="hoặc click để duyệt  ·  MP3, WAV, FLAC, Video", font=ctk.CTkFont(size=12), text_color="#666666")
        self.lbl_hint.pack(pady=(4, 0))

        self.dropzone.drop_target_register(DND_FILES)
        self.dropzone.dnd_bind('<<Drop>>', self.on_drop)
        # Bind click cho toàn bộ các widget con trong dropzone
        for widget in [self.dropzone, self.lbl_filename, self.lbl_hint, self.drop_icon, dropzone_inner]:
            widget.bind("<Button-1>", lambda e: self.browse_file())
        
        # Hover effect cho dropzone
        def dz_enter(e):
            if not self.selected_file:
                self.dropzone.configure(border_color="#555555", fg_color="#232323")
        def dz_leave(e):
            if not self.selected_file:
                self.dropzone.configure(border_color="#333333", fg_color="#1e1e1e")
        for widget in [self.dropzone, self.lbl_filename, self.lbl_hint, self.drop_icon, dropzone_inner]:
            widget.bind("<Enter>", dz_enter)
            widget.bind("<Leave>", dz_leave)

        # ------------------- INFO CARDS (3 cột: BPM / Key / Duration) -------------------
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=3, column=0, padx=25, pady=(10, 0), sticky="ew")
        self.info_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.info_frame.grid_remove() # Ẩn đi ban đầu

        # BPM Card
        self.bpm_card = self._create_info_card(self.info_frame, 0, "♡", "BPM", "--")
        # Key Card
        self.key_card = self._create_info_card(self.info_frame, 1, "♪", "TONE", "--")
        # Duration Card
        self.duration_card = self._create_info_card(self.info_frame, 2, "◷", "THỜI LƯỢNG", "--")
        
        # ------------------- WAVEFORM -------------------
        self.waveform_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#2a2a2a", height=160)
        self.waveform_frame.grid(row=4, column=0, padx=25, pady=(8, 0), sticky="ew")
        self.waveform_frame.grid_propagate(False) # Khóa chặt chiều cao
        self.waveform_frame.grid_remove() # Ẩn đi ban đầu
        
        self.waveform_label = ctk.CTkLabel(self.waveform_frame, text="")
        self.waveform_label.pack(fill="both", expand=True, padx=10, pady=8)

        # ------------------- ACTION BUTTONS -------------------
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=25, pady=(10, 0), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_remove() # Ẩn đi ban đầu

        # Nút tách stem chính — to, gradient, nổi bật
        self.btn_separate = ctk.CTkButton(
            self.action_frame, 
            text="🎧  Tách Nhạc cụ & Vocal", 
            height=42, 
            corner_radius=10,
            fg_color=self.current_theme_color, 
            hover_color=self._darken_color(self.current_theme_color, 0.8),
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_separation
        )
        self.btn_separate.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        # Nút phụ — hàng dưới: Chọn file khác + Mở thư mục
        sub_btn_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        sub_btn_frame.grid(row=1, column=0, sticky="ew")
        sub_btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.btn_change_file = ctk.CTkButton(
            sub_btn_frame,
            text="🔄  Chọn file khác",
            height=34,
            corner_radius=8,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            border_width=1,
            border_color="#3a3a3a",
            font=ctk.CTkFont(size=12),
            command=self.browse_file
        )
        self.btn_change_file.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        
        self.btn_open_folder = ctk.CTkButton(
            sub_btn_frame,
            text="📂  Mở thư mục đã lưu",
            height=34,
            corner_radius=8,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            border_width=1,
            border_color="#3a3a3a",
            font=ctk.CTkFont(size=12),
            command=self._open_output_folder,
            state="disabled",
            text_color_disabled="#555555"
        )
        self.btn_open_folder.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        
        # ------------------- PROGRESS -------------------
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=6, column=0, padx=25, pady=(8, 15), sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="", text_color="#888888", font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.pack(pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=4, progress_color=self.current_theme_color, fg_color="#2a2a2a")
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        self.progress_frame.grid_remove()

        # Context Menu (vẫn giữ làm phương án phụ)
        self.context_menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", font=("Helvetica", 11), activebackground=self.current_theme_color)
        self.context_menu.add_command(label="🪄 Tách Stem (Demucs)", command=self.start_separation)

        # Track output dir for "Mở thư mục"
        self.last_output_dir = None

    def _create_info_card(self, parent, col, icon, title, value):
        """Tạo một info card nhỏ gọn."""
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e1e1e", border_width=1, border_color="#2a2a2a", height=78)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 3, 0 if col == 2 else 3))
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure((0, 1, 2), weight=1)
        
        lbl_icon = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=13), text_color="#555555")
        lbl_icon.grid(row=0, column=0, sticky="s", pady=(6, 0))
        
        lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=self.current_theme_color)
        lbl_value.grid(row=1, column=0)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color="#666666")
        lbl_title.grid(row=2, column=0, sticky="n", pady=(0, 6))
        
        # Hover effect
        def on_enter(e): card.configure(border_color="#444444")
        def on_leave(e): card.configure(border_color="#2a2a2a")
        for w in [card, lbl_icon, lbl_value, lbl_title]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            
        card.tooltip_text = ""
        ToolTip(card, lambda: card.tooltip_text)
        
        return {"card": card, "icon": lbl_icon, "value": lbl_value, "title": lbl_title}

    def _darken_color(self, hexcode, factor=0.8):
        """Làm tối một mã màu hex."""
        hexcode = hexcode.lstrip('#')
        if len(hexcode) != 6:
            return "#1a5080"
        r, g, b = int(hexcode[0:2], 16), int(hexcode[2:4], 16), int(hexcode[4:6], 16)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _open_output_folder(self):
        """Mở thư mục chứa output trong File Explorer."""
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            os.startfile(self.last_output_dir)
        else:
            out_dir = self.default_output_dir if self.default_output_dir else (os.path.dirname(self.selected_file) if self.selected_file else "")
            if out_dir and os.path.isdir(out_dir):
                os.startfile(out_dir)

    def open_help_window(self):
        help_win = ctk.CTkToplevel(self)
        help_win.title("Hướng dẫn sử dụng")
        help_win.geometry("500x520")
        help_win.attributes("-topmost", True)
        help_win.focus()
        
        # Căn giữa màn hình
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 520) // 2
        help_win.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = ctk.CTkFrame(help_win, fg_color="transparent")
        header_frame.pack(fill="x", pady=(25, 10))
        
        icon_lbl = ctk.CTkLabel(header_frame, text="📖", font=ctk.CTkFont(size=36))
        icon_lbl.pack()
        
        header = ctk.CTkLabel(header_frame, text="Hướng dẫn magAutoTone", 
                              font=ctk.CTkFont(size=22, weight="bold"), text_color=self.current_theme_color)
        header.pack(pady=(5, 0))
        
        # Tabview
        tabview = ctk.CTkTabview(help_win, corner_radius=12,
                                 segmented_button_selected_color=self.current_theme_color,
                                 segmented_button_selected_hover_color=self.current_theme_color)
        tabview.pack(padx=30, pady=(5, 25), fill="both", expand=True)
        
        tab_main = tabview.add("🚀 Cơ bản")
        tab_adv = tabview.add("⚙️ Nâng cao")
        tab_about = tabview.add("💡 Ứng dụng")
        
        # --- Tab Cơ bản ---
        steps = [
            ("1. Chọn file:", "Kéo thả hoặc Click để mở file nhạc."),
            ("2. Xem Info:", "AI tự phân tích Nhịp, Tone & Độ dài. Di chuột vào để xem nốt nhạc chi tiết."),
            ("3. Tách Stem:", "Nhấn '🎧 Tách Nhạc cụ' và đợi AI xử lý từ 1-3 phút."),
            ("4. Kết quả:", "Nhấn 'Mở thư mục' để lấy file thành phẩm.")
        ]
        tab_main.grid_columnconfigure(1, weight=1)
        for i, (title, desc) in enumerate(steps):
            ctk.CTkLabel(tab_main, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="nw", text_color=self.current_theme_color).grid(row=i, column=0, sticky="nw", padx=(15, 10), pady=10)
            ctk.CTkLabel(tab_main, text=desc, font=ctk.CTkFont(size=14), wraplength=250, justify="left", anchor="nw", text_color="#dddddd").grid(row=i, column=1, sticky="nw", padx=(0, 15), pady=10)
            
        # --- Tab Nâng cao ---
        advs = [
            ("📁 Thư mục:", "Thay đổi nơi lưu file kết quả mặc định."),
            ("🎵 Định dạng:", "Chọn WAV (Chất lượng gốc), FLAC (Lossless) hoặc MP3 (Nhẹ)."),
            ("🎛️ Chế độ:", "Chọn tách 2 phần (Nhạc & Vocal) hoặc 4 phần đầy đủ."),
            ("🎨 Giao diện:", "Tùy biến màu sắc toàn app theo sở thích.")
        ]
        tab_adv.grid_columnconfigure(1, weight=1)
        for i, (title, desc) in enumerate(advs):
            ctk.CTkLabel(tab_adv, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="nw", text_color="#ffffff").grid(row=i, column=0, sticky="nw", padx=(15, 10), pady=12)
            ctk.CTkLabel(tab_adv, text=desc, font=ctk.CTkFont(size=14), text_color="#cccccc", wraplength=250, justify="left", anchor="nw").grid(row=i, column=1, sticky="nw", padx=(0, 15), pady=12)
            
        # --- Tab Ứng dụng ---
        about_text = (
            "magAutoTone là trợ thủ đắc lực hỗ trợ tách Stem âm nhạc tự động sử dụng sức mạnh của Trí tuệ nhân tạo (AI).\n\n"
            "🎯 Nhận diện tự động Tempo & Tone nhạc.\n\n"
            "🎤 Tách lời hát và nhạc cụ cực chuẩn xác.\n\n"
            "🔒 Hỗ trợ đổi tên qua mã xác thực bảo mật."
        )
        
        textbox = ctk.CTkTextbox(tab_about, font=ctk.CTkFont(size=15), text_color="#cccccc", 
                                 fg_color="transparent", wrap="word")
        textbox.pack(fill="both", expand=True, padx=15, pady=20)
        textbox.insert("0.0", about_text)
        textbox.configure(state="disabled")
        
        # Đóng cửa sổ khi ấn Esc
        help_win.bind("<Escape>", lambda e: help_win.destroy())

    def open_settings(self):
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Cài đặt")
        settings_win.geometry("520x720")
        settings_win.resizable(False, False)
        settings_win.transient(self) # Gắn với cửa sổ chính
        
        settings_win.grid_columnconfigure(0, weight=1)
        
        # --- Header ---
        header_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 15))
        ctk.CTkLabel(header_frame, text="⚙️ Preferences", font=ctk.CTkFont(family="Helvetica", size=26, weight="bold")).pack(side="left")
        
        # --- Card 1: Thư mục lưu ---
        card1 = ctk.CTkFrame(settings_win, corner_radius=12, fg_color="#2b2b2b", border_width=1, border_color="#3b3b3b")
        card1.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
        card1.grid_columnconfigure(0, weight=1)
        
        lbl_dir_title = ctk.CTkLabel(card1, text="📁 Thư mục xuất tệp", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0")
        lbl_dir_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 5))
        
        self.lbl_outdir = ctk.CTkLabel(card1, 
                                       text=self.default_output_dir if self.default_output_dir else "Mặc định: Cùng thư mục file gốc", 
                                       height=38, fg_color="#1f1f1f", corner_radius=6, anchor="w", padx=15, text_color="gray")
        self.lbl_outdir.grid(row=1, column=0, sticky="ew", padx=(20, 10), pady=(0, 20))
            
        self.btn_browse_dir = ctk.CTkButton(card1, text="Thay đổi", width=80, height=38, corner_radius=19,
                                       fg_color=self.current_theme_color, hover_color=self.current_theme_color, 
                                       command=lambda: self._browse_setting_dir(settings_win))
        self.btn_browse_dir.grid(row=1, column=1, padx=(0, 5), pady=(0, 20))
        
        btn_reset_dir = ctk.CTkButton(card1, text="Reset", width=60, height=38, corner_radius=19,
                                      fg_color="transparent", border_width=1, border_color="#e83151", text_color="#e83151", 
                                      hover_color="#3d1f25", command=lambda: self._reset_setting_dir(settings_win))
        btn_reset_dir.grid(row=1, column=2, padx=(0, 20), pady=(0, 20))

        # --- Card 2: Định dạng & Chế độ ---
        card2 = ctk.CTkFrame(settings_win, corner_radius=12, fg_color="#2b2b2b", border_width=1, border_color="#3b3b3b")
        card2.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 15))
        card2.grid_columnconfigure((0, 1), weight=1)
        
        lbl_fmt_title = ctk.CTkLabel(card2, text="🎵 Định dạng & Chế độ", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0")
        lbl_fmt_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))
        
        format_var = ctk.StringVar(value=self.output_format)
        self.format_selector = ctk.CTkSegmentedButton(card2, values=["WAV", "MP3", "FLAC"], variable=format_var, corner_radius=19,
                                                 command=self._change_output_format, 
                                                 selected_color=self.current_theme_color, 
                                                 selected_hover_color=self.current_theme_color, height=38)
        self.format_selector.grid(row=1, column=0, sticky="ew", padx=(20, 10), pady=(0, 20))
        
        mode_var = ctk.StringVar(value="Nhạc & Vocal (2)" if self.two_stems_mode else "Đầy đủ (4)")
        self.mode_selector = ctk.CTkSegmentedButton(card2, values=["Nhạc & Vocal (2)", "Đầy đủ (4)"], variable=mode_var, corner_radius=19,
                                                 command=self._change_separation_mode, 
                                                 selected_color=self.current_theme_color, 
                                                 selected_hover_color=self.current_theme_color, height=38)
        self.mode_selector.grid(row=1, column=1, sticky="ew", padx=(10, 20), pady=(0, 20))

        # --- Card 3: Màu chủ đạo ---
        card3 = ctk.CTkFrame(settings_win, corner_radius=12, fg_color="#2b2b2b", border_width=1, border_color="#3b3b3b")
        card3.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 15))
        card3.grid_columnconfigure(0, weight=1)
        
        lbl_color_title = ctk.CTkLabel(card3, text="🎨 Màu chủ đạo", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0")
        lbl_color_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        color_frame = ctk.CTkFrame(card3, fg_color="transparent")
        color_frame.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        preset_colors = ["#1f6aa5", "#10B981", "#8B5CF6", "#F97316", "#EC4899"]
        
        for i, color in enumerate(preset_colors):
            btn = ctk.CTkButton(color_frame, text="", width=32, height=32, corner_radius=16,
                                fg_color=color, hover_color=color, cursor="hand2",
                                command=lambda c=color: self.change_theme_color(c))
            btn.grid(row=0, column=i, padx=(0, 10))
        
        self.btn_custom_color = ctk.CTkButton(color_frame, text="🌈 Khác", width=70, height=32, corner_radius=16,
                                              fg_color=self.current_theme_color, hover_color=self.current_theme_color, cursor="hand2",
                                              command=self.open_color_picker, font=ctk.CTkFont(size=12, weight="bold"))
        self.btn_custom_color.grid(row=0, column=len(preset_colors), padx=(5, 0))

        # --- Card 4: Thông tin người dùng ---
        card4 = ctk.CTkFrame(settings_win, corner_radius=12, fg_color="#2b2b2b", border_width=1, border_color="#3b3b3b")
        card4.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 15))
        card4.grid_columnconfigure((0, 1), weight=1)
        
        lbl_user_title = ctk.CTkLabel(card4, text="👤 Người dùng", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0")
        lbl_user_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))
        
        self.lbl_current_user = ctk.CTkLabel(card4, text=self.username, height=38, fg_color="#1f1f1f", corner_radius=6, anchor="w", padx=15, text_color="gray")
        self.lbl_current_user.grid(row=1, column=0, sticky="ew", padx=(20, 10), pady=(0, 20))
        
        self.btn_change_name = ctk.CTkButton(card4, text="Đổi tên", width=80, height=38, corner_radius=19,
                                             fg_color=self.current_theme_color, hover_color=self.current_theme_color,
                                             command=self.open_rename_popup)
        self.btn_change_name.grid(row=1, column=1, padx=(0, 20), pady=(0, 20))

        # --- Card 5: Cập nhật ---
        card5 = ctk.CTkFrame(settings_win, corner_radius=12, fg_color="#2b2b2b", border_width=1, border_color="#3b3b3b")
        card5.grid(row=5, column=0, sticky="ew", padx=30, pady=(0, 20))
        card5.grid_columnconfigure(0, weight=1)
        
        lbl_update_title = ctk.CTkLabel(card5, text="🔄 Cập nhật phần mềm", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0")
        lbl_update_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))
        
        lbl_version = ctk.CTkLabel(card5, text=f"Phiên bản hiện tại: {CURRENT_VERSION}", text_color="gray")
        lbl_version.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
        
        btn_update = ctk.CTkButton(card5, text="Kiểm tra bản cập nhật", width=140, height=32, corner_radius=16,
                                   fg_color="transparent", border_width=1, border_color="gray", hover_color="#333333",
                                   command=self.manual_check_update)
        btn_update.grid(row=1, column=1, sticky="e", padx=20, pady=(0, 15))

    def _change_output_format(self, choice):
        self.output_format = choice
        self.save_config()

    def _change_separation_mode(self, choice):
        self.two_stems_mode = choice == "Nhạc & Vocal (2)"
        self.save_config()

    def _browse_setting_dir(self, win):
        dirname = filedialog.askdirectory(title="Chọn thư mục mặc định", parent=win)
        if dirname:
            self.default_output_dir = dirname
            self.lbl_outdir.configure(text=dirname)
            self.save_config()
            
    def _reset_setting_dir(self, win):
        self.default_output_dir = ""
        self.lbl_outdir.configure(text="Mặc định: Cùng thư mục file gốc")
        self.save_config()
        messagebox.showinfo("Reset", "Đã trả về thiết lập mặc định (Lưu cùng thư mục gốc).", parent=win)

    def open_color_picker(self):
        picker = ctk.CTkToplevel(self)
        picker.title("Tùy chỉnh màu sắc")
        picker.geometry("400x530")
        picker.resizable(False, False)
        picker.transient(self)
        picker.grab_set()

        current_hex = self.current_theme_color.lstrip('#')
        if len(current_hex) != 6:
            current_hex = "1f6aa5"
        r, g, b = tuple(int(current_hex[i:i+2], 16) for i in (0, 2, 4))

        ctk.CTkLabel(picker, text="Tạo màu của riêng bạn", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))

        preview_frame = ctk.CTkFrame(picker, height=80, corner_radius=12, fg_color=self.current_theme_color)
        preview_frame.pack(fill="x", padx=30, pady=(0, 15))
        
        # --- SWATCHES ---
        swatch_frame = ctk.CTkFrame(picker, fg_color="transparent")
        swatch_frame.pack(fill="x", padx=30, pady=(0, 15))
        swatches = ["#EF4444", "#F97316", "#F59E0B", "#10B981", "#06B6D4", "#3B82F6", "#8B5CF6", "#EC4899"]
        
        swatch_frame.grid_columnconfigure(list(range(len(swatches))), weight=1)
        for i, sw in enumerate(swatches):
            btn = ctk.CTkButton(swatch_frame, text="", width=25, height=25, corner_radius=12, fg_color=sw, hover_color=sw, cursor="hand2",
                                command=lambda s=sw: set_hex_direct(s))
            btn.grid(row=0, column=i, padx=2)

        def set_hex_direct(val):
            hex_var.set(val)
            on_hex_type(None)

        hex_var = ctk.StringVar(value=self.current_theme_color)
        
        sliders_frame = ctk.CTkFrame(picker, fg_color="transparent")
        sliders_frame.pack(fill="both", expand=True, padx=30)
        sliders_frame.columnconfigure(2, weight=1)

        def update_preview(*args):
            try:
                nr, ng, nb = int(r_slider.get()), int(g_slider.get()), int(b_slider.get())
                new_hex = f"#{nr:02x}{ng:02x}{nb:02x}"
                r_val.configure(text=f"{nr:3d}")
                g_val.configure(text=f"{ng:3d}")
                b_val.configure(text=f"{nb:3d}")
                
                preview_frame.configure(fg_color=new_hex)
                if hex_var.get() != new_hex:
                    hex_var.set(new_hex)
                btn_confirm.configure(fg_color=new_hex, hover_color=new_hex)
            except:
                pass

        def adjust(color, delta):
            if color == 'r': r_slider.set(min(255, max(0, int(r_slider.get()) + delta)))
            elif color == 'g': g_slider.set(min(255, max(0, int(g_slider.get()) + delta)))
            elif color == 'b': b_slider.set(min(255, max(0, int(b_slider.get()) + delta)))
            update_preview()

        # RED
        ctk.CTkLabel(sliders_frame, text="R", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=10)
        ctk.CTkButton(sliders_frame, text="-", width=24, height=24, command=lambda: adjust('r', -1)).grid(row=0, column=1, padx=(10, 5))
        r_slider = ctk.CTkSlider(sliders_frame, from_=0, to=255, command=update_preview, button_color="#EF4444", progress_color="#EF4444")
        r_slider.set(r)
        r_slider.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkButton(sliders_frame, text="+", width=24, height=24, command=lambda: adjust('r', 1)).grid(row=0, column=3, padx=5)
        r_val = ctk.CTkLabel(sliders_frame, text=f"{r:3d}", font=ctk.CTkFont(family="Consolas", size=13))
        r_val.grid(row=0, column=4, padx=(5, 0))

        # GREEN
        ctk.CTkLabel(sliders_frame, text="G", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=10)
        ctk.CTkButton(sliders_frame, text="-", width=24, height=24, command=lambda: adjust('g', -1)).grid(row=1, column=1, padx=(10, 5))
        g_slider = ctk.CTkSlider(sliders_frame, from_=0, to=255, command=update_preview, button_color="#10B981", progress_color="#10B981")
        g_slider.set(g)
        g_slider.grid(row=1, column=2, padx=5, sticky="ew")
        ctk.CTkButton(sliders_frame, text="+", width=24, height=24, command=lambda: adjust('g', 1)).grid(row=1, column=3, padx=5)
        g_val = ctk.CTkLabel(sliders_frame, text=f"{g:3d}", font=ctk.CTkFont(family="Consolas", size=13))
        g_val.grid(row=1, column=4, padx=(5, 0))

        # BLUE
        ctk.CTkLabel(sliders_frame, text="B", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", pady=10)
        ctk.CTkButton(sliders_frame, text="-", width=24, height=24, command=lambda: adjust('b', -1)).grid(row=2, column=1, padx=(10, 5))
        b_slider = ctk.CTkSlider(sliders_frame, from_=0, to=255, command=update_preview, button_color="#3B82F6", progress_color="#3B82F6")
        b_slider.set(b)
        b_slider.grid(row=2, column=2, padx=5, sticky="ew")
        ctk.CTkButton(sliders_frame, text="+", width=24, height=24, command=lambda: adjust('b', 1)).grid(row=2, column=3, padx=5)
        b_val = ctk.CTkLabel(sliders_frame, text=f"{b:3d}", font=ctk.CTkFont(family="Consolas", size=13))
        b_val.grid(row=2, column=4, padx=(5, 0))
        
        hex_frame = ctk.CTkFrame(picker, fg_color="transparent")
        hex_frame.pack(fill="x", padx=30, pady=15)
        ctk.CTkLabel(hex_frame, text="HEX:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        hex_entry = ctk.CTkEntry(hex_frame, textvariable=hex_var, width=100)
        hex_entry.pack(side="left", padx=10)

        def copy_hex():
            picker.clipboard_clear()
            picker.clipboard_append(hex_var.get())
            picker.update()

        btn_copy = ctk.CTkButton(hex_frame, text="📋 Copy", width=60, height=28, fg_color="#444", hover_color="#555", command=copy_hex)
        btn_copy.pack(side="left", padx=5)
        
        def on_hex_type(event):
            val = hex_entry.get().strip()
            if len(val) == 7 and val.startswith('#'):
                try:
                    nr, ng, nb = int(val[1:3], 16), int(val[3:5], 16), int(val[5:7], 16)
                    r_slider.set(nr)
                    g_slider.set(ng)
                    b_slider.set(nb)
                    r_val.configure(text=f"{nr:3d}")
                    g_val.configure(text=f"{ng:3d}")
                    b_val.configure(text=f"{nb:3d}")
                    preview_frame.configure(fg_color=val)
                    btn_confirm.configure(fg_color=val, hover_color=val)
                except ValueError:
                    pass
                    
        hex_entry.bind("<KeyRelease>", on_hex_type)
        
        btn_frame = ctk.CTkFrame(picker, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(10, 25))
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Hủy", width=120, height=38, corner_radius=19,
                                   fg_color="transparent", border_width=1, border_color="gray", hover_color="#333333",
                                   command=picker.destroy)
        btn_cancel.pack(side="left", expand=True, padx=(0, 5))
        
        btn_confirm = ctk.CTkButton(btn_frame, text="Áp dụng", width=120, height=38, corner_radius=19,
                                    fg_color=self.current_theme_color, hover_color=self.current_theme_color,
                                    command=lambda: [self.change_theme_color(hex_var.get()), picker.destroy()])
        btn_confirm.pack(side="right", expand=True, padx=(5, 0))

    def open_rename_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Đổi tên người dùng")
        popup.geometry("380x350")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Cập nhật hồ sơ", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(25, 5))
        ctk.CTkLabel(popup, text="Nhập tên mới và mã Key để xác thực", font=ctk.CTkFont(size=13), text_color="gray").pack(pady=(0, 20))
        
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=40)
        
        entry_name = ctk.CTkEntry(frame, placeholder_text="Tên mới của bạn...", height=42, corner_radius=8, font=ctk.CTkFont(size=14))
        entry_name.pack(fill="x", pady=(0, 15))
        
        entry_key = ctk.CTkEntry(frame, placeholder_text="Mã Key bảo mật", show="*", height=42, corner_radius=8, font=ctk.CTkFont(size=14))
        entry_key.pack(fill="x", pady=(0, 25))
        
        def on_confirm():
            new_name = entry_name.get().strip()
            key = entry_key.get().strip()
            if not new_name:
                messagebox.showerror("Lỗi", "Tên không được để trống!", parent=popup)
                return
            if key != "120408190808":
                messagebox.showerror("Lỗi", "Mã Key không chính xác!", parent=popup)
                return
                
            self.username = new_name
            self.lbl_username.configure(text=new_name)
            if hasattr(self, 'lbl_current_user') and self.lbl_current_user.winfo_exists():
                self.lbl_current_user.configure(text=new_name)
            self.save_config()
            popup.destroy()
            messagebox.showinfo("Thành công", f"Đã đổi tên thành {new_name}!")
            
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(0, 30))
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Hủy", width=120, height=42, corner_radius=21,
                                   fg_color="transparent", border_width=1, border_color="gray", hover_color="#333333",
                                   command=popup.destroy, font=ctk.CTkFont(size=14, weight="bold"))
        btn_cancel.pack(side="left", expand=True, padx=(0, 5))
        
        btn_confirm = ctk.CTkButton(btn_frame, text="Xác nhận", width=120, height=42, corner_radius=21,
                                    fg_color=self.current_theme_color, hover_color=self.current_theme_color,
                                    command=on_confirm, font=ctk.CTkFont(size=14, weight="bold"))
        btn_confirm.pack(side="right", expand=True, padx=(5, 0))

    def change_theme_color(self, hexcode):
        self.current_theme_color = hexcode
        
        # Update info cards
        self.bpm_card["value"].configure(text_color=hexcode)
        self.key_card["value"].configure(text_color=hexcode)
        self.duration_card["value"].configure(text_color=hexcode)
        
        # Update accent dot, progress bar, context menu
        self.accent_dot.configure(text_color=hexcode)
        self.progress_bar.configure(progress_color=hexcode)
        self.context_menu.configure(activebackground=hexcode)
        
        # Update action buttons
        self.btn_separate.configure(fg_color=hexcode, hover_color=self._darken_color(hexcode, 0.8))
        
        self.save_config()

        try:
            if hasattr(self, 'btn_custom_color') and self.btn_custom_color.winfo_exists():
                self.btn_custom_color.configure(fg_color=hexcode, hover_color=hexcode)
            if hasattr(self, 'btn_browse_dir') and self.btn_browse_dir.winfo_exists():
                self.btn_browse_dir.configure(fg_color=hexcode, hover_color=hexcode)
            if hasattr(self, 'format_selector') and self.format_selector.winfo_exists():
                self.format_selector.configure(selected_color=hexcode, selected_hover_color=hexcode)
            if hasattr(self, 'btn_change_name') and self.btn_change_name.winfo_exists():
                self.btn_change_name.configure(fg_color=hexcode, hover_color=hexcode)
        except Exception:
            pass
        
        if self.selected_file:
            self.dropzone.configure(border_color=hexcode)
            if self.analyzer.last_y is not None:
                try:
                    wf_path = self.analyzer.generate_waveform_image(hexcode)
                    self._display_waveform(wf_path)
                except Exception as e:
                    print(f"Lỗi vẽ waveform: {e}")

    def on_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.process_new_file(file_path)

    def browse_file(self):
        filetypes = (
            ("Audio/Video Files", "*.mp3 *.wav *.flac *.mkv *.mp4 *.avi *.mov"),
            ("All Files", "*.*")
        )
        filename = filedialog.askopenfilename(title="Chọn file", filetypes=filetypes)
        if filename:
            self.process_new_file(filename)

    def process_new_file(self, file_path):
        if not os.path.exists(file_path):
            return
            
        self.selected_file = file_path
        filename = os.path.basename(file_path)
        
        # 1. Tắt weight expand (dropzone không còn chiếm hết)
        self.grid_rowconfigure(4, weight=0)
        
        # 2. Thu nhỏ Dropzone thành thanh ngang nhỏ ở trên
        self.dropzone.grid(row=2, column=0, rowspan=1, padx=25, pady=(15, 0), sticky="ew")
        self.dropzone.configure(border_color=self.current_theme_color, fg_color="#1e1e1e")
        # Để dropzone tự động co giãn theo nội dung bên trong, tránh cắt chữ
        if hasattr(self.dropzone, 'grid_propagate'):
            self.dropzone.grid_propagate(True)
        
        self.drop_icon.pack_forget()
        self.lbl_hint.pack_forget()
        self.lbl_filename.configure(text=f"🎵  {filename}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#eeeeee")
        self.lbl_filename.pack(pady=0) # Padding trong đã được xử lý bởi dropzone_inner
        
        # 3. Hiển thị info cards, waveform, và action buttons
        self.info_frame.grid()
        self.waveform_frame.grid()
        self.action_frame.grid()
        
        # 4. Reset "Mở thư mục" button khi chọn file mới
        self.btn_open_folder.configure(state="disabled", text_color_disabled="#555555")
        self.btn_separate.configure(state="normal")
        
        # Bắt đầu phân tích
        self.start_analysis()

    def set_status(self, message, is_loading=False):
        self.after(0, self._set_status_ui, message, is_loading)

    def _set_status_ui(self, message, is_loading):
        if message:
            # Cắt ngắn log nếu quá dài để không làm hụt giao diện chiều ngang
            display_msg = message if len(message) < 80 else message[:77] + "..."
            
            self.progress_frame.grid()
            self.status_label.configure(text=display_msg)
            if is_loading:
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
            else:
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(1)
        else:
            self.progress_frame.grid_remove()
            self.progress_bar.stop()

    def start_analysis(self):
        self.set_status("Đang phân tích BPM & Key...", is_loading=True)
        # Reset info cards to loading state
        self.bpm_card["value"].configure(text="...", text_color="#555555")
        self.key_card["value"].configure(text="...", text_color="#555555")
        self.duration_card["value"].configure(text="...", text_color="#555555")
        empty_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0,0,0,0)), size=(1, 1))
        self.waveform_label.configure(image=empty_img, text="")
        self.waveform_label.image = empty_img
        # Disable tách stem khi đang phân tích
        self.btn_separate.configure(state="disabled")
        
        thread = threading.Thread(target=self._analysis_worker, daemon=True)
        thread.start()

    def _analysis_worker(self):
        try:
            result = self.analyzer.analyze(self.selected_file, progress_callback=lambda m: self.set_status(m, True), color=self.current_theme_color)
            self.after(0, self._update_analysis_ui, result)
        except Exception as e:
            self.set_status(f"Lỗi: {e}", is_loading=False)
            self.after(0, lambda: self.btn_separate.configure(state="normal"))

    def _get_scale_notes(self, key, scale):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        try:
            start_idx = notes.index(key)
        except:
            return ""
        if scale == "Major":
            intervals = [0, 2, 4, 5, 7, 9, 11]
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10]
        scale_notes = [notes[(start_idx + i) % 12] for i in intervals]
        return ", ".join(scale_notes)

    def _update_analysis_ui(self, result):
        # Update info cards with results
        self.bpm_card["value"].configure(text=str(result['bpm']), text_color=self.current_theme_color)
        self.key_card["value"].configure(text=result['key'], text_color=self.current_theme_color)
        self.duration_card["value"].configure(text=result.get('duration', '--'), text_color=self.current_theme_color)
        
        # Tooltips data
        self.bpm_card["card"].tooltip_text = f"Tempo bài hát là {result['bpm']} nhịp/phút."
        
        k, s = result['key'].split(' ') if ' ' in result['key'] else (result['key'], "Major")
        notes_str = self._get_scale_notes(k, s)
        self.key_card["card"].tooltip_text = f"Bài hát có Key {result['key']} với các note chính {notes_str}."
        
        duration_str = result.get('duration', '--')
        if ":" in duration_str:
            m, sec = duration_str.split(":")
            self.duration_card["card"].tooltip_text = f"Độ dài {m} phút {sec} giây"
        else:
            self.duration_card["card"].tooltip_text = f"Độ dài {duration_str}"
        
        
        self._display_waveform(result["waveform"])
        self.set_status("", is_loading=False)
        # Enable nút tách stem
        self.btn_separate.configure(state="normal")
        
    def _display_waveform(self, img_path):
        try:
            wf_img = Image.open(img_path)
            target_width = 480
            ratio = target_width / wf_img.width
            target_height = min(int(wf_img.height * ratio), 140) # Khóa max height
            
            ctk_img = ctk.CTkImage(light_image=wf_img, dark_image=wf_img, size=(target_width, target_height))
            self.waveform_label.configure(image=ctk_img, text="")
            
            self.waveform_label.bind("<Button-3>", self.show_context_menu)
        except Exception as e:
            print(f"Lỗi hiển thị waveform: {e}")

    def show_context_menu(self, event):
        if self.selected_file:
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def start_separation(self):
        if not self.selected_file:
            return
            
        out_dir = self.default_output_dir if self.default_output_dir else os.path.dirname(self.selected_file)
        self.set_status("Đang tách Stem (Demucs)...", is_loading=True)
        # Disable nút khi đang tách
        self.btn_separate.configure(state="disabled", text="⏳  Đang tách...")

        self.separator.separate(
            self.selected_file,
            out_dir,
            output_format=self.output_format,
            two_stems=self.two_stems_mode,
            progress_callback=lambda m: self.set_status(f"Tách nhạc: {m}", is_loading=True),
            done_callback=lambda d: self.after(0, self._separation_done, d),
            error_callback=lambda e: self.after(0, self._separation_error, e)
        )

    def _separation_done(self, out_dir):
        self.last_output_dir = out_dir
        self.set_status("✅  Tách hoàn tất!", is_loading=False)
        # Restore nút tách và enable nút mở thư mục
        self.btn_separate.configure(state="normal", text="🎧  Tách Nhạc cụ & Vocal")
        self.btn_open_folder.configure(state="normal")
        messagebox.showinfo("Thành công", f"Các Stems đã được lưu vào:\n{out_dir}")

    def _separation_error(self, error_msg):
        self.set_status("❌  Lỗi tách Stem", is_loading=False)
        self.btn_separate.configure(state="normal", text="🎧  Tách Nhạc cụ & Vocal")
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{error_msg}")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = AutoToneApp()
    app.mainloop()
