from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


WORKSPACE = Path(r"c:\Karart")
MARKER = WORKSPACE / ".cline-reset-result.txt"
LOG_PATH = WORKSPACE / ".cline-reset-log.txt"
CODE_EXE = Path(r"C:\Users\hasan\AppData\Local\Programs\Microsoft VS Code\Code.exe")
STORAGE_BASE = Path(os.environ["APPDATA"]) / "Code" / "User" / "globalStorage"
SOURCE_DIR = STORAGE_BASE / "saoudrizwan.claude-dev"


def write_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def write_marker(message: str) -> None:
    MARKER.write_text(message, encoding="utf-8")


def main() -> int:
    try:
        if MARKER.exists():
            MARKER.unlink()
        if LOG_PATH.exists():
            LOG_PATH.unlink()

        write_log("Python reset worker started.")
        time.sleep(4)

        write_log("Stopping VS Code via taskkill.")
        kill_result = subprocess.run(
            ["taskkill", "/F", "/IM", "Code.exe"],
            capture_output=True,
            text=True,
            check=False,
        )
        write_log(f"taskkill return code: {kill_result.returncode}")
        if kill_result.stdout.strip():
            write_log(f"taskkill stdout: {kill_result.stdout.strip()}")
        if kill_result.stderr.strip():
            write_log(f"taskkill stderr: {kill_result.stderr.strip()}")

        time.sleep(3)

        if SOURCE_DIR.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_dir = STORAGE_BASE / f"saoudrizwan.claude-dev.bak-{stamp}"
            write_log(f"Renaming '{SOURCE_DIR}' -> '{backup_dir}'")
            SOURCE_DIR.rename(backup_dir)
            write_marker(f"OK|{backup_dir}")
        else:
            write_log("Source storage folder not found.")
            write_marker("NOT_FOUND")

        if not CODE_EXE.exists():
            raise FileNotFoundError(f"Code.exe not found: {CODE_EXE}")

        write_log("Reopening VS Code.")
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        subprocess.Popen(
            [str(CODE_EXE), "-r", str(WORKSPACE)],
            creationflags=flags,
            close_fds=True,
        )
        write_log("Python reset worker finished successfully.")
        return 0
    except Exception as exc:  # noqa: BLE001
        write_log(f"ERROR: {exc}")
        write_marker(f"ERROR|{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())