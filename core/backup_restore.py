"""
Snapshot and restore of system state (power plan + services + priorities).
State is persisted to a JSON file so it survives crashes.
"""

import json
import os
import logging
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

_BACKUP_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "cpu_freeesh_backup.json"
)


@dataclass
class SystemSnapshot:
    power_plan_guid: str = ""
    power_plan_name: str = ""
    services: dict[str, str] = field(default_factory=dict)  # {name: previous_status}
    priorities_lowered: bool = False

    def is_valid(self) -> bool:
        return bool(self.power_plan_guid)


def save(snapshot: SystemSnapshot) -> None:
    try:
        with open(_BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(snapshot), f, indent=2)
        logger.info("Backup saved to %s", _BACKUP_FILE)
    except Exception as e:
        logger.error("save backup: %s", e)


def load() -> SystemSnapshot | None:
    if not os.path.exists(_BACKUP_FILE):
        return None
    try:
        with open(_BACKUP_FILE, encoding="utf-8") as f:
            data = json.load(f)
        snap = SystemSnapshot(**data)
        return snap if snap.is_valid() else None
    except Exception as e:
        logger.error("load backup: %s", e)
        return None


def clear() -> None:
    try:
        if os.path.exists(_BACKUP_FILE):
            os.remove(_BACKUP_FILE)
            logger.info("Backup cleared")
    except Exception as e:
        logger.error("clear backup: %s", e)


def has_backup() -> bool:
    return os.path.exists(_BACKUP_FILE)
