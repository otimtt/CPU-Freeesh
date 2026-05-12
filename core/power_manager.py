"""
Power plan management via powercfg.exe (no extra dependencies).
Saves current plan before switching so it can be restored.
"""

import subprocess
import re
import logging

logger = logging.getLogger(__name__)

HIGH_PERFORMANCE_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
POWER_SAVER_GUID = "a1841308-3541-4fab-bc81-f71556f20b4a"

_KNOWN_PLANS = {
    HIGH_PERFORMANCE_GUID: "High Performance",
    BALANCED_GUID: "Balanced",
    POWER_SAVER_GUID: "Power Saver",
}


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=0x08000000,  # CREATE_NO_WINDOW
    )


def get_active_plan() -> tuple[str, str]:
    """Returns (guid, display_name) of the currently active power plan."""
    try:
        result = _run(["powercfg", "/getactivescheme"])
        match = re.search(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            result.stdout,
            re.IGNORECASE,
        )
        if match:
            guid = match.group(1).lower()
            name_match = re.search(r"\((.+?)\)", result.stdout)
            name = name_match.group(1) if name_match else _KNOWN_PLANS.get(guid, guid)
            return guid, name
    except Exception as e:
        logger.error("get_active_plan: %s", e)
    return BALANCED_GUID, "Balanced"


def set_plan(guid: str) -> bool:
    """Activate a power plan by GUID. Returns True on success."""
    try:
        result = _run(["powercfg", "/s", guid])
        if result.returncode == 0:
            name = _KNOWN_PLANS.get(guid.lower(), guid)
            logger.info("Power plan set to: %s (%s)", name, guid)
            return True
        logger.error("powercfg /s %s failed: %s", guid, result.stderr.strip())
    except Exception as e:
        logger.error("set_plan(%s): %s", guid, e)
    return False


def activate_high_performance() -> bool:
    """Switch to High Performance power plan."""
    return set_plan(HIGH_PERFORMANCE_GUID)


def restore_plan(guid: str) -> bool:
    """Restore a previously saved power plan GUID."""
    return set_plan(guid)


def list_plans() -> list[tuple[str, str]]:
    """Return [(guid, name), ...] for all installed power plans."""
    plans: list[tuple[str, str]] = []
    try:
        result = _run(["powercfg", "/list"])
        for line in result.stdout.splitlines():
            match = re.search(
                r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s+\((.+?)\)",
                line,
                re.IGNORECASE,
            )
            if match:
                plans.append((match.group(1).lower(), match.group(2)))
    except Exception as e:
        logger.error("list_plans: %s", e)
    return plans
