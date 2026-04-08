# MORBION SCADA v01

**Intelligence. Precision. Vigilance.**

A complete virtual Industrial Control System lab — four running industrial
processes, a production SCADA server, and a real-time desktop client.
Built from scratch. 

---

## What This Is

MORBION SCADA v01 is a fully operational virtual ICS lab modelling four
real Kenyan industrial facilities. Every process runs real physics, real
PLC logic, real alarm evaluation, and real Modbus TCP communication.


---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MORBION ICS LAB NETWORK                      │
│                      NETWORK ADDRESS                            │
│                                                                 │
│   PLC VIRTUAL MACHINE  (VIRTUAL MACHINE IP)                     │
│   ├── pumping_station  port 502   Nairobi Water                 │
│   ├── heat_exchanger   port 506   KenGen Olkaria                │
│   ├── boiler           port 507   EABL/Bidco                    │
│   └── pipeline         port 508   Kenya Pipeline Company        │
│                             │                                   │
│                             ▼  Modbus TCP                       │
│   SCADA SERVER VIRTUAL MACHINE (VIRTUAL MACHINE IP)             │
│   ├── MORBION SCADA Server  port 5000  (REST + WebSocket)       │
│   ├── InfluxDB historian    port 8086                           │
│   ├── Grafana dashboards    port 3000                           │
│   ├── RapidSCADA            port 10008                          │
│   └── Mosquitto MQTT        port 1883                           │
│                             │                                   │
│                             ▼  WebSocket / REST                 │
│   SCADA CLIENT VIRTUAL MACHINE (VIRTUAL MACHINE IP)             │
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

---

# MORBION SCADA v01 — Installation Guide

This guide covers three ways to clone and set up the MORBION SCADA v01 repository:

1. **Clone All** — Full installation (all three components)
2. **Clone Selective** — Install only the component you need

---

## Prerequisites

| Requirement | Description |
|---|---|
| Python | 3.8 or higher |
| Network | 'NETWORK ADDRESS'/24 subnet (VMware VMnet1) |
| Git | Installed on your machine |
| sudo/Admin | Required for privileged ports (< 1024) |

---

## Option 1: Clone All Three Components

This downloads the complete repository with all three components: processes, server, and desktop client.

```bash
git clone https://github.com/MORBION-LABS/morbion-scada-v01.git
cd morbion-scada-v01
```

**What you get:**

```
morbion-scada-v01/
├── processes/        # 4 virtual PLC processes (runs on UBUNTU-PLC)
├── server/          # SCADA server (runs on UBUNTU-SCADA)
└── desktop-client/  # PyQt6 client (runs on HOST-ENG)
```

**Next steps:**

- Go to `processes/` → [Set up the PLC processes](#processes-setup)
- Go to `server/` → [Set up the SCADA server](#server-setup)
- Go to `desktop-client/` → [Set up the desktop client](#desktop-client-setup)

---

## Option 2: Clone Only Processes

Use this if you only need the four virtual PLC processes.

```bash
git clone --sparse https://github.com/MORBION-LABS/morbion-scada-v01.git
cd morbion-scada-v01
git sparse-checkout set processes
```

**What you get:**

```
morbion-scada-v01/
└── processes/   # Only the 4 PLC processes
```

**Next steps:** Continue to [Processes Setup](#processes-setup)

---

## Option 3: Clone Only Server

Use this if you only need the SCADA server.

```bash
git clone --sparse https://github.com/MORBION-LABS/morbion-scada-v01.git
cd morbion-scada-v01
git sparse-checkout set server
```

**What you get:**

```
morbion-scada-v01/
└── server/   # Only the SCADA server
```

**Next steps:** Continue to [Server Setup](#server-setup)

---

## Option 4: Clone Only Desktop Client

Use this if you only need the PyQt6 desktop client.

```bash
git clone --sparse https://github.com/MORBION-LABS/morbion-scada-v01.git
cd morbion-scada-v01
git sparse-checkout set desktop-client
```

**What you get:**

```
morbion-scada-v01/
└── desktop-client/   # Only the PyQt6 client
```

**Next steps:** Continue to [Desktop Client Setup](#desktop-client-setup)

---

## <a name="processes-setup"></a>Processes Setup

The four virtual PLC processes run on **UBUNTU-PLC** (192.168.100.20).

### 1. Install Dependencies

```bash
cd processes
sudo apt update
sudo apt install python3-psutil python3-yaml
```

Or if using pip:

```bash
sudo pip3 install psutil pyyaml typer rich --break-system-packages
```

### 2. Run Installer

```bash
sudo python3 installer.py
```

This creates:
- `logs/` directory
- `config.yaml`

### 3. Start All Processes

```bash
sudo python3 manager.py start
```

### 4. Verify Running

```bash
sudo ss -tlnp | grep -E ':(502|506|507|508) '
```

You should see four ports listening:
- 502 — Pumping Station
- 506 — Heat Exchanger
- 507 — Boiler
- 508 — Pipeline

### 5. Check Status

```bash
sudo python3 manager.py status
```

### 6. Stop Processes

```bash
sudo python3 manager.py stop
```

---

## <a name="server-setup"></a>Server Setup

The SCADA server runs on **UBUNTU-SCADA** (192.168.100.30).

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

Required packages: `flask`, `flask-sock`, `requests`

### 2. Configure

Edit `config.json` if needed:

```json
{
  "plc_host": "192.168.100.20",
  "poll_rate_s": 1.0,
  "server_port": 5000
}
```

### 3. Start Server

```bash
python3 main.py --config config.json
```

### 4. Verify Running

```bash
ss -tlnp | grep ':5000'
```

### 5. Test API

```bash
curl http://localhost:5000/health
curl http://localhost:5000/data
```

---

## <a name="desktop-client-setup"></a>Desktop Client Setup

The PyQt6 desktop client runs on **SCADA CLIENT MACHINE** (SCADA CLIENT MACHINE IP).

### 1. Install Dependencies

```bash
cd desktop-client
pip install -r requirements.txt
```

Required packages: `PyQt6`, `websocket-client`, `requests`

### 2. Configure

Edit `config.json` if needed:

```json
{
  "server_host": "SCADA SERVER MACHINE IP",
  "server_port": 5000,
  "ws_reconnect_interval_s": 3,
  "update_rate_ms": 1000
}
```

### 3. Launch Client

```bash
python3 main.py
```

The client will:
- Connect to the SCADA server via WebSocket at `ws://SCADA SERVER MACHINE IP:5000/ws`
- Auto-reconnect if the connection drops
- Display live data from all four processes

---

## Network Overview

```
NETWORK ADDRESS/24 (VMnet1 — Host-Only)

┌─────────────────┐
│  PLC MACHINE   │ PLC IP
│  ─────────────  │
│  pumping_station │ :502
│  heat_exchanger │ :506
│  boiler         │ :507
│  pipeline       │ :508
└────────┬────────┘
         │ Modbus TCP
         ▼
┌─────────────────┐
│ SCADA SERVER   │ SCADA SERVER IP
│  ─────────────  │
│  SCADA Server  │ :5000 (REST + WebSocket)
│  InfluxDB      │ :8086
│  Grafana       │ :3000
│  Mosquitto     │ :1883
└────────┬────────┘
         │ WebSocket / REST
         ▼
┌─────────────────┐
│ CLIENT MACHINE     │ CLIENT IP
│  ─────────────  │
│  Desktop Client │ (PyQt6)
└─────────────────┘
```

---

## Quick Reference

| Component | Location | Port | Command |
|---|---|---|---|
| Pumping Station | PLC MACHINE | 502 | `sudo python3 manager.py start` |
| Heat Exchanger | PLC MACHINE | 506 | `sudo python3 manager.py start` |
| Boiler | PLC MACHINE | 507 | `sudo python3 manager.py start` |
| Pipeline | PLC MACHINE | 508 | `sudo python3 manager.py start` |
| SCADA Server | SCADA SERVER MACHINE| 5000 | `python3 main.py` |
| Desktop Client | SCADA CLIENT MACHINE | — | `python3 main.py` |

---

## Troubleshooting

### Permission Denied (Linux)

Ports below 1024 are privileged. Always use `sudo`:

```bash
sudo python3 manager.py start
```

### psutil Not Found

Install for root user:

```bash
sudo pip3 install psutil --break-system-packages
```

### Processes Not Starting

Check if ports are already in use:

```bash
sudo ss -tlnp | grep -E ':(502|506|507|508) '
```

Kill any existing processes:

```bash
sudo pkill -f "python3.*main.py"
```

### Desktop Client Won't Connect

1. Verify SCADA server is running on UBUNTU-SCADA:
   ```bash
   curl http://SCADA SERVER MACHINE IP:5000/health
   ```

2. Check firewall settings between VMs

3. Verify VMnet1 network connectivity:
   ```bash
   ping "SCADA SERVER IP"
   ```

---

*For detailed documentation on each component, see the README.md inside each folder.*

## Quick Start

### 1. Start the Processes 

```bash
cd processes
sudo python3 manager.py start
sudo python3 manager.py status
```

### 2. Start the SCADA Server

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

Works from any machine on the  network:

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
regs = read('PLC VM IP', 506, 0, 17)
print(regs)
```

---

## Web Interfaces

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://SCADA SERVER VM IP:3000 | admin / admin |
| InfluxDB | http://SCADA SERVER VM IP:8086 | admin / admin123 |
| RapidSCADA | http://SCADA SERVER VM IP:10008 | admin / scada |
| SCADA Server | http://SCADA SERVER VM IP:5000/data | — |

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
