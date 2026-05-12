"""
Process management: list, kill, and reprioritize Windows processes.
All operations are guarded by a whitelist loaded from config/.
"""

import json
import os
import logging
from typing import NamedTuple

import psutil

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "safe_processes.json"
)

# Priority constants (Windows)
PRIORITY_IDLE = psutil.IDLE_PRIORITY_CLASS
PRIORITY_BELOW_NORMAL = psutil.BELOW_NORMAL_PRIORITY_CLASS
PRIORITY_NORMAL = psutil.NORMAL_PRIORITY_CLASS
PRIORITY_ABOVE_NORMAL = psutil.ABOVE_NORMAL_PRIORITY_CLASS
PRIORITY_HIGH = psutil.HIGH_PRIORITY_CLASS
PRIORITY_REALTIME = psutil.REALTIME_PRIORITY_CLASS

PRIORITY_LABELS = {
    PRIORITY_IDLE: "Idle",
    PRIORITY_BELOW_NORMAL: "Below Normal",
    PRIORITY_NORMAL: "Normal",
    PRIORITY_ABOVE_NORMAL: "Above Normal",
    PRIORITY_HIGH: "High",
    PRIORITY_REALTIME: "Realtime",
}


class ProcessInfo(NamedTuple):
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    priority: int
    status: str


def _load_safe_names() -> set[str]:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {n.lower() for n in data.get("critical", [])}
    except Exception as e:
        logger.error("Could not load safe_processes.json: %s", e)
        return set()


_SAFE_NAMES: set[str] = _load_safe_names()


def is_safe_process(name: str) -> bool:
    return name.lower() in _SAFE_NAMES


def get_processes() -> list[ProcessInfo]:
    """Return all non-critical user-space processes with usage stats."""
    result: list[ProcessInfo] = []

    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_info", "nice", "status"]
    ):
        try:
            info = proc.info
            name: str = info["name"] or "unknown"
            if is_safe_process(name):
                continue
            mem_mb = (info["memory_info"].rss / 1_048_576) if info["memory_info"] else 0.0
            result.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=name,
                    cpu_percent=round(info["cpu_percent"] or 0.0, 1),
                    memory_mb=round(mem_mb, 1),
                    priority=info["nice"] or PRIORITY_NORMAL,
                    status=info["status"] or "unknown",
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    result.sort(key=lambda p: p.cpu_percent, reverse=True)
    return result


def set_process_priority(pid: int, priority: int) -> bool:
    """Set priority of a process by PID. Returns True on success."""
    try:
        proc = psutil.Process(pid)
        if is_safe_process(proc.name()):
            logger.warning("Blocked: tried to change priority of safe process %s", proc.name())
            return False
        proc.nice(priority)
        logger.info("Set PID %d (%s) priority to %s", pid, proc.name(), PRIORITY_LABELS.get(priority))
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.error("set_process_priority(%d): %s", pid, e)
        return False


def kill_process(pid: int) -> bool:
    """Terminate a process by PID. Blocked for safe/critical processes."""
    try:
        proc = psutil.Process(pid)
        if is_safe_process(proc.name()):
            logger.warning("Blocked: tried to kill safe process %s (PID %d)", proc.name(), pid)
            return False
        proc.terminate()
        logger.info("Terminated PID %d (%s)", pid, proc.name())
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.error("kill_process(%d): %s", pid, e)
        return False


def lower_background_priorities(excluded_pids: set[int] | None = None) -> int:
    """
    Set all non-critical, non-excluded processes to Below Normal priority.
    Returns the count of processes successfully changed.
    """
    excluded_pids = excluded_pids or set()
    count = 0
    for proc in psutil.process_iter(["pid", "name", "nice"]):
        try:
            info = proc.info
            if is_safe_process(info["name"] or ""):
                continue
            if info["pid"] in excluded_pids:
                continue
            if (info["nice"] or PRIORITY_NORMAL) <= PRIORITY_NORMAL:
                proc.nice(PRIORITY_BELOW_NORMAL)
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    logger.info("Lowered %d background processes to Below Normal", count)
    return count


def restore_normal_priorities() -> int:
    """Reset all non-critical processes back to Normal priority."""
    count = 0
    for proc in psutil.process_iter(["pid", "name", "nice"]):
        try:
            info = proc.info
            if is_safe_process(info["name"] or ""):
                continue
            current = info["nice"] or PRIORITY_NORMAL
            if current != PRIORITY_NORMAL:
                proc.nice(PRIORITY_NORMAL)
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    logger.info("Restored %d processes to Normal priority", count)
    return count
