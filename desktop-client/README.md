# MORBION SCADA Desktop Client

PyQt6 desktop client for MORBION SCADA v3.0 industrial control system.

## Requirements

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Or with custom config:
```bash
python main.py --config config.json
```

## Features

- Real-time WebSocket updates from SCADA server
- 6 process views: Overview, Pumping Station, Heat Exchanger, Boiler, Pipeline, Alarms
- Fault injection controls
- Direct register write
- Dark cyan industrial theme

## Architecture

- **WebSocket Thread**: Auto-reconnects on disconnect
- **REST Client**: Non-blocking control commands
- **Views**: All views update in real-time regardless of active tab
