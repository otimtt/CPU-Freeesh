"""
Windows service management for gaming optimization.
Uses sc.exe / net.exe — no pywin32 dependency required.
"""

import subprocess
import json
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "optimizable_services.json"
)


@dataclass
class ServiceEntry:
    name: str
    display: str
    reason: str
    risk: str


def load_optimizable_services() -> list[ServiceEntry]:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return [
            ServiceEntry(
                name=s["name"],
                display=s["display"],
                reason=s["reason"],
                risk=s.get("risk", "low"),
            )
            for s in data.get("services", [])
        ]
    except Exception as e:
        logger.error("Could not load optimizable_services.json: %s", e)
        return []


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=0x08000000,  # CREATE_NO_WINDOW
    )


def get_service_status(service_name: str) -> str:
    """Returns 'running', 'stopped', 'disabled', or 'unknown'."""
    try:
        result = _run(["sc", "query", service_name])
        out = result.stdout.upper()
        if "RUNNING" in out:
            return "running"
        if "STOPPED" in out:
            return "stopped"
        if result.returncode == 1060:
            return "not_found"
        return "unknown"
    except Exception as e:
        logger.error("get_service_status(%s): %s", service_name, e)
        return "unknown"


def stop_service(service_name: str) -> bool:
    """Stop a Windows service. Returns True on success or if already stopped."""
    status = get_service_status(service_name)
    if status in ("stopped", "not_found"):
        return True
    try:
        result = _run(["net", "stop", service_name, "/y"])
        success = result.returncode == 0 or "already" in result.stdout.lower()
        if success:
            logger.info("Stopped service: %s", service_name)
        else:
            logger.warning("Could not stop %s: %s", service_name, result.stderr.strip() or result.stdout.strip())
        return success
    except Exception as e:
        logger.error("stop_service(%s): %s", service_name, e)
        return False


def start_service(service_name: str) -> bool:
    """Start a Windows service. Returns True on success or if already running."""
    status = get_service_status(service_name)
    if status == "running":
        return True
    if status == "not_found":
        return False
    try:
        result = _run(["net", "start", service_name])
        success = result.returncode == 0 or "already" in result.stdout.lower()
        if success:
            logger.info("Started service: %s", service_name)
        else:
            logger.warning("Could not start %s: %s", service_name, result.stderr.strip() or result.stdout.strip())
        return success
    except Exception as e:
        logger.error("start_service(%s): %s", service_name, e)
        return False


def optimize_services() -> dict[str, str]:
    """
    Stop all optimizable services. Returns {name: previous_status} for restore.
    """
    entries = load_optimizable_services()
    backup: dict[str, str] = {}
    for entry in entries:
        status = get_service_status(entry.name)
        backup[entry.name] = status
        if status == "running":
            stop_service(entry.name)
    return backup


def restore_services(backup: dict[str, str]) -> None:
    """Restart services that were running before optimization."""
    for name, previous_status in backup.items():
        if previous_status == "running":
            start_service(name)
