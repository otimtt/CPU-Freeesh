# ⚡ CPU Freeesh

**Game Performance Optimizer for Windows**

CPU Freeesh squeezes every last drop of performance from your PC before you launch a game — and puts everything back exactly as it was when you're done.

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Game Mode** | One-click activation of all optimizations |
| **High Performance Power Plan** | Switches Windows to use maximum CPU/GPU frequency |
| **Service Optimizer** | Pauses background Windows services that waste RAM and CPU |
| **Background Process Throttle** | Lowers priority of all non-game processes |
| **RAM Trim** | Frees physical memory by emptying background process working sets |
| **Process Manager** | Kill or reprioritize any process manually |
| **Full Restore** | Reverts every change — power plan, services, priorities — with one click |
| **Crash-safe Backup** | State is saved to disk before any change, so restore works even after a crash |

---

## 📋 Requirements

- Windows 10 / 11
- Python 3.11+ **or** the pre-built `.exe` (no Python needed)
- Run as **Administrator** (required to change services and process priorities)

---

## 🚀 Quick Start

### Option A — Run from source

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/CPU-Freeesh.git
cd CPU-Freeesh

# 2. Install dependency
pip install -r requirements.txt

# 3. Run (right-click → "Run as administrator", or from an elevated terminal)
python cpu_freeesh.py
```

### Option B — Pre-built executable

1. Download `CPU Freeesh.exe` from the [Releases](../../releases) page.
2. Right-click → **Run as administrator**.
3. Done.

### Build your own `.exe`

```bat
build.bat
```

Requires `pip install pyinstaller` (done automatically by the script).

---

## 🎮 How to Use

1. **Launch** CPU Freeesh as Administrator.
2. *(Optional)* Find your game in the Process Manager → select it → click **↑ High Priority**.
3. Click **ACTIVATE GAME MODE** — done. Play your game.
4. When you're done gaming, click **↩ RESTORE SETTINGS**.

> The restore step brings back your original power plan, restarts any paused services,
> and resets all process priorities. Nothing is permanently changed.

---

## 🛡️ Safety

- **Critical system processes are never touched.** A built-in whitelist (`config/safe_processes.json`) protects `lsass.exe`, `winlogon.exe`, audio services, security tools, and many others.
- **Services are paused, not disabled.** They return to their original state on restore.
- **All changes are backed up** to `cpu_freeesh_backup.json` before anything is modified.
- **No registry edits.** No permanent system modifications.
- **Open source** — you can read every line of code.

---

## ⚙️ Customizing Which Services Are Optimized

Edit `config/optimizable_services.json` to add or remove services from the optimization list.
Each entry has a `name` (Windows service name), `display`, `reason`, and `risk` field.

---

## 🗂️ Project Structure

```
CPU-Freeesh/
├── cpu_freeesh.py          # Entry point (admin check + launch GUI)
├── core/
│   ├── process_manager.py  # List, kill, reprioritize processes
│   ├── power_manager.py    # Switch/restore Windows power plans
│   ├── service_manager.py  # Pause/resume Windows services
│   ├── memory_optimizer.py # Trim working sets to free RAM
│   ├── backup_restore.py   # Snapshot and restore system state
│   └── logger_setup.py     # Rotating file log
├── gui/
│   └── main_window.py      # Full tkinter GUI (dark gaming theme)
├── config/
│   ├── safe_processes.json         # Processes that are never touched
│   └── optimizable_services.json  # Services paused in Game Mode
├── requirements.txt
├── build.bat               # Build standalone .exe with PyInstaller
└── LICENSE
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push and open a Pull Request

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and distribute.

---

> **Disclaimer:** This software modifies Windows system settings temporarily.
> While every precaution has been taken to make it safe, use it at your own risk.
> The authors are not responsible for any issues that may arise.
