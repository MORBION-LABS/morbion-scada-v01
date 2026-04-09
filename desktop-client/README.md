# MORBION SCADA Desktop Client

Real-time PyQt6 desktop SCADA client for the MORBION virtual ICS lab.
Connects to the MORBION SCADA Server via WebSocket.
Displays live process data across six views with fault injection controls.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Installer (Required First Time)

```bash
python3 installer.py
```

The installer will prompt for:
- **SCADA Server Host IP** — IP address where server runs

### 3. Launch Client

```bash
python3 main.py
```

---

## Views

| View | What It Shows |
|------|---------------|
| Overview | All four processes — live summary, active alarms |
| Pumping Station | Tank level, pump state, flow rates, pressure |
| Heat Exchanger | Hot/cold temperatures, flow rates, efficiency |
| Boiler | Drum pressure, level, temp, steam flow, burner state |
| Pipeline | Inlet/outlet pressure, flow rate, duty/standby status |
| Alarms | Active alarm list with severity, timestamp, source |

All views update in real time regardless of which tab is active.

---

## Architecture

```
main.py
+-- MainWindow (main_window.py)
    +-- WebSocketThread (connection/ws_thread.py)
    |   +-- Auto-reconnecting WebSocket -> SCADA Server
    +-- RESTClient (connection/rest_client.py)
    |   +-- Non-blocking POST /control -> SCADA Server
    +-- Views (views/)
        +-- OverviewView
        +-- PumpingView
        +-- HXView
        +-- BoilerView
        +-- PipelineView
        +-- AlarmsView
```

---

## Widgets

| Widget | Purpose |
|--------|---------|
| gauge_widget.py | Circular gauge — pressure, temperature, level |
| tank_widget.py | Animated tank fill level |
| valve_bar.py | Valve position indicator |
| sparkline_widget.py | Mini trend chart — last N values |
| status_badge.py | Colour-coded process state badge |
| value_label.py | Engineering value with unit label |
| control_panel.py | Fault injection and register write controls |

---

## Configuration

After running `installer.py`, your `config.json` will be updated with your Server IP:

```json
{
  "server": {
    "host": "YOUR_SERVER_HOST_IP",
    "port": 5000
  },
  "ui": {
    "poll_display_ms": 500,
    "sparkline_points": 120,
    "theme": "dark_cyan",
    "window_title": "MORBION SCADA v3.0",
    "window_width": 1600,
    "window_height": 950
  }
}
```

---

## Sending Control Commands

The client sends register writes via the SCADA Server REST API.

```
POST http://YOUR_SERVER_HOST_IP:5000/control
{
  "process": "boiler",
  "register": 2,
  "value": 150
}
```

This sets drum_level to 15% -> triggers LOW_WATER interlock -> burner trips.
Clear by writing 0 to the fault_code register.

---

## Theme

Dark cyan industrial theme defined in theme.py.

| Role | Colour |
|------|--------|
| Background | #0d1117 |
| Surface | #161b22 |
| Accent / Running | #00bcd4 |
| Warning / Alarm | #ff9800 |
| Fault / Trip | #f44336 |
| Stopped / Offline | #424242 |

---

## Troubleshooting

### "server.host not configured in config.json"
Run the installer first:
```bash
python3 installer.py
```

### Client won't connect to server
1. Verify server is running: curl http://YOUR_SERVER_IP:5000/health
2. Check config.json has correct server IP
3. Check firewall allows connection on port 5000

---

## Dependencies

```bash
pip install -r requirements.txt
```

Requirements: PyQt6, websocket-client, requests
