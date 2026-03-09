import os
import shutil
import urllib.request
import urllib.error
import zipfile
import threading
import subprocess
import time
import platform
import sys

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

class CLI_Toolbox:
    def __init__(self):
        self.selected_sd = None
        self.os_type = platform.system()

    def print_header(self):
        os.system('clear' if self.os_type != 'Windows' else 'cls')
        print("="*65)
        print("             🚀 3DS ULTIMATE SD TOOLBOX 🚀")
        print("      Dọn dẹp, Cài đặt & Hack 3DS (Hỗ trợ Windows & macOS)")
        print("="*65)
        if self.selected_sd:
            print(f"👉 Thẻ SD đang chọn: {self.selected_sd}")
        else:
            print("👉 Thẻ SD đang chọn: CHƯA CHỌN")
        print("="*65)

    def detect_sd_cards(self):
        print("\n⏳ Đang quét các ổ đĩa ngoài / Thẻ SD...")
        sd_cards = []
        
        if self.os_type == "Windows":
            import ctypes
            # Get Logical Drives
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if bitmask & 1:
                    drive = f"{letter}:\\"
                    # Check drive type (2 = DRIVE_REMOVABLE)
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                    if drive_type == 2:
                        sd_cards.append(drive)
                bitmask >>= 1
        else:
            # macOS / Linux Drive Detection
            volumes_dir = "/Volumes"
            if os.path.exists(volumes_dir):
                for vol in os.listdir(volumes_dir):
                    if vol not in ["Macintosh HD", "Recovery", "Preboot", "Update"] and not vol.startswith("com.apple"):
                        path = os.path.join(volumes_dir, vol)
                        if os.path.ismount(path):
                            sd_cards.append(path)
        
        if not sd_cards:
            print("❌ Không tìm thấy thẻ SD hoặc ổ USB Removable nào.")
            print("Vui lòng cắm thẻ SD của 3DS vào máy tính!")
            return None
        
        print("\nCác thẻ SD/USB phát hiện được:")
        for idx, sd in enumerate(sd_cards):
            try:
                usage = shutil.disk_usage(sd)
                total_gb = usage.total / (1024**3)
                free_gb = usage.free / (1024**3)
                print(f"  [{idx + 1}] {sd} (Tổng: {total_gb:.1f}GB - Trống: {free_gb:.1f}GB)")
            except Exception:
                print(f"  [{idx + 1}] {sd}")
        
        try:
            choice = input(f"\nNhập số (1-{len(sd_cards)}) để chọn thẻ SD (hoặc bấm Enter để huỷ): ")
            if not choice.strip(): return
            
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(sd_cards):
                self.selected_sd = sd_cards[choice_idx - 1]
                print(f"✅ Đã chọn: {self.selected_sd}")
            else:
                print("❌ Lựa chọn không hợp lệ.")
        except ValueError:
            print("❌ Vui lòng nhập số.")

    def download_file(self, url, dest_path):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            return True
        except Exception as e:
            print(f"❌ Lỗi tải xuống: {e}")
            return False

    def check_fat32(self, sd):
        """Kiểm tra FAT32. Trả về False nếu xác định được thẻ sai định dạng."""
        try:
            if self.os_type == "Windows":
                drive_letter = sd[:2]
                res = subprocess.run(["wmic", "volume", "where", f"DriveLetter='{drive_letter}'", "get", "FileSystem"], check=True, capture_output=True, text=True)
                return "FAT32" in res.stdout.upper()
            else:
                res = subprocess.run(["diskutil", "info", sd], check=True, capture_output=True, text=True)
                out = res.stdout.upper()
                return "FAT32" in out or "MS-DOS" in out or "FAT16" in out
        except Exception:
            return True

    def install_luma(self):
        if not self.selected_sd:
            print("❌ Vui lòng chọn thẻ SD trước (Phím 1)!")
            return
            
        if not self.check_fat32(self.selected_sd):
            print("\n⚠️ CẢNH BÁO: Thẻ SD của bạn dường như KHÔNG phải định dạng FAT32!")
            print("Máy 3DS CHỈ đọc được thẻ định dạng FAT32 (Cluster Size 32KB).")
            print("Nếu bạn tiếp tục, Tool vẫn xả file nhưng 3DS sẽ KHÔNG NHẬN THẺ!")
            ans = input("Bạn có chắc chắn muốn ép buộc tiếp tục cài đặt không? (y/N): ")
            if ans.lower() != 'y':
                print("❌ Đã HỦY quá trình cài đặt để bạn tự đi Format FAT32.")
                return

        print("\n>> BẮT ĐẦU CÀI ĐẶT LUMA3DS (HACK SD) <<")
        print("⏳ Đang dò tìm phiên bản Luma3DS mới nhất từ Github API...")
        
        luma_url = get_latest_luma_url()
        if not luma_url:
            print("❌ Không thể lấy được link tải Luma3DS mới nhất. Github có thể bị lỗi.")
            return

        print(f"⏳ Đang tải {luma_url.split('/')[-1]}...")
        tmp_zip = os.path.join(self.selected_sd, "luma_tmp.zip")
        if self.download_file(luma_url, tmp_zip):
            print("✅ Tải thành công. Đang giải nén vào thẻ SD...")
            with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
                zip_ref.extractall(self.selected_sd)
            os.remove(tmp_zip)
            print("✅ Đã cài đặt Luma3DS (`boot.firm` và `boot.3dsx`) lên thẻ SD thành công!")
            print("🌟 Bây giờ thẻ nhớ đã có đầy đủ hệ điều hành Luma mới nhất.")
            
            # Tự động kết nối cài luôn thư mục và ứng dụng cơ bản vói script finalize
            self.install_essential_software()

        else:
            print("❌ Không thể tải Luma3DS.")

    def install_essential_software(self):
        if not self.selected_sd:
            print("❌ Vui lòng chọn thẻ SD trước (Phím 1)!")
            return
        print("\n>> TẢI CÁC HOMEBREW CƠ BẢN <<")
        cias_dir = os.path.join(self.selected_sd, "cias")
        hbl_dir = os.path.join(self.selected_sd, "3ds")
        os.makedirs(cias_dir, exist_ok=True)
        os.makedirs(hbl_dir, exist_ok=True)
        
        # Download CIAs
        for name, url in CIA_URLS.items():
            print(f"⏳ Đang tải {name} (.cia)...")
            dest = os.path.join(cias_dir, f"{name}.cia")
            if self.download_file(url, dest):
                print(f"  👉 Đã lưu: /cias/{name}.cia")
                
        # Download 3DSX for Homebrew Launcher
        print("\n>> TẢI BẢN .3DSX CHO HOMEBREW LAUNCHER <<")
        for name, url in HBL_3DSX_URLS.items():
            print(f"⏳ Đang tải {name} (.3dsx)...")
            
            # Create app specific folder
            app_dir = os.path.join(hbl_dir, name)
            os.makedirs(app_dir, exist_ok=True)
            
            dest = os.path.join(app_dir, f"{name}.3dsx")
            if self.download_file(url, dest):
                print(f"  👉 Đã lưu: /3ds/{name}/{name}.3dsx")
                
        # Download Finalize Setup files
        print("\n>> TẢI GÓI FINALIZE SETUP (CÀI ĐẶT TỰ ĐỘNG) <<")
        payloads_dir = os.path.join(self.selected_sd, "luma", "payloads")
        os.makedirs(payloads_dir, exist_ok=True)
        
        for name, url in FINALIZE_URLS.items():
            print(f"⏳ Đang tải {name}...")
            if name == "finalize.romfs":
                dest = os.path.join(self.selected_sd, name)
            else:
                dest = os.path.join(payloads_dir, name)
            if self.download_file(url, dest):
                if name == "finalize.romfs":
                    print(f"  👉 Đã lưu: /{name} (Root Thẻ SD)")
                else:
                    print(f"  👉 Đã lưu: /luma/payloads/{name}")
        
        print("\n" + "="*65)
        print(" TẤT CẢ QUÁ TRÌNH THÀNH CÔNG! ")
        print("="*65)
        print("\n HƯỚNG DẪN CUỐI CÙNG DÀNH CHO BẠN:")
        print(" 1. Rút thẻ cắm lại vào 3DS.")
        print(" 2. Nhấn & GIỮ NÚT `START`, bóp Nút Nguồn để bật máy.")
        print(" 3. Chọn `x_finalize_helper` trong Menu hiện ra.")
        print(" 4. Làm theo hướng dẫn trên màn hình 3DS để nó tự động cài FBI và dọn rác hệ thống.")
        print("\n Chúc bạn chơi game vui vẻ!!")

    def copy_minh_store(self):
        if not self.selected_sd:
            print("❌ Vui lòng chọn thẻ SD trước (Phím 1)!")
            return
        print("\n>> COPY MINH GAME STORE <<")
        
        # Sửa cấu hình để chạy đúng nếu đóng thành .exe / file binary
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            if base_dir.endswith('Contents/MacOS'):
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        source_cia = os.path.join(base_dir, "MinhGameStore-v1.3.7.cia")
        
        cias_dir = os.path.join(self.selected_sd, "cias")
        os.makedirs(cias_dir, exist_ok=True)
        
        if os.path.exists(source_cia):
            dest_cia = os.path.join(cias_dir, "MinhGameStore-v1.3.7.cia")
            try:
                shutil.copy2(source_cia, dest_cia)
                print("✅ Đã chép file MinhGameStore-v1.3.7.cia vào thư mục /cias/ thành công!")
            except Exception as e:
                print(f"❌ Lỗi copy: {e}")
        else:
            print(f"❌ Không tìm thấy file gốc tại {source_cia}")
            print("Vui lòng đảm bảo bạn đang chạy tool ở cùng thư mục chứa file MinhGameStore-v1.3.7.cia!")

    def create_folders(self):
        if not self.selected_sd:
            print("❌ Vui lòng chọn thẻ SD trước (Phím 1)!")
            return
        print("\n>> TẠO CẤU TRÚC THƯ MỤC CHUẨN <<")
        folders = ["3ds", "cias", "luma", "luma/payloads", "gm9", "gm9/scripts", "Nintendo 3DS", "themes"]
        for f in folders:
            # os.path.join có thể dùng / hoặc \\ tuỳ OS
            path = os.path.join(self.selected_sd, os.path.normpath(f)) 
            os.makedirs(path, exist_ok=True)
            print(f"  👉 Đã tạo: /{f}/")
        print("✅ Hoàn tất cấu trúc thẻ nhớ chuẩn.")

    def self_check_sd(self):
        if not self.selected_sd:
            print("❌ Vui lòng chọn thẻ SD trước (Phím 1)!")
            return False
        return True

    def rename_sd(self):
        if not self.self_check_sd(): return
        print(f"\n>> ĐỔI TÊN THẺ SD ({self.selected_sd}) <<")
        
        current_name = os.path.basename(self.selected_sd) if self.os_type != "Windows" else ""
        
        new_name = input(f"Nhập tên mới (Viết hoa, không dấu, max 11 kí tự) [Enter để huy]: ").strip().upper()
        if not new_name:
            print("❌ Đã huỷ đổi tên.")
            return
            
        if len(new_name) > 11:
            print("❌ Lỗi: Tên thẻ định dạng FAT32 không được dài quá 11 kí tự!")
            return
            
        print(f"⏳ Đang khởi tạo đổi tên thành: {new_name}...")
        try:
            if self.os_type == "Windows":
                drive_letter = self.selected_sd[:2]
                subprocess.run(["label", drive_letter, new_name], check=True, shell=True)
            else:
                subprocess.run(["diskutil", "rename", self.selected_sd, new_name], check=True, capture_output=True, text=True)
                
            print(f"✅ Đã đổi tên thành công thành '{new_name}'.")
            time.sleep(1) # wait for remount
            self.selected_sd = None # force re-select
            print("🔄 Vui lòng quét lại Thẻ SD (phím 1) để thấy tên mới.")
        except Exception as e:
            print(f"❌ Lỗi Đổi tên: {e}")

    def copy_games(self):
        if not self.self_check_sd(): return
        print(f"\n>> COPY GAME (.cia, .3ds) VÀO {self.selected_sd} <<")
        print("💡 Bạn có thể kéo thả trực tiếp một file game (.cia, .3ds) hoặc CẢ MỘT THƯ MỤC chứa game vào cửa sổ này.")
        source_path = input("👉 Đường dẫn file/thư mục game: ").strip()
        
        # Remove quotes from drag-and-drop on macOS/Windows
        if source_path.startswith("'") and source_path.endswith("'"): source_path = source_path[1:-1]
        elif source_path.startswith('"') and source_path.endswith('"'): source_path = source_path[1:-1]
        
        if not os.path.exists(source_path):
            print("❌ Lỗi: Đường dẫn không tồn tại.")
            return
            
        cias_dir = os.path.join(self.selected_sd, "cias")
        os.makedirs(cias_dir, exist_ok=True)
        
        files_to_copy = []
        if os.path.isfile(source_path):
            if source_path.lower().endswith(('.cia', '.3ds')):
                files_to_copy.append(source_path)
        elif os.path.isdir(source_path):
            for file in os.listdir(source_path):
                if file.lower().endswith(('.cia', '.3ds')):
                    files_to_copy.append(os.path.join(source_path, file))
                    
        if not files_to_copy:
            print("❌ Không tìm thấy file (.cia) hay (.3ds) nào hợp lệ trong đường dẫn đã nhập!")
            return
            
        print(f"⏳ Tìm thấy {len(files_to_copy)} file. Bắt đầu chép...")
        for i, fpath in enumerate(files_to_copy, 1):
            fname = os.path.basename(fpath)
            print(f"  👉 Đang chép [{i}/{len(files_to_copy)}]: {fname}...")
            try:
                shutil.copy2(fpath, os.path.join(cias_dir, fname))
            except Exception as e:
                print(f"  ❌ Lỗi khi chép {fname}: {e}")
                
        print("✅ Hoàn tất copy Game! Bạn có thể cắm thẻ qua 3DS dùng FBI cài đặt.")

    def eject_sd(self):
        if not self.self_check_sd(): return
        print(f"\n>> ĐANG NGẮT KẾT NỐI {self.selected_sd} <<")
        
        if self.os_type == "Windows":
            print("⚠️ Trên Windows: Vui lòng click phải vào biểu tượng USB ở Taskbar góc dưới bên phải và chọn 'Eject / Safely Remove Hardware'.")
            self.selected_sd = None
            print("✅ Đã giải phóng quyền truy cập. Bạn có thể rút thẻ ra an toàn.")
        else:
            try:
                subprocess.run(["diskutil", "eject", self.selected_sd], check=True, capture_output=True, text=True)
                print("✅ Đã Eject an toàn! Lấy thẻ ra và cắm vào 3DS nhé.")
                self.selected_sd = None
            except subprocess.CalledProcessError as e:
                print(f"❌ Lỗi Eject: {e.stderr}")

    def run(self):
        while True:
            self.print_header()
            print("1. 🔎 Quét Lại & Chọn Thẻ SD")
            print("2. 🔓 Format & Hack Mới SD (Cài Luma, Tạo Thư mục, Xóa sạch)")
            print("3. 📁 Tạo Cấu trúc Thư mục 3DS Chuẩn")
            print("4. 📦 Tải Ứng dụng Thiết yếu (FBI, Universal-Updater, ...)")
            print("5. ⭐ Chép Minh Game Store v1.3.7 (Mới Nhất) vào SD")
            print("6. 🎮 Copy Game (.cia, .3ds) vào thẻ SD")
            print("7. ✏️ Đổi tên thẻ SD (Rename)")
            print("8. ⏏️ Eject Thẻ SD an toàn")
            print("9. 🚪 Thoát Toolbox")
            print("-" * 65)
            
            choice = input("👉 Nhập số chức năng muốn chạy: ")
            
            if choice == '1':
                self.detect_sd_cards()
            elif choice == '2':
                print("Lưu ý: Bạn phải tự Format FAT32 từ Disk Utility trước khi bấm nhé!")
                self.install_luma()
            elif choice == '3':
                self.create_folders()
            elif choice == '4':
                self.install_essential_software()
            elif choice == '5':
                self.copy_minh_store()
            elif choice == '6':
                self.copy_games()
            elif choice == '7':
                self.rename_sd()
            elif choice == '8':
                self.eject_sd()
            elif choice == '9':
                print("Tạm biệt! Hẹn gặp lại. Chơi game vui vẻ trên 3DS nhé!")
                break
            else:
                print("❌ Lựa chọn không hợp lệ!")
            
            input("\nNhấn Enter để tiếp tục...")

if __name__ == "__main__":
    app = CLI_Toolbox()
    app.run()
