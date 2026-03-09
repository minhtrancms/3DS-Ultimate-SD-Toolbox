import sys
import os
import shutil
import urllib.request
import urllib.error
import zipfile
import threading
import subprocess
import time
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QComboBox, QPushButton, QTextEdit, QMessageBox, QInputDialog, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# URLs for 3DS Homebrew CIA files
CIA_URLS = {
    "FBI": "https://github.com/Steveice10/FBI/releases/latest/download/FBI.cia",
    "Universal-Updater": "https://github.com/Universal-Team/Universal-Updater/releases/latest/download/Universal-Updater.cia",
    "Anemone3DS": "https://github.com/astronautlevel2/Anemone3DS/releases/latest/download/Anemone3DS.cia",
    "Checkpoint": "https://github.com/FlagBrew/Checkpoint/releases/latest/download/Checkpoint.cia",
    "FTPD": "https://github.com/mtheall/ftpd/releases/latest/download/ftpd.cia"
}

# 3DSX versions for running from Homebrew Launcher (No install needed)
HBL_3DSX_URLS = {
    "FBI": "https://github.com/Steveice10/FBI/releases/latest/download/FBI.3dsx",
    "Universal-Updater": "https://github.com/Universal-Team/Universal-Updater/releases/latest/download/Universal-Updater.3dsx",
    "Checkpoint": "https://github.com/FlagBrew/Checkpoint/releases/latest/download/Checkpoint.3dsx",
    "FTPD": "https://github.com/mtheall/ftpd/releases/latest/download/ftpd.3dsx",
    "Anemone3DS": "https://github.com/astronautlevel2/Anemone3DS/releases/latest/download/Anemone3DS.3dsx",
    "Faketik": "https://github.com/ihaveamac/faketik/releases/latest/download/faketik.3dsx"
}

# Finalize Setup files (for automated CIA installation & DSP dump)
FINALIZE_URLS = {
    "finalize.romfs": "https://github.com/hacks-guide/finalize/releases/latest/download/finalize.romfs",
    "x_finalize_helper.firm": "https://github.com/hacks-guide/finalize/releases/latest/download/x_finalize_helper.firm"
}

# No hardcoded Luma URL because GitHub zip names keep changing per release version
def get_latest_luma_url():
    import json
    try:
        req = urllib.request.Request("https://api.github.com/repos/LumaTeam/Luma3DS/releases/latest", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for asset in data.get('assets', []):
                if asset['name'].startswith('Luma3DS') and asset['name'].endswith('.zip'):
                    return asset['browser_download_url']
    except Exception as e:
        print(f"Error fetching Luma API: {e}")
    return None

class Worker(QThread):
    log_signal = pyqtSignal(str)
    refresh_sd_signal = pyqtSignal()

    def __init__(self, target_func, *args, **kwargs):
        super().__init__()
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.target_func(*self.args, **self.kwargs)

class SDToolBox(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3DS Ultimate SD Toolbox (macOS)")
        self.setFixedSize(600, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # A container to store user choice from dialog
        self._user_choice = None

        # --- Section: SD Card Detection ---
        sd_group = QGroupBox(" 1. Trình quản lý Thẻ SD ")
        sd_main_layout = QVBoxLayout()
        sd_main_layout.setContentsMargins(10, 15, 10, 10)
        sd_main_layout.setSpacing(10)
        
        self.sd_dropdown = QComboBox()
        self.sd_dropdown.setMinimumHeight(35)
        sd_main_layout.addWidget(self.sd_dropdown)

        sd_btn_layout = QHBoxLayout()
        sd_btn_layout.setSpacing(10)

        refresh_btn = QPushButton(" Làm mới")
        refresh_btn.setMinimumHeight(35)
        refresh_btn.clicked.connect(self.detect_sd_cards)
        sd_btn_layout.addWidget(refresh_btn)

        rename_btn = QPushButton(" Đổi Tên")
        rename_btn.setMinimumHeight(35)
        rename_btn.clicked.connect(self.rename_sd)
        sd_btn_layout.addWidget(rename_btn)

        eject_btn = QPushButton(" Eject")
        eject_btn.setMinimumHeight(35)
        eject_btn.clicked.connect(self.eject_sd)
        sd_btn_layout.addWidget(eject_btn)
        
        sd_main_layout.addLayout(sd_btn_layout)
        sd_group.setLayout(sd_main_layout)
        main_layout.addWidget(sd_group)

        # --- Section: Quick Actions ---
        action_group = QGroupBox(" 2. Chức năng Nhanh ")
        action_layout = QVBoxLayout()
        action_layout.setContentsMargins(10, 15, 10, 10)
        action_layout.setSpacing(10)
        
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        btn_luma = QPushButton(" Format & Hack Mới thẻ SD (Luma + Thư mục)")
        btn_luma.setMinimumHeight(45)
        btn_luma.clicked.connect(lambda: self.run_task(self.install_luma, requires_format_confirm=True))
        action_layout.addWidget(btn_luma)

        btn_apps = QPushButton(" Cài Ứng Dụng (FBI, hShop...)")
        btn_apps.setMinimumHeight(35)
        btn_apps.clicked.connect(lambda: self.run_task(self.install_essential_software))
        row1.addWidget(btn_apps)

        btn_copy = QPushButton(" Copy Minh Game Store")
        btn_copy.setMinimumHeight(35)
        btn_copy.clicked.connect(lambda: self.run_task(self.copy_minh_store))
        row1.addWidget(btn_copy)

        btn_copy_game = QPushButton(" Tải Game (.cia, .3ds) vào Thẻ")
        btn_copy_game.setMinimumHeight(35)
        btn_copy_game.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        btn_copy_game.clicked.connect(self.select_and_copy_games)
        row2.addWidget(btn_copy_game)

        btn_twilight = QPushButton(" Cài Giả lập NDS (TWiLight Menu++)")
        btn_twilight.setMinimumHeight(35)
        btn_twilight.clicked.connect(lambda: self.run_task(self.install_twilight))
        row2.addWidget(btn_twilight)

        row3 = QHBoxLayout()
        row3.setSpacing(10)
        
        btn_format = QPushButton(" Ép Format FAT32 (Tự Động)")
        btn_format.setMinimumHeight(35)
        btn_format.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold;")
        btn_format.clicked.connect(self.prompt_format_fat32)
        row3.addWidget(btn_format)

        action_layout.addLayout(row1)
        action_layout.addLayout(row2)
        action_layout.addLayout(row3)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        # --- Section: Console Log ---
        log_group = QGroupBox(" Console Log ")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(10, 15, 10, 10)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        font = self.log_area.font()
        font.setFamily("Menlo")
        font.setPointSize(12)
        self.log_area.setFont(font)
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        self.detect_sd_cards()

    def format_log(self, message):
        lines = message.split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            
            c_color = ""
            c_bold = False
            
            if line.startswith("---") or line.startswith("==="):
                c_color = "#00BCD4"
                c_bold = True
                formatted_lines.append(f"<span style='color:{c_color}; font-weight:bold;'>{line}</span>")
                continue
                
            # Pattern matching for auto coloring
            lower_line = line.lower()
            if "lỗi " in lower_line or "không thể" in lower_line or "không tìm thấy" in lower_line or "hủy" in lower_line or "không phát hiện" in lower_line:
                c_color = "#F44336" # Red
                c_bold = True
            elif "cảnh báo" in lower_line or "đang quét" in lower_line or "đang xóa" in lower_line or "đang tải" in lower_line or "đang giải nén" in lower_line or "đang đổi tên" in lower_line or "đang dò" in lower_line or "trên windows:" in lower_line or "đang ngắt" in lower_line or "tạo: /" in lower_line:
                c_color = "#FF9800" # Orange
            elif "thành công" in lower_line or "đã lưu" in lower_line or "đã tìm thấy" in lower_line or "đã xóa" in lower_line or "đã ngắt" in lower_line or "đã tạo" in lower_line or "đã đổi tên" in lower_line or "đã cập nhật" in lower_line or "đã cài đặt" in lower_line or "đã chép" in lower_line:
                c_color = "#4CAF50" # Green
                c_bold = True
            elif "hướng dẫn cuối cùng" in lower_line or line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or "chúc bạn" in lower_line or "tất cả quá trình" in lower_line:
                c_color = "#E91E63" # Pink/Magenta
                c_bold = True

            style = ""
            if c_color: style += f"color: {c_color};"
            if c_bold: style += "font-weight: bold;"
            
            prefix = "[*]"
            
            if style:
                formatted_lines.append(f"<span style='{style}'>{prefix} {line}</span>")
            else:
                formatted_lines.append(f"{prefix} {line}")
                
        return "<br>".join(formatted_lines)

    def log(self, message):
        self.raw_append(self.format_log(message))
        
    def raw_append(self, html_msg):
        self.log_area.append(html_msg)
        # Auto scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def detect_sd_cards(self):
        self.log("Đang quét các ổ đĩa ngoài...")
        sd_cards = []
        
        if platform.system() == "Windows":
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if bitmask & 1:
                    drive = f"{letter}:\\"
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                    if drive_type == 2: # DRIVE_REMOVABLE
                        sd_cards.append(drive)
                bitmask >>= 1
        else:
            volumes_dir = "/Volumes"
            if os.path.exists(volumes_dir):
                for vol in os.listdir(volumes_dir):
                    if vol not in ["Macintosh HD", "Recovery", "Preboot", "Update"] and not vol.startswith("com.apple"):
                        path = os.path.join(volumes_dir, vol)
                        if os.path.ismount(path):
                            sd_cards.append(path)

        formatted_sd_cards = []
        for path in sd_cards:
            try:
                usage = shutil.disk_usage(path)
                total_gb = usage.total / (1024**3)
                free_gb = usage.free / (1024**3)
                label = f"{path} (Tổng: {total_gb:.1f}GB - Trống: {free_gb:.1f}GB)"
                formatted_sd_cards.append((label, path))
            except Exception:
                formatted_sd_cards.append((path, path))
        
        self.sd_dropdown.clear()
        if formatted_sd_cards:
            for label, path in formatted_sd_cards:
                self.sd_dropdown.addItem(label, path)
            self.log(f"Đã tìm thấy {len(sd_cards)} ổ đĩa di động.")
        else:
            self.sd_dropdown.addItem("Không tìm thấy thẻ SD", None)
            self.log("Không phát hiện thẻ SD/USB nào. Vui lòng cắm thẻ và ấn Làm mới.")

    def get_selected_sd(self):
        sd = self.sd_dropdown.currentData()
        if not sd or not os.path.exists(sd):
            QMessageBox.critical(self, "Lỗi", "Vui lòng chọn một thẻ SD hợp lệ!")
            return None
        return sd
        
    def check_fat32(self, sd):
        """Kiểm tra xem thẻ có phải FAT32 không. Trả về False nếu chắc chắn sai, True nếu đúng hoặc không thể xác định."""
        try:
            if platform.system() == "Windows":
                drive_letter = sd[:2]
                res = subprocess.run(["wmic", "volume", "where", f"DriveLetter='{drive_letter}'", "get", "FileSystem"], check=True, capture_output=True, text=True)
                return "FAT32" in res.stdout.upper()
            else:
                res = subprocess.run(["diskutil", "info", sd], check=True, capture_output=True, text=True)
                out = res.stdout.upper()
                return "FAT32" in out or "MS-DOS" in out or "FAT16" in out
        except Exception:
            return True

    def eject_sd(self):
        sd = self.get_selected_sd()
        if not sd: return
        self.log(f"Đang ngắt kết nối an toàn cho: {sd}...")
        try:
            if platform.system() == "Windows":
                 self.log("Trên Windows: Vui lòng dùng Eject ở góc phải màn hình bên Taskbar.")
                 return
            subprocess.run(["diskutil", "eject", sd], check=True, capture_output=True, text=True)
            self.log(" Đã ngắt kết nối an toàn. Bạn có thể rút thẻ SD ra.")
            self.sd_dropdown.clear()
            self.detect_sd_cards()
        except subprocess.CalledProcessError as e:
            self.log(f" Lỗi Eject: {e.stderr}")

    def rename_sd(self):
        sd = self.get_selected_sd()
        if not sd: return
        
        current_name = os.path.basename(sd)
        if platform.system() == "Windows":
             current_name = sd[:2] # e.g. D:
             
        new_name, ok = QInputDialog.getText(
            self, "Đổi Tên Thẻ SD", 
            f"Nhập tên mới (Viết hoa, không dấu, tối đa 11 kí tự):", 
            text="" if platform.system() == "Windows" else current_name
        )
        
        if ok and new_name is not None:
            new_name = new_name.strip().upper()
            if not new_name: return
            if len(new_name) > 11:
                QMessageBox.warning(self, "Lỗi", "Tên thẻ SD định dạng FAT32 không được vượt quá 11 kí tự!")
                return
                
            self.log(f"Đang đổi tên thẻ SD thành: {new_name}...")
            try:
                if platform.system() == "Windows":
                    drive_letter = sd[:2]
                    subprocess.run(["label", drive_letter, new_name], check=True, shell=True)
                else:
                    subprocess.run(["diskutil", "rename", sd, new_name], check=True, capture_output=True, text=True)
                    
                self.log(f" Đã đổi tên thành công thành '{new_name}'.")
                time.sleep(1) # wait for system to remount
                self.detect_sd_cards()
                
            except Exception as e:
                self.log(f" Lỗi Đổi tên: {e}")

    def run_task(self, task_func, *args, requires_format_confirm=False, **kwargs):
        sd = self.get_selected_sd()
        if not sd: return
        
        if requires_format_confirm:
            if not self.check_fat32(sd):
                fat32_reply = QMessageBox.warning(
                    self,
                    "⚠️ CẢNH BÁO ĐỊNH DẠNG SAI",
                    f"Thẻ SD ({sd}) dường như KHÔNG phải là định dạng FAT32 (có thể là exFAT/NTFS).\n\n"
                    "Máy 3DS CHỈ đọc được thẻ SD đã format FAT32 (Cluster 32KB).\n"
                    "Nếu bỏ qua, Tool vẫn sẽ chạy nhưng máy 3DS sẽ không nhận thẻ!\n\n"
                    "Bạn có chắc chắn muốn tiếp tục không?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if fat32_reply != QMessageBox.StandardButton.Yes:
                    self.log(" Đã HỦY thao tác để người dùng tự Format FAT32.")
                    return
                    
            reply = QMessageBox.warning(
                self, 
                "Xác nhận Format thẻ SD", 
                f"Bạn có chắc chắn muốn xóa TOÀN BỘ dữ liệu (Format)\ntrên thẻ {sd} để làm lại từ đầu không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.log(" Đã HỦY thao tác do không đồng ý xóa thẻ SD.")
                return

        self.worker = Worker(task_func, sd, *args, **kwargs)
        self.worker.log_signal.connect(self.raw_append)
        self.worker.refresh_sd_signal.connect(self.detect_sd_cards)
        self.worker.start()

    def thread_log(self, msg):
        # We need to emit signal since you can't access GUI from worker thread
        self.worker.log_signal.emit(self.format_log(msg))

    def download_file(self, url, dest_path):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            return True
        except Exception as e:
            self.thread_log(f" Lỗi tải xuống: {e}")
            return False

    def clean_sd_card(self, sd):
        self.thread_log(f"Đang xóa sạch dữ liệu cũ tại {sd}...")
        success = True
        try:
            for item in os.listdir(sd):
                item_path = os.path.join(sd, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    self.thread_log(f" Cảnh báo: Không thể xóa {item} ({e}). Đang tiếp tục...")
                    success = False # Flag that it wasn't a perfect wipe, but we continue
                    
            if success:
                self.thread_log(" Đã xóa sạch thẻ SD.")
            else:
                self.thread_log(" Đã xóa phần lớn thẻ SD. Một vài file cứng đầu (ẩn) của macOS đã được giữ lại (không ảnh hưởng tới 3DS).")
            return True
        except Exception as e:
            self.thread_log(f" Lỗi nghiêm trọng khi truy cập ổ đĩa: {e}")
            return False

    def install_luma(self, sd):
        if not self.clean_sd_card(sd):
            return

        self.thread_log("\n--- BẮT ĐẦU CÀI ĐẶT LUMA3DS ---")
        self.thread_log("Đang dò tìm phiên bản Luma3DS mới nhất từ Github API...")
        
        luma_url = get_latest_luma_url()
        if not luma_url:
            self.thread_log(" Không thể lấy được link tải Luma3DS mới nhất. Github có thể bị lỗi.")
            return

        self.thread_log(f"Đang tải {luma_url.split('/')[-1]}...")
        
        tmp_zip = os.path.join(sd, "luma_tmp.zip")
        if self.download_file(luma_url, tmp_zip):
            self.thread_log("Tải thành công. Đang giải nén vào thẻ SD...")
            with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
                zip_ref.extractall(sd)
            os.remove(tmp_zip)
            self.thread_log(" Đã cài đặt Luma3DS (`boot.firm` và `boot.3dsx`) lên thẻ SD thành công!")
            
            self.thread_log("\n--- TẠO CẤU TRÚC THƯ MỤC CHUẨN ---")
            folders = ["3ds", "cias", "luma", "luma/payloads", "gm9", "gm9/scripts", "Nintendo 3DS", "themes"]
            for f in folders:
                path = os.path.join(sd, f)
                os.makedirs(path, exist_ok=True)
                self.thread_log(f"Tạo: /{f}")
            self.thread_log(" Đã tạo cấu trúc thư mục 3DS chuẩn.")
            
            # Tự động tải luôn App và gói Finalize ở đây để quy trình khép kín 1-Click
            self.install_essential_software(sd)
        else:
            self.thread_log(" Không thể tải Luma3DS.")

    def install_essential_software(self, sd):
        self.thread_log("\n--- TẢI CÁC HOMEBREW CƠ BẢN ---")
        cias_dir = os.path.join(sd, "cias")
        hbl_dir = os.path.join(sd, "3ds")
        os.makedirs(cias_dir, exist_ok=True)
        os.makedirs(hbl_dir, exist_ok=True)
        
        # Download CIAs
        for name, url in CIA_URLS.items():
            self.thread_log(f"Đang tải {name} (.cia)...")
            dest = os.path.join(cias_dir, f"{name}.cia")
            if self.download_file(url, dest):
                self.thread_log(f" Đã lưu: /cias/{name}.cia")
                
        # Download 3DSX for Homebrew Launcher
        self.thread_log("\n--- TẢI BẢN .3DSX CHO HOMEBREW LAUNCHER ---")
        for name, url in HBL_3DSX_URLS.items():
            self.thread_log(f"Đang tải {name} (.3dsx)...")
            
            # Create app specific folder
            app_dir = os.path.join(hbl_dir, name)
            os.makedirs(app_dir, exist_ok=True)
            
            dest = os.path.join(app_dir, f"{name}.3dsx")
            if self.download_file(url, dest):
                self.thread_log(f" Đã lưu: /3ds/{name}/{name}.3dsx")
                
        # Download Finalize Setup files
        self.thread_log("\n--- TẢI GÓI FINALIZE SETUP (CÀI ĐẶT TỰ ĐỘNG) ---")
        payloads_dir = os.path.join(sd, "luma", "payloads")
        os.makedirs(payloads_dir, exist_ok=True)
        
        for name, url in FINALIZE_URLS.items():
            self.thread_log(f"Đang tải {name}...")
            if name == "finalize.romfs":
                dest = os.path.join(sd, name)
            else:
                dest = os.path.join(payloads_dir, name)
            if self.download_file(url, dest):
                if name == "finalize.romfs":
                    self.thread_log(f" Đã lưu: /{name} (Root Thẻ SD)")
                else:
                    self.thread_log(f" Đã lưu: /luma/payloads/{name}")
        
        self.thread_log("\n==================================")
        self.thread_log(" TẤT CẢ QUÁ TRÌNH THÀNH CÔNG! ")
        self.thread_log("==================================")
        self.thread_log("\n HƯỚNG DẪN CUỐI CÙNG DÀNH CHO BẠN:")
        self.thread_log(" 1. Rút thẻ cắm lại vào 3DS.")
        self.thread_log(" 2. Nhấn & GIỮ NÚT `START`, bóp Nút Nguồn để bật máy.")
        self.thread_log(" 3. Chọn `x_finalize_helper` trong Menu hiện ra.")
        self.thread_log(" 4. Máy sẽ tự động vào Finalize: Nhấn `A` và nhập Combo phím để nó TỰ ĐỘNG cài tất cả FBI, hShop, Universal Updater... ra màn hình chính, tự động dọn rác System.")
        self.thread_log("\n QUAN TRỌNG NHẤT (CHỐNG BRICK MÁY):")
        self.thread_log(" Sau khi làm xong mọi thứ lên màn hình chính. Bạn TẮT NGUỒN lại.")
        self.thread_log(" Nhấn GIỮ NÚT `START`, bóp Nguồn chọn `GodMode9`.")
        self.thread_log(" Nhấn BẤM PHÍM `HOME` -> `Scripts` -> `GM9Megascript` -> `Scripts from Plailect's Guide` -> `Setup Luma3DS to CTRNAND`.")
        self.thread_log(" Thoát ra bấm `HOME` -> `Scripts` -> `GM9Megascript` -> `Backup Options` -> `SysNAND Backup`.")
        self.thread_log(" Chúc bạn phưu lưu bất tận an toàn với chiếc Thẻ Thần Thánh này nhé!!")

    def copy_minh_store(self, sd):
        self.thread_log("\n--- COPY MINH GAME STORE ---")
        
        if getattr(sys, 'frozen', False):
            # Nếu chạy dưới dạng file thực thi (.exe / .app)
            base_dir = os.path.dirname(sys.executable)
            # Nếu trên macOS là .app thì phải lùi ra 3 thư mục gốc (TênApp.app/Contents/MacOS/TênApp)
            if base_dir.endswith('Contents/MacOS'):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
        else:
            # Nếu chạy bằng file .py
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        source_cia = os.path.join(base_dir, "MinhGameStore-v1.3.7.cia")
        cias_dir = os.path.join(sd, "cias")
        os.makedirs(cias_dir, exist_ok=True)
        
        if os.path.exists(source_cia):
            dest_cia = os.path.join(cias_dir, "MinhGameStore-v1.3.7.cia")
            try:
                shutil.copy2(source_cia, dest_cia)
                self.thread_log(" Đã chép file MinhGameStore-v1.3.7.cia vào thư mục /cias/ trên thẻ SD thành công!")
            except Exception as e:
                self.thread_log(f" Lỗi copy: {e}")
        else:
            self.thread_log(f" Không tìm thấy file MinhGameStore CIA ({source_cia}). Vui lòng kiểm tra lại!")

    def select_and_copy_games(self):
        sd = self.get_selected_sd()
        if not sd: return
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Chọn Game muốn chép", "", "3DS Games (*.cia *.3ds);;All Files (*)")
        if not file_paths: return
        self.run_task(self.copy_games_task, file_paths)

    def copy_games_task(self, sd, file_paths):
        self.thread_log("\n--- COPY GAME VÀO THẺ NHỚ ---")
        cias_dir = os.path.join(sd, "cias")
        os.makedirs(cias_dir, exist_ok=True)
        
        total_files = len(file_paths)
        for i, source in enumerate(file_paths, 1):
            filename = os.path.basename(source)
            size_mb = os.path.getsize(source) / (1024**2)
            self.thread_log(f"Đang chép [{i}/{total_files}]: {filename} (Dung lượng: {size_mb:.1f} MB)...")
            dest = os.path.join(cias_dir, filename)
            try:
                # Basic copy without progress bar, could take time depending on file size
                shutil.copy2(source, dest)
                self.thread_log(f" Đã chép thành công: {filename}")
            except Exception as e:
                self.thread_log(f" Lỗi copy {filename}: {e}")
                
        self.thread_log("\n HOÀN TẤT CHÉP GAME! BẠN CÓ THỂ RÚT THẺ VÀ CÀI QUA FBI/FBI CUSTOM TRÊN 3DS.")

    def prompt_format_fat32(self):
        sd = self.get_selected_sd()
        if not sd: return
        
        reply = QMessageBox.warning(
            self, 
            "⚠️ NGHIỀN NÁT & ÉP FORMAT FAT32", 
            f"Bạn có chắc chắn muốn TỰ ĐỘNG CÀY MẶT & ĐỊNH DẠNG LẠI THẺ {sd} thành FAT32 không?\n"
            "TOÀN BỘ DỮ LIỆU SẼ BAY MÀU VĨNH VIỄN!\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.run_task(self.auto_format_fat32_task)

    def auto_format_fat32_task(self, sd):
        self.thread_log("\n--- BẮT ĐẦU ÉP FORMAT THẺ THÀNH ĐỊNH DẠNG FAT32 CHUẨN ---")
        try:
            if platform.system() == "Windows":
                self.thread_log(" Đang chạy lệnh Format FAT32 của Windows...")
                self.thread_log(" Cảnh báo: Nếu thẻ lớn hơn 32GB, lệnh này của Windows sẽ tự động báo lỗi. Khi đó bạn bắt buộc dùng App GUIFormat để ép Format bằng tay!")
                drive_letter = sd[:2]
                res = subprocess.run(["format", drive_letter, "/FS:FAT32", "/V:3DS_SD", "/Q", "/Y"], capture_output=True, text=True)
                if res.returncode == 0:
                    self.thread_log(" Đã Ép Format FAT32 thành công rực rỡ! Bắt đầu chép Luma thôi.")
                    time.sleep(1)
                    self.worker.refresh_sd_signal.emit()
                else:
                    self.thread_log(f" Lỗi Hệ điều hành Windows: Phần vùng quá lớn hoặc chưa được Mount quyền. ({res.stderr})")
                    self.thread_log(" Vui lòng sử dụng công cụ GUIFormat (Tạo bởi Ridgecrop) để xử lý thay thế!")
            else:
                self.thread_log(" Đang đọc Device Node từ hệ thống macOS...")
                info_res = subprocess.run(["diskutil", "info", sd], check=True, capture_output=True, text=True)
                dev_node = None
                for line in info_res.stdout.split('\n'):
                    if 'Device Node:' in line:
                        dev_node = line.split('Device Node:')[1].strip()
                        break
                
                if dev_node:
                    self.thread_log(f" Tìm thấy phân vùng ổ đĩa: {dev_node}. Bắt đầu nghiền nát...")
                    fmt_res = subprocess.run(["diskutil", "eraseVolume", "FAT32", "3DS_SD", dev_node], check=True, capture_output=True, text=True)
                    self.thread_log(" Đã Ép Format FAT32 bằng lệnh Apple thành công rực rỡ! Bắt đầu chép Luma thôi.")
                    time.sleep(1)
                    self.worker.refresh_sd_signal.emit()
                else:
                    self.thread_log(" Không thể tìm ra thiết bị đích (Device Node) từ macOS. Lỗi bất ngờ!")
        except Exception as e:
            self.thread_log(f" Lỗi Quá Trình Format FAT32: {e}")

    def install_twilight(self, sd):
        self.thread_log("\n--- BẮT ĐẦU CÀI ĐẶT TWiLIGHT MENU++ (GIẢ LẬP NDS) ---")
        self.thread_log("Đang dò tìm phiên bản TWiLight Menu++ mới nhất...")
        
        url = "https://api.github.com/repos/DS-Homebrew/TWiLightMenu/releases/latest"
        download_url = None
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as res:
                data = __import__('json').loads(res.read().decode())
                for asset in data.get('assets', []):
                    if asset['name'] == 'TWiLightMenu-3DS.7z':
                        download_url = asset['browser_download_url']
                        break
        except Exception as e:
            self.thread_log(f" Lỗi Github API: {e}")
            return
            
        if not download_url:
            self.thread_log(" Không tìm thấy file cài đặt TWiLight Menu 3DS.")
            return

        tmp_7z = os.path.join(sd, "twilight_tmp.7z")
        self.thread_log("Đang tải TWiLightMenu-3DS.7z (Cần một chút thời gian)...")
        if self.download_file(download_url, tmp_7z):
            self.thread_log(" Đã tải xong! Đang giải nén file .7z (Sẽ mất vài phút, vui lòng KHÔNG tắt App!)...")
            try:
                import py7zr
                with py7zr.SevenZipFile(tmp_7z, mode='r') as z:
                    z.extractall(path=sd)
                os.remove(tmp_7z)
                self.thread_log(" Đã cài đặt thành công Giả lập NDS (TWiLight Menu++)!")
                
                # Create rom folders
                for console in ["nds", "gba", "snes", "gbc"]:
                    os.makedirs(os.path.join(sd, "roms", console), exist_ok=True)
                self.thread_log(" Đã tạo sẵn các thư mục chứa game ở: /roms/nds/, /roms/gba/ ...")
                self.thread_log(" HƯỚNG DẪN CUỐI CÙNG: \n 1. Rút thẻ ra, chép game NDS (.nds) vào thư mục /roms/nds/\n 2. Game Gameboy (.gba) chép vào /roms/gba/\n 3. Cắm thẻ vào chơi trực tiếp thông qua TWiLight Menu++ !!")
            except Exception as e:
                self.thread_log(f" Lỗi giải nén .7z: {e}")
        else:
            self.thread_log(" Lỗi không thể tải được TWiLight Menu!")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SDToolBox()
    window.show()
    sys.exit(app.exec())
