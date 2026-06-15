"""
Setup flow for Wholphin integration.

Connects to the user's Jellyfin server with the provided credentials, then
discovers active Wholphin client sessions to register as controllable devices.
"""

from __future__ import annotations

import logging
import socket
from typing import Any

from jellyfin_apiclient_python import Jellyfin
from jellyfin_apiclient_python.connection_manager import CONNECTION_STATE
from ucapi import RequestUserInput, SetupAction
from ucapi_framework import BaseSetupFlow

from uc_intg_wholphin.config import WholphinConfig
from uc_intg_wholphin.const import WHOLPHIN_CLIENT_NAMES

_LOG = logging.getLogger(__name__)


class WholphinSetupFlow(BaseSetupFlow[WholphinConfig]):

    async def get_pre_discovery_screen(self) -> RequestUserInput | None:
        return self.get_manual_entry_form()

    async def _handle_discovery(self) -> SetupAction:
        if self._pre_discovery_data:
            host = self._pre_discovery_data.get("host")
            username = self._pre_discovery_data.get("username")
            password = self._pre_discovery_data.get("password")

            if not all([host, username, password]):
                return self.get_manual_entry_form()

            try:
                result = await self.query_device(self._pre_discovery_data)
                if hasattr(result, "identifier"):
                    return await self._finalize_device_setup(result, self._pre_discovery_data)
                return result
            except Exception as err:
                _LOG.error("Discovery failed: %s", err)
                return self.get_manual_entry_form()

        return await self._handle_manual_entry()

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "Wholphin / Jellyfin Server Setup"},
            [
                {
                    "id": "host",
                    "label": {"en": "Jellyfin Server URL"},
                    "field": {
                        "text": {
                            "placeholder": "http://192.168.1.100:8096",
                        }
                    },
                },
                {
                    "id": "username",
                    "label": {"en": "Username"},
                    "field": {"text": {"placeholder": "your_username"}},
                },
                {
                    "id": "password",
                    "label": {"en": "Password"},
                    "field": {"password": {}},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> WholphinConfig | RequestUserInput:
        host = (input_values.get("host") or "").strip().rstrip("/")
        username = (input_values.get("username") or "").strip()
        password = (input_values.get("password") or "").strip()

        if not all([host, username, password]):
            return self.get_manual_entry_form()

        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"

        _LOG.info("Validating connection to Jellyfin server at %s ...", host)

        jellyfin = Jellyfin()
        client = jellyfin.get_client()

        try:
            device_name = socket.gethostname()
            client.config.app(
                "Wholphin Integration", "1.0.0", device_name, "wholphin-setup-ucapi"
            )
            client.config.http("Wholphin-Integration/1.0.0")
            client.config.data["auth.ssl"] = host.startswith("https")

            connect_result = client.auth.connect_to_address(host)
            if CONNECTION_STATE(connect_result["State"]) != CONNECTION_STATE.ServerSignIn:
                raise ValueError(f"Cannot reach Jellyfin server at {host}")

            auth_result = client.auth.login(host, username, password)
            if "AccessToken" not in auth_result:
                raise ValueError("Authentication failed — check credentials")

            user_id = auth_result.get("User", {}).get("Id", "")
            if not user_id:
                raise ValueError("Could not determine user ID from login response")
            _LOG.info("Authenticated user_id=%s", user_id)

            server_id = "unknown"
            server_name = "Jellyfin"
            try:
                server_info = client.jellyfin.get_system_info()
                server_id = server_info.get("Id", "unknown")
                server_name = server_info.get("ServerName", "Jellyfin")
            except Exception:
                try:
                    pub_info = client.jellyfin.get_public_info()
                    server_id = pub_info.get("Id", "unknown")
                    server_name = pub_info.get("ServerName", "Jellyfin")
                except Exception:
                    _LOG.warning("Could not retrieve server info during setup")

            config_id = f"wholphin_{server_id[:12]}".lower()

            config = WholphinConfig(
                identifier=config_id,
                name=f"Wholphin ({server_name})",
                host=host,
                username=username,
                password=password,
                user_id=user_id,
                server_id=server_id,
            )

            # Discover active Wholphin sessions on this server
            try:
                all_sessions = client.jellyfin.sessions()
                _LOG.info("Total Jellyfin sessions: %d", len(all_sessions or []))

                for s in (all_sessions or []):
                    _LOG.debug(
                        "Session: Client=%s, DeviceId=%s, DeviceName=%s, "
                        "UserId=%s, NowPlaying=%s",
                        s.get("Client"), s.get("DeviceId"), s.get("DeviceName"),
                        s.get("UserId"), bool(s.get("NowPlayingItem")),
                    )

                wholphin_sessions = [
                    s for s in (all_sessions or [])
                    if s.get("UserId") == user_id
                    and s.get("DeviceId") != "wholphin-setup-ucapi"
                    and s.get("Client") in WHOLPHIN_CLIENT_NAMES
                ]

                if not wholphin_sessions:
                    _LOG.info(
                        "No active Wholphin sessions found. Make sure the Wholphin app "
                        "is open and connected to this Jellyfin server. Sessions will be "
                        "discovered automatically when Wholphin starts playback."
                    )

                for session in wholphin_sessions:
                    wp_device_id = session.get("DeviceId", "")
                    if not wp_device_id:
                        continue
                    client_name = session.get("Client", "Wholphin")
                    device_name_s = session.get("DeviceName", "")
                    # e.g. "Wholphin (Living Room Fire TV)"
                    if device_name_s and device_name_s != client_name:
                        name = f"{client_name} ({device_name_s})"
                    else:
                        name = client_name
                    config.add_device(wp_device_id, name)

                _LOG.info("Discovered %d Wholphin device(s)", len(config.devices))

            except Exception as err:
                _LOG.warning("Wholphin session discovery failed during setup: %s", err)

            return config

        except Exception as err:
            _LOG.error("Setup validation failed: %s", err)
            raise ValueError(f"Setup failed: {err}") from err

        finally:
            try:
                if hasattr(client, "stop"):
                    client.stop()
            except Exception:
                pass
