# MORBION SCADA Server v1.0

**Intelligence. Precision. Vigilance.**

Central SCADA server for the MORBION virtual ICS lab.
Polls four industrial processes via raw Modbus TCP.
Serves live process data via REST API and WebSocket.
Runs alarm evaluation and writes to InfluxDB historian.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│           Flask Server (server.py)                │
│           REST API + WebSocket                    │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│        PlantState (plant_state.py)                │
│        Thread-safe central state                  │
└──────────┬──────────────────────┬────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌──────────────────────────┐
│ Poller           │   │ Alarm Engine             │
│ (poller.py)      │   │ (alarm_engine.py)        │
└────────┬─────────┘   └──────────────────────────┘
         │
    ┌────┴───────────────────┐
    ▼                        ▼
┌─────────┐         ┌────────────────┐
│ Readers │         │ Historian     │
│ /readers│         │ /historian    │
└─────────┘         └────────────────┘
    │
    ▼  Modbus TCP (raw sockets)
UBUNTU-PLC 192.168.100.20
ports 502, 506, 507, 508
```

---

## Quick Start

```bash
pip install -r requirements.txt
python3 main.py --config config.json
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API info and version |
| GET | `/health` | Server health and process status |
| GET | `/data` | Full plant snapshot — all four processes |
| GET | `/data/<process>` | Single process data |
| GET | `/data/alarms` | Active alarms list |
| POST | `/control` | Write to a PLC register |
| WS | `/ws` | Live WebSocket stream (1s updates) |

Valid `<process>` values: `pumping_station`, `heat_exchanger`, `boiler`, `pipeline`

---

## Configuration

`config.json`:

```json
{
  "plc_host": "192.168.100.20",
  "poll_rate_s": 1.0,
  "server_port": 5000,
  "processes": {
    "pumping_station": {"enabled": true, "port": 502},
    "heat_exchanger":  {"enabled": true, "port": 506},
    "boiler":          {"enabled": true, "port": 507},
    "pipeline":        {"enabled": true, "port": 508}
  },
  "influxdb": {"enabled": false}
}
```

---

## Sending a Control Command

```bash
curl -X POST http://192.168.100.30:5000/control \
  -H "Content-Type: application/json" \
  -d '{"process": "boiler", "register": 8, "value": 75}'
```

```python
import requests

requests.post('http://192.168.100.30:5000/control', json={
    "process": "heat_exchanger",
    "register": 3,
    "value": 1000    # T_cold_out = 100°C → OVERTEMP alarm
})
```

---

## WebSocket Client

```javascript
const ws = new WebSocket('ws://192.168.100.30:5000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.pumping_station.tank_level_pct);
};
```

```python
import websocket, json

def on_message(ws, message):
    data = json.loads(message)
    print(data['boiler']['drum_pressure'])

websocket.WebSocketApp(
    'ws://192.168.100.30:5000/ws',
    on_message=on_message
).run_forever()
```

---

## Module Structure

```
server/
├── main.py              Entry point
├── server.py            Flask app — REST + WebSocket
├── plant_state.py       Thread-safe central state
├── poller.py            Modbus polling engine
├── alarm_engine.py      Alarm evaluation
├── config.json          Server configuration
├── readers/             Per-process Modbus register readers
│   ├── base.py
│   ├── pumping_station.py
│   ├── heat_exchanger.py
│   ├── boiler.py
│   └── pipeline.py
├── alarms/              Per-process alarm evaluators
│   ├── base.py
│   ├── evaluators.py
│   ├── pumping_station.py
│   ├── heat_exchanger.py
│   ├── boiler.py
│   └── pipeline.py
└── historian/           InfluxDB writer
    ├── client.py
    └── writer.py
```

---

## Example Response

`GET /data/boiler`:

```json
{
  "drum_pressure": 8.02,
  "drum_temp": 170.4,
  "drum_level": 50.3,
  "steam_flow": 3731.0,
  "burner_state": 1,
  "fault_code": 0,
  "alarms": []
}
```

---

## Dependencies

```bash
pip install -r requirements.txt
```

Requirements: `flask`, `flask-sock`, `requests`
