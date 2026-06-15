#!/usr/bin/env python3
"""
Wholphin Integration for Unfolded Circle Remote Two/3.

Controls the Wholphin Android TV player (https://github.com/damontecres/Wholphin)
via the Jellyfin HTTP API. The integration connects to the Jellyfin server and
targets only sessions whose Client field is "Wholphin" or "Wholphin (Debug)".
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from ucapi_framework import BaseConfigManager, get_config_path

from uc_intg_wholphin.config import WholphinConfig
from uc_intg_wholphin.driver import WholphinDriver
from uc_intg_wholphin.setup_flow import WholphinSetupFlow

logging.getLogger(__name__).addHandler(logging.NullHandler())

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _DRIVER_JSON = str(Path(sys._MEIPASS) / "driver.json")
else:
    _DRIVER_JSON = str(Path(__file__).parent.parent.absolute() / "driver.json")

try:
    with open(_DRIVER_JSON, "r", encoding="utf-8") as f:
        driver_info = json.load(f)
        __version__ = driver_info.get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    __version__ = "0.0.0"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)-40s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
logging.getLogger("jellyfin_apiclient_python").setLevel(logging.INFO)

_LOG = logging.getLogger(__name__)


async def main() -> None:
    _LOG.info("=" * 70)
    _LOG.info("Wholphin Integration v%s (ucapi-framework)", __version__)
    _LOG.info("=" * 70)

    driver = WholphinDriver()

    config_path = get_config_path(driver.api.config_dir_path or "")
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=WholphinConfig,
    )
    driver.config_manager = config_manager

    setup_handler = WholphinSetupFlow.create_handler(driver)
    await driver.api.init(_DRIVER_JSON, setup_handler)

    await driver.register_all_configured_devices(connect=False)

    configs = list(config_manager.all())
    if configs:
        _LOG.info("Connecting %d configured server(s)...", len(configs))
        await driver.connect_devices()
    else:
        _LOG.info("No configured servers — waiting for setup via UC3 web interface")

    await asyncio.Future()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOG.info("Integration stopped by user")
    except Exception as err:
        _LOG.error("Fatal error: %s", err, exc_info=True)
        raise


__all__ = ["__version__", "main", "run"]

if __name__ == "__main__":
    run()
