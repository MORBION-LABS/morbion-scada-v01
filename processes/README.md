# MORBION Processes

Four virtual industrial processes modelling real Kenyan infrastructure.
Each runs real physics, real PLC logic, real alarm evaluation, and a
raw-socket Modbus TCP server. No pymodbus. No shortcuts.

---

## Processes

| Process | Port | Models | Steady State |
|---|---|---|---|
| Pumping Station | 502 | Nairobi Water Municipal Pumping | Level 20–80%, flow 120 m³/hr |
| Heat Exchanger | 506 | KenGen Olkaria Geothermal Recovery | T_cold_out ~75°C, efficiency ~80% |
| Boiler | 507 | EABL/Bidco Industrial Steam Plant | Drum 8 bar, level 50%, steam 3733 kg/hr |
| Pipeline | 508 | Kenya Pipeline Co. Petroleum Transfer | Outlet ~40 bar, flow ~450 m³/hr |

---

## Architecture — Every Process

```
process_name/
├── equipment_1.py      Physical component — owns its state and physics
├── equipment_n.py      Physical component — owns its state and physics
├── plc_logic.py        PLC scan cycle — control, alarms, interlocks
├── modbus_server.py    Pure socket Modbus TCP server
├── process_state.py    Thread-safe central state dataclass
├── process_state.json  Persistence — save on stop, restore on start
├── config.json         All parameters — never hardcoded
├── main.py             Orchestrator — scan loop, shutdown handler
├── installer.py        
├── start.sh            setsid launch + log attach
└── stop.sh             pkill by name + port verification
```

Code style: classes only. No globals. Each equipment class owns its state.
All parameters live in `config.json`. Nothing is hardcoded.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run installer (creates logs/ and config.yaml)
sudo python3 installer.py

# Start all four processes
sudo python3 manager.py start

# Check status
sudo python3 manager.py status

# Follow logs live
sudo python3 manager.py logs -f

# Stop all
sudo python3 manager.py stop
```

> **Note:** Ports 502, 506, 507, 508 are privileged on Linux. `sudo` is required.

---

## Manager Commands

| Command | Description |
|---|---|
| `sudo python3 manager.py start` | Start all 4 processes |
| `sudo python3 manager.py stop` | Stop all 4 processes |
| `sudo python3 manager.py restart` | Restart all 4 processes |
| `sudo python3 manager.py status` | Show status of all processes |
| `sudo python3 manager.py logs` | Show last 50 lines of logs |
| `sudo python3 manager.py logs -f` | Follow logs live (Ctrl+C to exit) |

---

## Individual Process Control

```bash
cd pumping_station && sudo bash start.sh
cd heat_exchanger  && sudo bash start.sh
cd boiler          && sudo bash start.sh
cd pipeline        && sudo bash start.sh

cd pumping_station && sudo bash stop.sh
cd heat_exchanger  && sudo bash stop.sh
cd boiler          && sudo bash stop.sh
cd pipeline        && sudo bash stop.sh
```

---

## Register Maps

### Pumping Station (port 502)

| Register | Tag | Scale | Units |
|---|---|---|---|
| 40001 | tank_level_pct | ×10 | % |
| 40002 | tank_volume_m3 | ×10 | m³ |
| 40003 | pump_speed_rpm | ×1 | RPM |
| 40004 | pump_flow_m3hr | ×10 | m³/hr |
| 40005 | discharge_pressure | ×100 | bar |
| 40006 | pump_current_A | ×10 | A |
| 40007 | pump_power_kW | ×10 | kW |
| 40008 | pump_running | — | 0/1 |
| 40009 | inlet_valve_pos | ×10 | % |
| 40010 | outlet_valve_pos | ×10 | % |
| 40011 | demand_flow_m3hr | ×10 | m³/hr |
| 40012 | net_flow_m3hr | ×10 | m³/hr |
| 40013 | pump_starts_today | ×1 | count |
| 40014 | level_sensor_mm | ×1 | mm |
| 40015 | fault_code | — | 0=OK 1=HIGH 2=LOW 3=PUMP 4=DRY_RUN |

### Heat Exchanger (port 506)

| Register | Tag | Scale | Units |
|---|---|---|---|
| 40001 | T_hot_in | ×10 | °C |
| 40002 | T_hot_out | ×10 | °C |
| 40003 | T_cold_in | ×10 | °C |
| 40004 | T_cold_out | ×10 | °C |
| 40005 | flow_hot | ×10 | L/min |
| 40006 | flow_cold | ×10 | L/min |
| 40007 | pressure_hot_in | ×100 | bar |
| 40008 | pressure_hot_out | ×100 | bar |
| 40009 | pressure_cold_in | ×100 | bar |
| 40010 | pressure_cold_out | ×100 | bar |
| 40011 | Q_duty_kW | ×1 | kW |
| 40012 | efficiency | ×10 | % |
| 40013 | hot_pump_speed | ×1 | RPM |
| 40014 | cold_pump_speed | ×1 | RPM |
| 40015 | hot_valve_pos | ×10 | % |
| 40016 | cold_valve_pos | ×10 | % |
| 40017 | fault_code | — | 0=OK 1=PUMP 2=SENSOR 3=OVERTEMP |

### Boiler (port 507)

| Register | Tag | Scale | Units |
|---|---|---|---|
| 40001 | drum_pressure | ×100 | bar |
| 40002 | drum_temp | ×10 | °C |
| 40003 | drum_level | ×10 | % |
| 40004 | steam_flow | ×10 | kg/hr |
| 40005 | feedwater_flow | ×10 | kg/hr |
| 40006 | fuel_flow | ×10 | kg/hr |
| 40007 | burner_state | — | 0=OFF 1=LOW 2=HIGH |
| 40008 | fw_pump_speed | ×1 | RPM |
| 40009 | steam_valve_pos | ×10 | % |
| 40010 | fw_valve_pos | ×10 | % |
| 40011 | blowdown_valve_pos | ×10 | % |
| 40012 | flue_gas_temp | ×10 | °C |
| 40013 | combustion_efficiency | ×10 | % |
| 40014 | Q_burner_kW | ×1 | kW |
| 40015 | fault_code | — | 0=OK 1=LOW_WATER 2=OVERPRESSURE 3=FLAME_FAILURE 4=PUMP_FAULT |

### Pipeline (port 508)

| Register | Tag | Scale | Units |
|---|---|---|---|
| 40001 | inlet_pressure | ×100 | bar |
| 40002 | outlet_pressure | ×100 | bar |
| 40003 | flow_rate | ×10 | m³/hr |
| 40004 | duty_pump_speed | ×1 | RPM |
| 40005 | duty_pump_current | ×10 | A |
| 40006 | duty_pump_running | — | 0/1 |
| 40007 | standby_pump_speed | ×1 | RPM |
| 40008 | standby_pump_running | — | 0/1 |
| 40009 | inlet_valve_pos | ×10 | % |
| 40010 | outlet_valve_pos | ×10 | % |
| 40011 | pump_differential | ×100 | bar |
| 40012 | flow_velocity | ×100 | m/s |
| 40013 | duty_pump_power_kW | ×1 | kW |
| 40014 | leak_flag | — | 0=OK 1=SUSPECTED |
| 40015 | fault_code | — | 0=OK 1=DUTY 2=BOTH 3=OVERPRESSURE |

---

## Fault Injection

```python
import socket, struct

def write(host, port, reg_index, value):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect((host, port))
    pdu = struct.pack('>BHH', 0x06, reg_index, value)
    req = struct.pack('>HHHB', 1, 0, 1+len(pdu), 1) + pdu
    s.sendall(req)
    s.recv(256)
    s.close()

# Heat Exchanger — inject OVERTEMP
write('PLC MACHINE IP', 506, 3, 1000)   # T_cold_out = 100°C
write('PLC MACHINE IP', 506, 16, 0)     # Clear fault

# Boiler — trip on low water
write('PLC MACHINE IP', 507, 2, 150)    # drum_level = 15%
write('PLC MACHINE IP', 507, 14, 0)     # Clear fault

# Pumping Station — high level alarm
write('PLC MACHINE IP', 502, 0, 920)    # tank_level = 92%
write('PLC MACHINE IP', 502, 14, 0)     # Clear fault

# Pipeline — outlet overpressure
write('PLC MACHINE IP', 508, 1, 5600)   # outlet = 56 bar
write('PLC MACHINE IP', 508, 14, 0)     # Clear fault
```

---

## Physics

**Pumping Station:** 
'''
Q_pump × dt = ΔV_tank + Q_demand × dt
'''

**Heat Exchanger:**

```
Q_hot  = m_hot  × Cp_hot  × (T_hot_in  - T_hot_out)
Q_cold = m_cold × Cp_cold × (T_cold_out - T_cold_in)
Q_hot must equal Q_cold within ±15%
m = flow_lpm / 60.0  [L/min → kg/s]
```

**Boiler:**

```
Q_burner = m_fuel × LHV × η  = 2,125 kW at rated
m_steam  = Q_burner / h_fg   = 3,733 kg/hr at rated
T_sat(P) = 100 + 28.6 × ln(P)  [P in bar]
```

**Pipeline:**

```
outlet_P = inlet_P + pump_head - friction_loss - elevation_loss
         = 2.0 + 46.0 - 5.2 - 0.4 = ~42 bar
flow discrepancy > 15 m³/hr → leak_flag activates
```

---

## Troubleshooting

**Permission denied on start**

```bash
sudo python3 manager.py start
```

**Manager says not running but port is listening**

```bash
ss -tlnp | grep -E ':(502|506|507|508) '
sudo pkill -f "python3.*main.py"
sudo python3 manager.py start
```

**Verify specific process**

```bash
ss -tlnp | grep ':506 '
```

---

## Dependencies

```bash
pip install -r requirements.txt
# or
sudo apt install python3-psutil python3-yaml
```

Requirements: `pyyaml`, `psutil`, `typer`, `rich`
