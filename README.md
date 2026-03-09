# 🚀 3DS Ultimate SD Toolbox (macOS & Windows)

Are you tired of manually downloading multiple files, creating folders, and fixing black screens after formatting or buying a new Nintendo 3DS?
This Toolbox is designed to turn the tedious 3DS CFW (Custom Firmware) setup process into a seamless "1-Click To Win" experience!

## 🔥 Killer Features
- 🔎 **Cross-Platform Auto Detect**: Automatically scans for removable SD cards on both Windows and macOS. Displays volume paths and accurate storage capacity (Total & Free space).
- 💡 **FAT32 Format Checker**: Prevents the dreaded "blind" SD error by strictly checking if the SD card is formatted to FAT32 (32KB cluster). Displays a warning for exFAT/NTFS drives that the 3DS cannot read.
- 🔓 **Luma3DS Auto Installer**: Connects to the GitHub API to fetch and extract the latest Luma3DS v13+ directly to the root of your SD card. No more 404 broken links or outdated files.
- 📁 **Standard Directory Structure**: Automatically generates the essential folder tree (`3ds/`, `cias/`, `luma/payloads`, `Nintendo 3DS/`, etc.).
- 📦 **Essential Homebrew Downloader**: Automatically downloads the must-have toolkit: `FBI`, `Universal-Updater` (hShop), `Anemone3DS`, `Checkpoint`, `FTPD`, and the lifesaver app `Faketik`.
- ⚙️ **Finalize Setup Ready**: Fully integrates the automated Finalize Setup Script. Just insert the SD card into your 3DS, hold `START` on boot, and watch it automatically install all apps to your Home Menu and clean system junk!
- 🕹️ **Bulk Copy 3DS Games**: Select multiple `.cia` or `.3ds` game files directly from the UI and copy them straight into the `cias/` folder of your SD card.
- ✏️ **Safe SD Management**: Built-in FAT32-compliant name changer (Rename) and safe Eject mechanism to prevent data corruption.

## 💻 Installation & Usage

### CLI Version (Command-Line Interface)
The CLI version uses pure standard Python 3 libraries and requires no additional dependencies:
```bash
python3 3ds_toolbox_cli.py
```

### GUI Version (Graphical User Interface)
The GUI version requires the `PyQt6` UI library:
```bash
pip install -r requirements.txt
python3 3ds_toolbox.py
```

> **Note**: For the best experience, it is highly recommended to use an SD card under 64GB formatted to FAT32. For 64GB+ cards, please use tools like GUIFormat to enforce a 32KB cluster size. Enjoy reviving your 3DS! 🌟
