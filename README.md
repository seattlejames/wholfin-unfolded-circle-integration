
# Wholphin Integration for Unfolded Circle Remote 2/3

Control your [Wholphin](https://github.com/damontecres/Wholphin) Android TV player directly from your Unfolded Circle Remote 2 or Remote 3.

## How it works

[Wholphin](https://github.com/damontecres/Wholphin) is an open-source Android TV client for Jellyfin. It connects to your existing Jellyfin media server and registers itself as a client session named **"Wholphin"**.

This integration connects to the **same Jellyfin server** and uses the Jellyfin HTTP Session API to discover and control only the Wholphin sessions — leaving other Jellyfin clients (official app, web browser, etc.) unaffected.

```
UC Remote 3
    │
    │  WebSocket / HTTP
    ▼
uc-intg-wholphin   ──── Jellyfin HTTP API ────►  Jellyfin Server
                                                        │
                                                        │  Session commands
                                                        ▼
                                               Wholphin Android TV App
```

---

## Features

### 🎵 Media Player Control
- **Play / Pause** — seamless playback toggle
- **Stop** — stops current playback
- **Previous / Next** — track / episode navigation
- **Fast Forward / Rewind** — 30-second skip controls
- **Seek** — direct position seek
- **Volume** — set absolute level, step up/down, mute toggle
- **Repeat & Shuffle** — full queue control

### 📺 Now-Playing Information
- Media title, artist, album (for music), series + episode info (for TV)
- High-quality artwork pulled directly from the Jellyfin server
- Playback position and total duration
- Playing / Paused / Stopped state indicators

### 📚 Library Browser & Search
- Browse all Jellyfin libraries (Movies, TV Shows, Music, etc.)
- Full-text search across the entire library

### 🖱️ Remote Control Entity
Full D-Pad navigation — send UI commands directly to the Wholphin app:
- Arrow keys, OK/Select, Back, Home, Menu
- Numeric keypad (0–9)

<img width="440" height="843" alt="PXL_20260616_104444016" src="https://github.com/user-attachments/assets/f7a5455a-fae5-447a-b836-b8644f448ad6" />

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Jellyfin server** | Version 10.10.x or 10.11.x (matching Wholphin's requirements) |
| **Wholphin app** | Installed on an Android TV / Fire TV device, connected to the same Jellyfin server |
| **Network** | UC Remote, Jellyfin server, and Android TV device on the same local network |

> **Important:** The Wholphin app must be open and connected to the Jellyfin server when you run the integration setup, so that active sessions can be discovered. The integration also auto-discovers new Wholphin sessions dynamically.

---

## Installation

### Option 1: Upload to Remote (Recommended)

1. Download the latest `uc-intg-wholphin-<version>-aarch64.tar.gz` from the "Releases" page.
2. Open your remote's web interface: `http://<your-remote-ip>`
3. Go to **Settings → Integrations → Add Integration**
4. Click **Upload** and select the downloaded `.tar.gz` file.

### Option 2: Docker

```yaml
services:
  uc-intg-wholphin:
    image: ghcr.io/seattlejames/uc-intg-wholphin:latest
    container_name: uc-intg-wholphin
    network_mode: host
    volumes:
      - /path/to/config:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

```bash
docker run -d \
  --name uc-intg-wholphin \
  --restart unless-stopped \
  --network host \
  -v wholphin-config:/config \
  -e UC_CONFIG_HOME=/config \
  -e UC_INTEGRATION_INTERFACE=0.0.0.0 \
  -e UC_INTEGRATION_HTTP_PORT=9090 \
  -e PYTHONPATH=/app \
  ghcr.io/YOUR_USERNAME/uc-intg-wholphin:latest
```

---

## Configuration

### Step 1: Prepare

1. Ensure your Jellyfin server is running and reachable.
2. Open the **Wholphin app** on your Android TV / Fire TV device and confirm it is connected to the Jellyfin server.
3. Note your Jellyfin server URL (e.g. `http://192.168.1.100:8096`).

### Step 2: Setup via UC3 Interface

1. After installing, go to **Settings → Integrations**.
2. The Wholphin integration will appear — click **Configure**.
3. Enter:
   - **Jellyfin Server URL** — e.g. `http://192.168.1.100:8096`
   - **Username** — your Jellyfin username
   - **Password** — your Jellyfin password
4. Click **Complete Setup**.

The integration will connect, authenticate, and discover any active Wholphin sessions. Each session appears as a separate media player entity named **"Wholphin (Your Device Name)"**.

> **No Wholphin sessions found?** This just means the app wasn't open at setup time. Sessions are discovered automatically once you open Wholphin and start playing media — no reconfiguration needed.

---

## Using the Integration

### Adding to Activities

1. Go to **Activities** in your remote interface.
2. Create or edit an activity.
3. Add Wholphin entities from **Available Entities**.
4. Configure button mappings and layout as desired.
5. Save the activity.

### Session Discovery

The integration polls the Jellyfin server every **5 seconds**. New Wholphin sessions (e.g. opening the app on a second device) are discovered and added automatically without restarting.

---

## Development Setup

```bash
git clone https://github.com/seattlejames/uc-intg-wholphin.git
cd uc-intg-wholphin

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

export UC_CONFIG_HOME=./config
python -m uc_intg_wholphin
```

The integration listens on `localhost:9090` by default. Configure it with your Jellyfin server details from the UC3 web interface.

---

## Project Structure

```
uc-intg-wholphin/
├── uc_intg_wholphin/
│   ├── __init__.py        # Entry point & main()
│   ├── __main__.py        # Module runner
│   ├── browser.py         # Media library browser & search
│   ├── config.py          # WholphinConfig, WholphinDeviceConfig
│   ├── const.py           # Constants & Wholphin client name filter
│   ├── device.py          # Jellyfin API wrapper (Wholphin session filter)
│   ├── driver.py          # Integration driver (entity orchestration)
│   ├── media_player.py    # Media player UC entity
│   ├── remote.py          # Remote control UC entity
│   ├── sensor.py          # State & Now Playing sensors
│   └── setup_flow.py      # Setup wizard
├── .github/workflows/
│   └── build.yml          # Automated aarch64 + Docker builds
├── lib/
│   └── ucapi-0.6.0-py3-none-any.whl
├── Dockerfile
├── docker-compose.yml
├── driver.json
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Credits & Acknowledgements

- **[Wholphin](https://github.com/damontecres/Wholphin)** — the Android TV Jellyfin client this integration is built for
- **[mase1981/uc-intg-jellyfin](https://github.com/mase1981/uc-intg-jellyfin)** — the Jellyfin integration this project is based on (MPL-2.0)
- **[Unfolded Circle](https://www.unfoldedcircle.com/)** — Remote Two/3 integration framework (ucapi)
- **[Jellyfin](https://jellyfin.org/)** — the media server providing the underlying API

## License

Mozilla Public License 2.0 (MPL-2.0) — see [LICENSE](LICENSE) for details.
