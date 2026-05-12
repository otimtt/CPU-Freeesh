"""
CPU Freeesh — Game Performance Optimizer for Windows
Entry point: admin-check then launches the GUI.
"""

import sys
import ctypes
import os


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
    )


def main() -> None:
    if not is_admin():
        relaunch_as_admin()
        sys.exit(0)

    # Ensure working directory is the script directory so relative paths work.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    from gui.main_window import MainWindow

    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
