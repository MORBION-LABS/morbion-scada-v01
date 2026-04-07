# MORBION SCADA v01

**Intelligence. Precision. Vigilance.**

A complete virtual Industrial Control System lab — four running industrial
processes, a production SCADA server, and a real-time desktop client.
Built from scratch. No shortcuts.

---

## What This Is

MORBION SCADA v01 is a fully operational virtual ICS lab modelling four
real Kenyan industrial facilities. Every process runs real physics, real
PLC logic, real alarm evaluation, and real Modbus TCP communication.

This is not a simulation framework. It is operational OT infrastructure.
Code here controls running processes. Register writes have physical
consequences. Alarms fire because physical limits are breached.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MORBION ICS LAB NETWORK                      │
│                      192.168.100.0/24                           │
│                                                                  │
│   UBUNTU-PLC  192.168.100.20                                    │
│   ├── pumping_station  port 502   Nairobi Water                 │
│   ├── heat_exchanger   port 506   KenGen Olkaria                │
│   ├── boiler           port 507   EABL/Bidco                    │
│   └── pipeline         port 508   Kenya Pipeline Company        │
│                             │                                    │
│                             ▼  Modbus TCP                        │
│   UBUNTU-SCADA  192.168.100.30                                  │
│   ├── MORBION SCADA Server  port 5000  (REST + WebSocket)       │
│   ├── InfluxDB historian    port 8086                           │
│   ├── Grafana dashboards    port 3000                           │
│   ├── RapidSCADA            port 10008                          │
│   └── Mosquitto MQTT        port 1883                           │
│                             │                                    │
│                             ▼  WebSocket / REST                  │
│   HOST-ENG  192.168.100.10                                      │
│   └── MORBION SCADA Desktop Client  (PyQt6)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
morbion-scada-v01/
├── processes/          Four virtual industrial processes (runs on UBUNTU-PLC)
├── server/             MORBION SCADA Server v1.0 (runs on UBUNTU-SCADA)
└── desktop-client/     PyQt6 Desktop SCADA Client (runs on HOST-ENG)
```

---

## The Four Processes

| Process | Port | Models | Key Physics |
|---|---|---|---|
| Pumping Station | 502 | Nairobi Water | Mass balance, affinity laws |
| Heat Exchanger | 506 | KenGen Olkaria | NTU-effectiveness, energy balance |
| Boiler | 507 | EABL/Bidco | Steam thermodynamics, three-element control |
| Pipeline | 508 | Kenya Pipeline Co. | Darcy-Weisbach, duty/standby logic |

Each process exposes a Modbus TCP server. Each has real PLC scan logic,
real alarm limits, and real fault injection and recovery capability.

---

## Quick Start

### 1. Start the Processes (UBUNTU-PLC)

```bash
cd processes
sudo python3 manager.py start
sudo python3 manager.py status
```

### 2. Start the SCADA Server (UBUNTU-SCADA)

```bash
cd server
python3 main.py --config config.json
```

### 3. Launch the Desktop Client

```bash
cd desktop-client
pip install -r requirements.txt
python3 main.py
```

### 4. Verify All Processes Running

```bash
ss -tlnp | grep -E ':(502|506|507|508) '
```

---

## Reading Live Data

Works from any machine on the 192.168.100.0/24 network:

```python
import socket, struct

def read(host, port, start, count):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((host, port))
    pdu     = struct.pack('>BHH', 0x03, start, count)
    request = struct.pack('>HHHB', 1, 0, 1+len(pdu), 1) + pdu
    s.sendall(request)
    resp = s.recv(256)
    s.close()
    return list(struct.unpack(f'>{count}H', resp[9:9+count*2]))

# Read heat exchanger — 17 registers
regs = read('192.168.100.20', 506, 0, 17)
print(regs)
```

---

## Web Interfaces

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://192.168.100.30:3000 | admin / admin |
| InfluxDB | http://192.168.100.30:8086 | admin / admin123 |
| RapidSCADA | http://192.168.100.30:10008 | admin / scada |
| SCADA Server | http://192.168.100.30:5000/data | — |

---

## Conservation Laws

Every process obeys physical conservation laws at all times.
Sensor manipulation violates them. Violations are detectable in real time.

- **Pumping Station:** `Q_pump × dt = ΔV_tank + Q_demand × dt`
- **Heat Exchanger:** `Q_hot = Q_cold ± 15%`
- **Boiler:** `m_feedwater ≈ m_steam + m_blowdown`
- **Pipeline:** `flow_meter ≈ pump_expected_flow ± 15 m³/hr`

---

## Stack

Python · Modbus TCP (raw sockets) · Flask · WebSocket · PyQt6 ·
InfluxDB · Grafana · Mosquitto MQTT · RapidSCADA

---

*The software manages physical systems and machines.*
*Not users. Not user data. Software meets physics and engineering.*
