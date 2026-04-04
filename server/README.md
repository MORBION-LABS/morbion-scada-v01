# MORBION SCADA Server v3.0

**Intelligence. Precision. Vigilance.**

Central SCADA server for the MORBION virtual ICS lab.
Polls 4 critical infrastructure processes via raw Modbus TCP.
Serves live data via REST and WebSocket.
Accepts control commands via POST /control.

## Architecture

```
┌──────────────────┐
│   Flask Server   │  REST + WebSocket
│   (server.py)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   PlantState     │  Thread-safe central state
│  (plant_state.py)│
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│ Poller  │ │ Alarm    │
│(poller) │ │ Engine   │
└────┬───┘ └────┬─────┘
     │          │
     ▼          ▼
┌────────┐ ┌──────────┐
│ Readers│ │ Alarms   │
│ Modbus │ │ (limits) │
└────────┘ └──────────┘
```

## Processes

| Process | Port | Registers | Industry |
|---------|------|-----------|----------|
| Pumping Station | 502 | 15 | Municipal Water |
| Heat Exchanger | 506 | 17 | Geothermal |
| Boiler | 507 | 15 | Industrial Steam |
| Pipeline | 508 | 15 | Petroleum Transfer |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py --config config.json
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Server health & status |
| GET | `/data` | Full plant snapshot |
| GET | `/data/<process>` | Single process data |
| GET | `/data/alarms` | Active alarms list |
| POST | `/control` | Write to PLC register |
| WS | `/ws` | Live WebSocket stream |

## Configuration

Edit `config.json`:

```json
{
  "plc_host": "192.168.100.20",
  "poll_rate_s": 1.0,
  "server_port": 5000,
  "processes": {
    "pumping_station": {"enabled": true, "port": 502},
    "heat_exchanger": {"enabled": true, "port": 506},
    "boiler": {"enabled": true, "port": 507},
    "pipeline": {"enabled": true, "port": 508}
  },
  "influxdb": {"enabled": false}
}
```

## Control Command

```bash
curl -X POST http://localhost:5000/control \
  -H "Content-Type: application/json" \
  -d '{"process": "boiler", "register": 8, "value": 75}'
```

## WebSocket Client

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## License

MIT
