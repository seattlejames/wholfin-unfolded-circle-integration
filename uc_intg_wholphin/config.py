"""
Configuration for Wholphin integration.

Wholphin is an Android TV client for Jellyfin. This integration connects to
the Jellyfin server and controls only Wholphin client sessions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


def make_device_id(wholphin_device_id: str) -> str:
    """Create a stable short device ID from the Jellyfin session DeviceId."""
    return f"wp_{hashlib.md5(wholphin_device_id.encode()).hexdigest()[:12]}"


@dataclass
class WholphinDeviceConfig:
    """Configuration for a single Wholphin client device (Jellyfin session)."""

    device_id: str          # UC entity identifier (wp_<md5>)
    wholphin_device_id: str  # Jellyfin session DeviceId
    name: str               # Human-readable name (e.g. "Wholphin (Living Room Fire TV)")


@dataclass
class WholphinConfig:
    """Configuration for a Jellyfin server connection used by the Wholphin integration."""

    identifier: str
    name: str
    host: str
    username: str
    password: str
    user_id: str = ""
    server_id: str = ""
    devices: list[WholphinDeviceConfig] = field(default_factory=list)

    def __post_init__(self):
        converted = []
        for device in self.devices:
            if isinstance(device, dict):
                converted.append(WholphinDeviceConfig(**device))
            else:
                converted.append(device)
        self.devices = converted

    def add_device(self, wholphin_device_id: str, name: str) -> str:
        device_id = make_device_id(wholphin_device_id)
        for existing in self.devices:
            if existing.wholphin_device_id == wholphin_device_id:
                existing.name = name
                return device_id
        self.devices.append(WholphinDeviceConfig(
            device_id=device_id,
            wholphin_device_id=wholphin_device_id,
            name=name,
        ))
        return device_id

    def get_device(self, device_id: str) -> WholphinDeviceConfig | None:
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None

    def find_by_wholphin_id(self, wholphin_device_id: str) -> WholphinDeviceConfig | None:
        for device in self.devices:
            if device.wholphin_device_id == wholphin_device_id:
                return device
        return None
