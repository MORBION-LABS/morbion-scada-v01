================================================================================
MORBION ICS LAB — COMPLETE REFERENCE
Virtual Industrial Control Systems Laboratory
================================================================================

PHILOSOPHY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This lab is not a teaching aid. It is operational OT infrastructure.

Every language phase — Python, C, C#, C++, Bash, PowerShell, Batch,
Assembly — is learned by operating, controlling, breaking, and recovering
real running industrial processes.

The code has physical consequence. Even in simulation.
A register write changes something in a running process.
An alarm fires because a physical limit was breached.
A recovery script brings a process back from fault state.

This is what separates OT programming from generic programming.
The software manages physical systems and machines.
Not users. Not user data. Software meets physics and engineering.

LAB RULE — ALL PHASES:
    Data comes from real lab processes. Always.
    Actions are taken against real lab processes. Always.
    Observations are made on real lab responses. Always.
    No invented data. No placeholder values. No fake sensors.

WHAT A SESSION LOOKS LIKE:

    Topic: Any language mechanic (loops, functions, classes, threads...)

    Step 1 — Pull live data from a running process
              Read registers via Modbus TCP
              Get real values. Real timestamps. Real physics.

    Step 2 — Apply the mechanic to that real data
              The language concept demonstrated on live process data
              Not invented numbers. Not a textbook example.

    Step 3 — Command the process
              Write to a register. Change a setpoint. Open a valve.
              The process responds. Temperatures shift. Flows change.

    Step 4 — Break the process
              Inject a fault. Force a limit breach. Starve a flow.
              The PLC alarm logic fires. Fault code changes. Alarm activates.

    Step 5 — Recover the process
              Write the recovery code. Clear the fault. Restore setpoints.
              Verify: process returns to steady state. Fault code = 0.

    This is every topic. Every language. Always operational.

================================================================================
NETWORK ARCHITECTURE
================================================================================

    VMware Workstation Pro — Host: Windows 11 Pro

    VMnet8  NAT          — internet access (installs/updates only)
    VMnet1  Host-Only    — OT lab network 192.168.100.0/24

    HOST-ENG     192.168.100.10   Windows 11 — engineering workstation
    UBUNTU-PLC   192.168.100.20   Ubuntu Server — all virtual processes
    UBUNTU-SCADA 192.168.100.30   Ubuntu Server — SCADA/historian/broker
    CyphyOS      192.168.100.40   Attack platform (security phases only)
    ControlThings 192.168.100.50  ICS security research (security phases only)

================================================================================
PROCESSES DIRECTORY STRUCTURE
================================================================================

morbion_processes/
├── pumping_station/        # Process 1 - Nairobi Water Municipal Pumping
├── heat_exchanger/         # Process 2 - KenGen Olkaria Geothermal Heat Recovery
├── boiler/                 # Process 3 - EABL/Bidco Industrial Steam Generation
├── pipeline/               # Process 4 - Kenya Pipeline Co. Petroleum Transfer
├── logs/                   # Created by installer.py
├── config.yaml             # Central configuration (all 4 processes)
├── manager.py              # Central ProcessManager (OOP) - start/stop/status all
├── installer.py            # Central Installer (OOP) - setup + optional services
├── uninstaller.py          # Central Uninstaller (OOP) - cleanup
├── test_communication.py  # CLI monitor/test tool (Typer + Rich)
└── requirements.txt       # Dependencies: pyyaml, psutil, typer, rich

================================================================================
CENTRAL MANAGER — manager.py
================================================================================

OOP Design:
    class Process
        - name: str
        - port: int
        - path: str
        - pid: int | None
        - start() -> bool
        - stop() -> bool
        - is_running() -> bool

    class ProcessManager
        - processes: list[Process]
        - load_pids() / save_pids()
        - start_all() -> dict
        - stop_all() -> dict
        - status() -> dict
        - logs(tail_lines, follow) -> None

Commands:
    python manager.py start      # Start all 4 processes
    python manager.py stop       # Stop all 4 processes
    python manager.py restart    # Restart all 4 processes
    python manager.py status     # Show status of all processes
    python manager.py logs       # Show last 50 lines
    python manager.py logs -f    # Follow logs live (Ctrl+C)

IMPORTANT - Linux Requirements:
    - Ports below 1024 are privileged. Use sudo:
        sudo python3 manager.py start
        sudo python3 manager.py stop
    - Install psutil for root:
        sudo pip3 install psutil
    - Manager scans by port - no PID file needed

================================================================================
INSTALLER — installer.py
================================================================================

OOP Design:
    class ConfigManager
        - load() / save()
        - get_process_config(name) -> dict
        - ensure_config_exists()

    class ServiceManager
        - install_services()  # Windows Services or systemd
        - remove_services()
        - is_service_installed(name) -> bool

    class Installer
        - install(basic=True, services=False)
        - create_logs_directory()
        - create_config()

Basic Installation:
    python installer.py
    Creates: logs/, config.yaml

With System Services:
    sudo python installer.py --services     # Linux
    python installer.py --services          # Windows (Admin)

================================================================================
UNINSTALLER — uninstaller.py
================================================================================

OOP Design:
    class Uninstaller
        - uninstall(remove_services=True, remove_logs=True, remove_config=True)
        - stop_processes()
        - remove_services()
        - remove_logs()
        - remove_config()

Usage:
    python uninstaller.py              # Full cleanup
    python uninstaller.py --no-services # Keep services
    python uninstaller.py --no-logs    # Keep logs
    python uninstaller.py --no-config  # Keep config

================================================================================
TEST COMMUNICATION — test_communication.py
================================================================================

CLI tool using Typer + Rich for beautiful terminal UI.

Commands:
    python test_communication.py monitor     # Continuous monitor
    python test_communication.py monitor -1  # Run once and exit
    python test_communication.py status     # Quick status check
    python test_communication.py test        # Test connectivity

Options:
    -i, --interval INT   Update interval (default: 2s)
    -1, --once           Run once and exit

================================================================================
BACKWARD COMPATIBILITY
================================================================================

Each process folder still has its own start.sh and stop.sh:

    cd pumping_station
    ./start.sh    # Start just pumping station
    ./stop.sh     # Stop just pumping station

Individual process control independent of central manager.

================================================================================
VIRTUAL PROCESSES — COMPLETE INVENTORY
================================================================================

All processes run on UBUNTU-PLC (192.168.100.20).
Each process is completely independent.
Each exposes a Modbus TCP server on its own port.
Each has its own physics, its own PLC logic, its own alarm system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROCESS 1 — PUMPING STATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Path:     processes/pumping_station/
Port:     502
Models:   Nairobi Water — municipal water pumping station
Style:    Classes, config.json, full physics

What this process does:
    Pump draws water from source.
    Fills elevated storage tank.
    Community demand continuously draws from tank.
    PLC starts pump when level drops below 20%.
    PLC stops pump when level rises above 80%.
    Tank cycles continuously — fill, drain, fill, drain.
    Dry run protection trips pump if no flow while running.

Equipment:
    pump.py              Centrifugal pump — affinity laws (Q∝N H∝N² P∝N³)
    tank.py              Storage tank — mass balance (dV/dt = Q_in - Q_out)
    inlet_valve.py       Inlet isolation — on/off motorized
    outlet_valve.py      Outlet control — modulating to distribution
    flow_meter.py        Electromagnetic flow meter — discharge line
    level_sensor.py      Ultrasonic level sensor — tank top mount
    pressure_sensor.py   Pressure transmitter — pump discharge
    plc_logic.py         PLC — level control, dry run protection, alarms
    process_state.py     Central shared state — thread-safe dataclass
    process_state.json   Persistence — save on stop, restore on start
    config.json          All parameters — customizable without code
    main.py              Orchestrator — scan loop, shutdown handler
    start.sh             setsid launch, log attach, Ctrl+C detaches safely
    stop.sh              pkill by name, port-based verification

Physics:
    Tank mass balance:   dV/dt = Q_in × inlet_pos - Q_demand × outlet_pos
    Pump affinity:       Q∝N   H∝N²   P∝N³
    System curve:        H_system = H_static + H_friction (Darcy-Weisbach)
    Friction loss:       dH = f × (L/D) × (v²/2g)
    Conservation law:    Q_pump × dt = ΔV + Q_demand × dt
                         Violation = leak or sensor manipulation

Operating parameters:
    Tank volume:         50.3 m³  (4m diameter × 4m height)
    Normal level:        50%      (20-80% operating band)
    Pump flow:           120 m³/hr at 1450 RPM
    Demand flow:         60 m³/hr (constant community draw)
    Net fill rate:       60 m³/hr when pump running
    Static head:         25 m     (tank elevation)
    Total head:          60 m     (static + friction at rated flow)
    Pump power:          27.2 kW  at rated conditions

Register map (port 502):
    40001  tank_level_pct        % × 10
    40002  tank_volume_m3        m³ × 10
    40003  pump_speed_rpm        RPM
    40004  pump_flow_m3hr        m³/hr × 10
    40005  discharge_pressure_bar bar × 100
    40006  pump_current_A        A × 10
    40007  pump_power_kW         kW × 10
    40008  pump_running          0/1
    40009  inlet_valve_pos_pct   % × 10
    40010  outlet_valve_pos_pct  % × 10
    40011  demand_flow_m3hr      m³/hr × 10
    40012  net_flow_m3hr         m³/hr × 10
    40013  pump_starts_today     count
    40014  level_sensor_mm       mm
    40015  fault_code            0=OK 1=HIGH_LEVEL 2=LOW_LEVEL
                                 3=PUMP_FAULT 4=DRY_RUN

Alarm limits:
    Level high:          90%  — pump stop, outlet restriction
    Level low:           10%  — critical, restrict demand
    Level low-low:        5%  — dry run risk
    No flow on run:     <5 m³/hr for >10s — dry run trip
    Pressure high:        8 bar — overpressure

PLC control logic:
    Pump START when:    level < 20%  AND  no active fault
    Pump STOP when:     level > 80%  OR  high level alarm
    Dry run trip:       flow < 5 m³/hr for 10s while running
    Outlet valve:       85% normal, 20% on high alarm, 0% on low-low

Operational commands (FC06 writes):
    Force pump start:    write 1 to register 40008
    Force pump stop:     write 0 to register 40008
    Change setpoint:     write to outlet_valve_pos (40010)
    Inject level fault:  write value to 40001 (scale ×10)
    Clear fault:         write 0 to 40015

Conservation law (physics-based detection target):
    Q_pump × dt = ΔV_tank + Q_demand × dt
    Manipulate level sensor → mass balance breaks
    Detection fires within one scan cycle

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROCESS 2 — HEAT EXCHANGER STATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Path:     processes/heat_exchanger/
Port:     506
Models:   KenGen Olkaria — geothermal heat recovery station
Style:    Classes, config.json, full physics

What this process does:
    Hot geothermal brine (180°C) enters shell side.
    Cold feedwater (25°C) enters tube side — counter-flow.
    Heat transfers through tube walls.
    Brine exits cooled (~107°C) — returned to geothermal well.
    Feedwater exits heated (~75°C) — to steam generation.
    Two pumps drive circulation on each side.
    Two control valves modulate flow rates.
    PLC monitors temperatures, efficiency, and alarms.

Equipment:
    shell_and_tube.py    Heat exchanger unit — NTU-effectiveness method
    hot_pump.py          Hot side pump — geothermal brine circuit
    cold_pump.py         Cold side pump — feedwater circuit
    control_valve.py     Hot and cold side control valves
    plc_logic.py         PLC — pump control, valve positioning, alarms
    process_state.py     Central shared state
    process_state.json   Persistence
    config.json          All parameters
    main.py              Orchestrator
    start.sh / stop.sh

Physics:
    Energy balance:   Q = m_hot × Cp_hot × (T_hot_in - T_hot_out)
                      Q = m_cold × Cp_cold × (T_cold_out - T_cold_in)
                      Both must be equal — violation = sensor manipulation
    NTU method:       NTU = U × A / C_min
    Effectiveness:    ε = (1-exp(-NTU(1-Cr))) / (1-Cr×exp(-NTU(1-Cr)))
    Mass flow:        m = flow_lpm / 60.0  [L/min → kg/s]
    Pump affinity:    Q∝N   H∝N²   P∝N³
    Valve flow:       Q = Cv × √(ΔP/SG)

Config parameters:
    U = 850 W/m²·K    A = 36.3 m²    U×A = 30,875 W/K
    Cp_hot  = 3800 J/kg·K  (geothermal brine)
    Cp_cold = 4186 J/kg·K  (water)
    tau_thermal = 45s  (thermal lag — slow temperature response)

Steady state targets:
    T_hot_in   = 180°C    T_hot_out  = 100-120°C
    T_cold_in  =  25°C    T_cold_out =  70-85°C
    efficiency = 75-85%   fault_code = 0

Register map (port 506):
    40001  T_hot_in           °C × 10
    40002  T_hot_out          °C × 10
    40003  T_cold_in          °C × 10
    40004  T_cold_out         °C × 10
    40005  flow_hot           L/min × 10
    40006  flow_cold          L/min × 10
    40007  pressure_hot_in    bar × 100
    40008  pressure_hot_out   bar × 100
    40009  pressure_cold_in   bar × 100
    40010  pressure_cold_out  bar × 100
    40011  Q_duty_kW          kW
    40012  efficiency         % × 10
    40013  hot_pump_speed     RPM
    40014  cold_pump_speed    RPM
    40015  hot_valve_pos      % × 10
    40016  cold_valve_pos     % × 10
    40017  fault_code         0=OK 1=PUMP 2=SENSOR 3=OVERTEMP

Alarm limits:
    T_hot_out high:    160°C
    T_cold_out high:    95°C — triggers OVERTEMP fault
    Efficiency low:     60%  — fouling indicator

PLC control logic:
    Start both pumps at config setpoint RPM
    Maintain hot valve at 80% setpoint
    Maintain cold valve at 75% setpoint
    OVERTEMP: any outlet temp above limit → fault_code = 3
    PUMP_FAULT: either pump fails → fault_code = 1

Operational commands (FC06 writes):
    Inject OVERTEMP:     write 1000 to 40004 (T_cold_out = 100°C)
    Inject pump fault:   write 1 to fault_code register 40017
    Close cold valve:    write 0 to 40016
    Change pump speed:   write RPM value to 40013 or 40014
    Clear fault:         write 0 to 40017

Conservation law (physics-based detection target):
    Q_hot = m_hot × Cp_hot × (T_hot_in - T_hot_out)
    Q_cold = m_cold × Cp_cold × (T_cold_out - T_cold_in)
    Q_hot must equal Q_cold within tolerance
    Manipulate T_cold_out → energy imbalance detected immediately

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROCESS 3 — BOILER STEAM GENERATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Path:     processes/boiler/
Port:     507
Models:   EABL/Bidco — industrial steam generation
Style:    Classes, config.json, full physics

What this process does:
    Natural gas burner fires at LOW or HIGH state.
    Heat releases into water in steam drum.
    Water heats to saturation temperature at drum pressure.
    Steam forms in drum — exits through steam outlet valve.
    Feedwater pump continuously replaces steam lost.
    Three-element control maintains drum level.
    Periodic blowdown removes concentrated water.
    Safety interlocks trip burner on low water or overpressure.

Equipment:
    burner.py            Natural gas burner — fuel to heat release
    drum.py              Steam drum — mass and energy balance
    feedwater_pump.py    Feedwater pump — affinity laws
    steam_valve.py       Steam outlet control valve
    feedwater_valve.py   Feedwater control valve — three-element
    blowdown_valve.py    Bottom blowdown — periodic water quality
    plc_logic.py         PLC — three-element control, safety interlocks
    process_state.py     Central shared state
    process_state.json   Persistence
    config.json          All parameters
    main.py              Orchestrator
    start.sh / stop.sh

Physics:
    Burner:       Q_burner = m_fuel × LHV × η_combustion
                  = 0.05 kg/s × 50,000 kJ/kg × 0.85 = 2,125 kW
    Steam:        m_steam = Q_burner / h_fg
                  = 2,125 / 2,048 = 1.037 kg/s = 3,733 kg/hr
    Saturation:   T_sat(P) = 100 + 28.6 × ln(P)  [P in bar]
                  At 8 bar: T_sat = 170.4°C
    Mass balance: dm/dt = m_feedwater - m_steam - m_blowdown
    Energy:       dU/dt = Q_burner - m_steam × h_fg - Q_losses
    Three-element: FW_cmd = 50 + (level_error × Kp) + (FF_steam × FF_gain)

Steady state targets:
    Drum pressure:     8 bar        Drum temp:    170°C
    Drum level:        50%          Steam flow:   3,733 kg/hr
    Fuel flow:         180 kg/hr    Efficiency:   ~82%
    Burner state:      LOW or HIGH  fault_code:   0

Register map (port 507):
    40001  drum_pressure        bar × 100
    40002  drum_temp            °C × 10
    40003  drum_level           % × 10
    40004  steam_flow           kg/hr × 10
    40005  feedwater_flow       kg/hr × 10
    40006  fuel_flow            kg/hr × 10
    40007  burner_state         0=OFF 1=LOW 2=HIGH
    40008  fw_pump_speed        RPM
    40009  steam_valve_pos      % × 10
    40010  fw_valve_pos         % × 10
    40011  blowdown_valve_pos   % × 10
    40012  flue_gas_temp        °C × 10
    40013  combustion_efficiency % × 10
    40014  Q_burner_kW          kW
    40015  fault_code           0=OK 1=LOW_WATER 2=OVERPRESSURE
                                3=FLAME_FAILURE 4=PUMP_FAULT

Alarm limits:
    Drum pressure high:  10 bar — CRITICAL — burner trip
    Drum pressure low:    6 bar — HIGH
    Drum level low:       20%  — CRITICAL — burner trip (LOW_WATER)
    Drum level high:      80%  — HIGH

Safety interlocks (immediate burner trip):
    Level < 20%     → fault_code = 1  (LOW_WATER)
    Pressure > 10   → fault_code = 2  (OVERPRESSURE)
    Pump fault      → fault_code = 4

Operational commands (FC06 writes):
    Trip burner:         write 0 to burner_state (40007)
    Force low water:     write 150 to drum_level (40003) = 15%
    Force overpressure:  write 1100 to drum_pressure (40001) = 11 bar
    Clear fault:         write 0 to fault_code (40015)
    Change steam demand: write position to steam_valve (40009)

Conservation law (physics-based detection target):
    Q_burner must balance with steam energy output + losses
    m_feedwater must balance with m_steam + m_blowdown + dm_drum/dt
    Sensor manipulation breaks either balance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROCESS 4 — PIPELINE PUMP STATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Path:     processes/pipeline/
Port:     508
Models:   Kenya Pipeline Company — petroleum product transfer
Style:    Classes, config.json, full physics

What this process does:
    Petroleum product (diesel, SG=0.85) arrives at low inlet pressure.
    Duty pump boosts pressure for downstream segment delivery.
    Standby pump auto-starts if duty pump faults.
    Outlet valve modulates to maintain target outlet pressure.
    Flow meter measures product flow rate continuously.
    Pressure sensors monitor inlet and outlet headers.
    PLC manages duty/standby logic and pressure control.
    Leak detection compares pump flow to meter reading.

Equipment:
    duty_pump.py         Primary pump — affinity laws + system curve
    standby_pump.py      Standby pump — identical, auto-start on fault
    inlet_valve.py       Inlet isolation — on/off only
    outlet_valve.py      Outlet control valve — pressure modulation
    flow_meter.py        Turbine flow meter — product flow
    pressure_sensors.py  Inlet and outlet pressure transmitters
    plc_logic.py         PLC — duty/standby logic, pressure control, leak
    process_state.py     Central shared state
    process_state.json   Persistence
    config.json          All parameters
    main.py              Orchestrator
    start.sh / stop.sh

Physics:
    Affinity laws:    Q∝N   H∝N²   P∝N³
    System curve:     H_system = H_static + H_friction + H_elevation
    Darcy-Weisbach:   dH = f × (L/D) × (v²/2g)
    Segment params:   D=0.356m  L=15km  elevation=50m  f=0.018
    At rated flow:    v = 1.26 m/s
    Friction loss:    5.2 bar
    Elevation loss:   0.4 bar
    Pump head:        46 bar rated
    Net outlet:       2.0 + 46.0 - 5.2 - 0.4 = ~42 bar
    Power:            P = ρgQH/η = 737 kW at rated conditions

Steady state targets:
    Inlet pressure:    2.0 bar      Outlet pressure:  38-42 bar
    Flow rate:         450 m³/hr    Pump speed:       1480 RPM
    Duty pump:         running      Standby pump:     on standby
    fault_code:        0

Register map (port 508):
    40001  inlet_pressure      bar × 100
    40002  outlet_pressure     bar × 100
    40003  flow_rate           m³/hr × 10
    40004  duty_pump_speed     RPM
    40005  duty_pump_current   A × 10
    40006  duty_pump_running   0/1
    40007  standby_pump_speed  RPM
    40008  standby_pump_running 0/1
    40009  inlet_valve_pos     % × 10
    40010  outlet_valve_pos    % × 10
    40011  pump_differential   bar × 100
    40012  flow_velocity       m/s × 100
    40013  duty_pump_power_kW  kW
    40014  leak_flag           0=OK 1=SUSPECTED
    40015  fault_code          0=OK 1=DUTY_FAULT 2=BOTH_FAULT
                               3=OVERPRESSURE

Alarm limits:
    Outlet pressure high:  55 bar — CRITICAL
    Outlet pressure low:   38 bar — HIGH
    Inlet pressure low:     1 bar — HIGH
    Flow low:             200 m³/hr — MEDIUM
    Leak suspected:       >15 m³/hr discrepancy

PLC control logic:
    Duty pump runs at rated speed (1480 RPM)
    Outlet valve modulates to maintain 40 bar target pressure
    Duty fault → standby starts automatically → fault_code = 1
    Both fault → emergency shutdown → fault_code = 2
    Overpressure → fault_code = 3

Operational commands (FC06 writes):
    Force duty fault:       write 1 to fault indicator
    Simulate flow drop:     write low value to flow register 40003
    Force outlet high:      write 5500 to outlet pressure (40002)
    Change valve position:  write position to 40010
    Clear fault:            write 0 to 40015

Conservation law (physics-based detection target):
    flow_in = flow_out + d(line_pack)/dt
    Pump expected flow vs meter reading
    Discrepancy > threshold → leak_flag activates
    Sensor manipulation breaks flow-pressure relationship

================================================================================
STARTING AND STOPPING PROCESSES
================================================================================

METHOD 1 — Central Manager (Recommended):
    cd processes
    sudo python3 manager.py start     # sudo required for ports < 1024
    sudo python3 manager.py stop
    sudo python3 manager.py status
    sudo python3 manager.py logs

METHOD 2 — Individual Process Scripts:
    cd processes/pumping_station && sudo bash start.sh
    cd processes/heat_exchanger  && sudo bash start.sh
    cd processes/boiler          && sudo bash start.sh
    cd processes/pipeline        && sudo bash start.sh

    cd processes/pumping_station && sudo bash stop.sh
    cd processes/heat_exchanger  && sudo bash stop.sh
    cd processes/boiler          && sudo bash stop.sh
    cd processes/pipeline        && sudo bash stop.sh

VERIFY ALL RUNNING:
    ss -tlnp | grep -E ':(502|506|507|508) '

REQUIREMENTS (Linux):
    sudo pip3 install psutil pyyaml

================================================================================
READING LIVE DATA — UNIVERSAL PATTERN
================================================================================

Pure socket read — no pymodbus — works from any VM:

    python3 - <<'EOF'
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

    regs = read('192.168.100.20', 506, 0, 17)   # heat exchanger example
    print(regs)
    EOF

================================================================================
WRITING TO PROCESSES — OPERATIONAL COMMANDS
================================================================================

FC06 write — change a register value:

    python3 - <<'EOF'
    import socket, struct

    def write(host, port, register_index, value):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((host, port))
        pdu     = struct.pack('>BHH', 0x06, register_index, value)
        request = struct.pack('>HHHB', 1, 0, 1+len(pdu), 1) + pdu
        s.sendall(request)
        resp = s.recv(256)
        s.close()
        return resp[7] == 0x06   # True = confirmed

    # Examples:
    write('192.168.100.20', 506, 3,  1000)  # T_cold_out = 100°C (OVERTEMP)
    write('192.168.100.20', 506, 16, 0)     # Clear fault code
    write('192.168.100.20', 508, 5,  0)     # Stop duty pump
    write('192.168.100.20', 502, 0,  200)   # Force tank level to 20%
    EOF

================================================================================
FAULT INJECTION — OPERATIONAL BREAK SCENARIOS
================================================================================

Every process has defined fault injection points.
Use these during language exercises to demonstrate
that the code being learned controls real running systems.

HEAT EXCHANGER (port 506):
    OVERTEMP alarm:       write 1000 to index 3   (T_cold_out = 100°C)
    PUMP_FAULT:           write 1 to index 16     (fault_code = 1)
    Close cold valve:     write 0 to index 15     (cold_valve_pos = 0%)
    Stop cold pump:       write 0 to index 13     (cold_pump_speed = 0)
    Clear all faults:     write 0 to index 16     (fault_code = 0)

PUMPING STATION (port 502):
    HIGH_LEVEL alarm:     write 920 to index 0    (tank_level = 92%)
    LOW_LEVEL alarm:      write 80 to index 0     (tank_level = 8%)
    DRY_RUN:              write 0 to index 3      (flow = 0 with pump on)
    Stop pump:            write 0 to index 7      (pump_running = 0)
    Clear fault:          write 0 to index 14     (fault_code = 0)

BOILER (port 507):
    LOW_WATER trip:       write 150 to index 2    (drum_level = 15%)
    OVERPRESSURE trip:    write 1100 to index 0   (drum_pressure = 11 bar)
    Trip burner:          write 0 to index 6      (burner_state = OFF)
    Clear fault:          write 0 to index 14     (fault_code = 0)

PIPELINE (port 508):
    Outlet overpressure:  write 5600 to index 1   (outlet = 56 bar)
    Simulate flow drop:   write 500 to index 2    (flow = 50 m³/hr)
    Force duty fault:     write 1 to index 14     (fault_code = 1)
    Clear fault:          write 0 to index 14

================================================================================
RECOVERY VERIFICATION — AFTER EVERY FAULT
================================================================================

After any fault injection and recovery attempt — verify:

    python3 - <<'EOF'
    import socket, struct

    def read(host, port, start, count):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((host, port))
        pdu = struct.pack('>BHH', 0x03, start, count)
        req = struct.pack('>HHHB', 1, 0, 1+len(pdu), 1) + pdu
        s.sendall(req)
        resp = s.recv(256)
        s.close()
        return list(struct.unpack(f'>{count}H', resp[9:9+count*2]))

    processes = {
        'pumping_station': (502, 14),   # fault_code at index 14
        'heat_exchanger':  (506, 16),   # fault_code at index 16
        'boiler':          (507, 14),   # fault_code at index 14
        'pipeline':        (508, 14),   # fault_code at index 14
    }

    print("Process Health:")
    print("─" * 40)
    for name, (port, fault_idx) in processes.items():
        try:
            regs = read('192.168.100.20', port, 0, fault_idx+1)
            fc   = regs[fault_idx]
            status = "OK" if fc == 0 else f"FAULT {fc}"
            print(f"  {name:<20} port {port}  {status}")
        except Exception as e:
            print(f"  {name:<20} port {port}  UNREACHABLE")
    EOF

================================================================================
DATA FLOW — COMPLETE VIRTUAL PLANT
================================================================================

UBUNTU-PLC (192.168.100.20)
    port 502  pumping_station    Nairobi Water
    port 506  heat_exchanger     KenGen Olkaria
    port 507  boiler             EABL/Bidco
    port 508  pipeline           Kenya Pipeline Company

All processes → Modbus TCP → HOST-ENG / UBUNTU-SCADA (any client)
All processes → MQTT publish → UBUNTU-SCADA Mosquitto (port 1883)
UBUNTU-SCADA → InfluxDB      → time-series historian (port 8086)
UBUNTU-SCADA → Grafana       → live dashboards (port 3000)
UBUNTU-SCADA → RapidSCADA    → SCADA operator interface (port 10008)

================================================================================
PHYSICS-BASED DETECTION REFERENCE
================================================================================

These are the physical laws each process obeys.
Any sensor manipulation breaks one or more of them.
OT-Guardian validates these in real time.

PUMPING STATION:
    Q_pump × dt = ΔV_tank + Q_demand × dt
    Pump flow = f(pump_speed)  — affinity law
    Discharge pressure = f(pump_speed²)

HEAT EXCHANGER:
    Q_hot = m_hot × Cp_hot × (T_hot_in - T_hot_out)
    Q_cold = m_cold × Cp_cold × (T_cold_out - T_cold_in)
    Q_hot must equal Q_cold within ±15%
    Pump flow must match affinity law prediction

BOILER:
    Q_burner = m_fuel × LHV × η
    m_steam = Q_burner / h_fg  (within efficiency range)
    m_feedwater ≈ m_steam + m_blowdown
    Pressure-temperature: T_sat = 100 + 28.6 × ln(P)

PIPELINE:
    flow_meter ≈ pump_expected_flow (within ±15 m³/hr)
    Outlet_pressure = inlet + pump_head - friction - elevation
    Discrepancy > threshold → leak_flag

================================================================================
PROTOCOL EVOLUTION — ROADMAP
================================================================================

The lab starts Modbus TCP only.
Each language phase adds protocols as that language matures.

Phase 1 (current):
    Modbus TCP on all processes (ports 502-508)

Phase 2 — MQTT publishing added:
    Each process adds mqtt_publisher.py
    Publishes all register values to Mosquitto every 1s
    Topic structure: factory/{process}/{tag}

Phase 3 — Modbus RTU added:
    Serial via /dev/ttyUSB0 (Tier 2 hardware)
    STM32 as real Modbus RTU slave

Phase 4 — OPC UA added:
    Each process adds opcua_server.py
    Exposes all tags as OPC UA nodes
    Port 4840 per process

Phase 5 — DNP3 added:
    Pipeline process gets DNP3 server
    Realistic for KPC utility SCADA context

Phase 6+ — Security phases:
    CyphyOS (192.168.100.40) active
    ControlThings (192.168.100.50) active
    All protocols become attack surfaces

================================================================================
MODBUS IMPLEMENTATION — ALL LANGUAGE PHASES
================================================================================

pymodbus is ONLY acceptable as temporary pre-code in Phase 1
shell scripting exercises before own implementations are built.

After each language builds its own Modbus implementation:

    Python  → MORBIONModbusTCP (Python Phase 2 Module 6)
    C       → raw socket + struct (C Phase 2)
    C#      → TcpClient raw frames (C# Phase 2)
    PowerShell → System.Net.Sockets.TcpClient (PowerShell Phase 2)
    Bash    → /dev/tcp socket (Bash Phase 2)
    C++     → RAII socket wrapper (C++ Phase 2)

After each language reaches its protocol module:
    pymodbus never appears again in that language's exercises.
    Own implementation used exclusively from that point forward.

================================================================================
KNOWN ISSUES AND FIXES
================================================================================

ISSUE: process_state.json empty file crashes restore()
FIX:   All restore() methods guard with:
           if os.path.getsize(path) == 0: return
           try/except json.JSONDecodeError: return

ISSUE: Permission denied when binding to ports < 1024
FIX:   Linux requires root for privileged ports (502, 506, 507, 508)
       Always use sudo:
           sudo python3 manager.py start
           sudo python3 manager.py stop

ISSUE: psutil not found when running with sudo
FIX:   Install psutil for root user:
           sudo pip3 install psutil

ISSUE: Manager says "Not running" but processes ARE running
FIX:   - Always use sudo for both start AND stop
       - Manager now scans by port - no PID file needed
       - If stuck: sudo pkill -f "python3.*main.py"

ISSUE: manager.py stop doesn't work - processes keep running
FIX:   - Must use same sudo user that started the processes
       - Or use port-based scan fallback (now built-in)
       - Manual: sudo ss -tlnp | grep ':502 ' → get PID → sudo kill PID

ISSUE: psutil.AccessDenied when scanning processes
FIX:   Running manager with sudo solves this:
           sudo python3 manager.py start
           sudo python3 manager.py stop

ISSUE: Ctrl+C kills background process
FIX:   Use setsid in start.sh. Use disown after &.
       trap 'echo Detached; exit 0' INT before tail -f

ISSUE: Unit conversion L/min to kg/s
FIX:   m_kgs = flow_lpm / 60.0   NOT /60000.0
       L/min ÷ 60 = L/s = kg/s (water density ≈ 1 kg/L)

ISSUE: NTU too high — effectiveness → 1.0 — overheating
FIX:   Calculate U×A from target outlet temps first.
       Never guess U and A. Derive from energy balance target.

ISSUE: Pipeline outlet pressure too low
FIX:   Segment length determines friction losses.
       One pump station cannot cover 80km + 200m elevation.
       Use realistic single-station parameters: 15km, 50m elevation.

================================================================================
QUICK REFERENCE — LINUX
================================================================================

# Install dependencies (as root)
sudo pip3 install psutil pyyaml

# Start all processes
sudo python3 manager.py start

# Check status
sudo python3 manager.py status

# View logs
sudo python3 manager.py logs

# Stop all processes
sudo python3 manager.py stop

# If stuck - manual kill
sudo pkill -f "python3.*main.py"

# Verify ports listening
sudo ss -tlnp | grep -E ':(502|506|507|508) '

================================================================================
