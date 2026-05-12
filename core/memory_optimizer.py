"""
RAM optimization: empties the working sets of background processes,
freeing physical memory for the active game.
"""

import ctypes
import ctypes.wintypes
import logging
import psutil

logger = logging.getLogger(__name__)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SET_QUOTA = 0x0100
PROCESS_VM_OPERATION = 0x0008
_ACCESS = PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA | PROCESS_VM_OPERATION

_kernel32 = ctypes.windll.kernel32
_psapi = ctypes.windll.psapi


def _empty_working_set(pid: int) -> bool:
    handle = _kernel32.OpenProcess(_ACCESS, False, pid)
    if not handle:
        return False
    try:
        return bool(_psapi.EmptyWorkingSet(handle))
    finally:
        _kernel32.CloseHandle(handle)


def free_background_ram(game_pids: set[int] | None = None) -> tuple[int, float]:
    """
    Trim working sets of all non-game processes.

    Returns (processes_trimmed, mb_before - mb_after).
    """
    game_pids = game_pids or set()
    before_mb = psutil.virtual_memory().used / 1_048_576
    trimmed = 0

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.pid in game_pids:
                continue
            if proc.pid <= 4:  # System / Idle
                continue
            if _empty_working_set(proc.pid):
                trimmed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    after_mb = psutil.virtual_memory().used / 1_048_576
    freed_mb = max(0.0, before_mb - after_mb)
    logger.info("RAM trim: %d processes, ~%.0f MB freed", trimmed, freed_mb)
    return trimmed, freed_mb


def get_ram_stats() -> dict:
    """Return a dict with total/used/available in MB and percent."""
    vm = psutil.virtual_memory()
    return {
        "total_mb": round(vm.total / 1_048_576),
        "used_mb": round(vm.used / 1_048_576),
        "available_mb": round(vm.available / 1_048_576),
        "percent": vm.percent,
    }
