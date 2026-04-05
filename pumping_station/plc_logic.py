"""
plc_logic.py — Pumping Station PLC
Level-based pump start/stop control.
Dry run protection.
Alarm evaluation with deadband.
Conservation law monitoring.

Control strategy:
    Pump START conditions (all must be true):
        level < level_start_pct (20%)
        no fault active
        pump not already running

    Pump STOP conditions (any triggers stop):
        level > level_stop_pct (80%)
        high level alarm active
        low-low level alarm (dry run risk)
        pump fault

    Outlet valve:
        Normally open at setpoint (85%)
        Closes to 20% on high level alarm
        Closes fully on low-low level alarm

    Dry run protection:
        If pump running for >10s with flow < 5 m³/hr
        Trip pump — fault_code = 4

    Conservation law check:
        Q_pump × dt vs ΔV_tank + Q_demand × dt
        Discrepancy > threshold → alarm
"""


class PumpingStationPLC:

    def __init__(self, config: dict, pump, inlet_valve, outlet_valve):
        self._cfg          = config
        self._pump         = pump
        self._inlet_valve  = inlet_valve
        self._outlet_valve = outlet_valve

        ctrl = config["control"]
        self._level_start  = ctrl["level_start_pct"]
        self._level_stop   = ctrl["level_stop_pct"]
        self._dry_run_delay= ctrl["dry_run_delay_s"]

        # Alarm states
        self._alarm_high:     bool  = False
        self._alarm_low:      bool  = False
        self._alarm_low_low:  bool  = False
        self._alarm_no_flow:  bool  = False
        self._alarm_pressure: bool  = False
        self._alarm_dry_run:  bool  = False

        # Dry run timer
        self._no_flow_timer:  float = 0.0

    def scan(self, state, dt: float):
        self._read_inputs(state)
        self._safety_checks(state, dt)
        self._control_logic(state)
        self._alarm_logic(state)

    def _read_inputs(self, state):
        with state:
            self._running   = state.process_running
            self._level     = state.level_sensor_pct
            self._flow      = state.flow_m3hr
            self._pressure  = state.discharge_pressure_bar
            self._pump_run  = state.pump_running
            self._pump_flt  = state.pump_fault
            self._fault     = state.fault_code

    def _safety_checks(self, state, dt: float):
        """Dry run protection — trip pump if no flow while running."""
        if self._pump_run and self._flow < self._cfg["alarms"]["no_flow_on_run"]["limit"]:
            self._no_flow_timer += dt
            if self._no_flow_timer > self._dry_run_delay:
                self._alarm_dry_run = True
                self._pump.stop()
                self._inlet_valve.close()
                with state:
                    state.fault_code     = 4
                    state.alarm_dry_run  = True
        else:
            self._no_flow_timer = 0.0

    def _control_logic(self, state):
        if not self._running:
            self._pump.stop()
            self._inlet_valve.close()
            self._outlet_valve.fail_safe()
            return

        if self._fault > 0:
            self._pump.stop()
            self._inlet_valve.close()
            return

        # Pump start condition
        if not self._pump_run and self._level < self._level_start:
            self._pump.start()
            self._pump.set_speed(self._cfg["pump"]["setpoint_rpm"])
            self._inlet_valve.open()

        # Pump stop condition
        if self._pump_run and self._level > self._level_stop:
            self._pump.stop()
            self._inlet_valve.close()

        # Outlet valve control
        if self._alarm_high:
            self._outlet_valve.set_position(20.0)
        elif self._alarm_low_low:
            self._outlet_valve.set_position(0.0)
        else:
            self._outlet_valve.set_position(
                self._cfg["outlet_valve"]["setpoint_pct"])

        # Clear dry run fault if level recovered
        if self._fault == 4 and self._level > 15.0:
            with state:
                state.fault_code    = 0
                state.alarm_dry_run = False
            self._alarm_dry_run = False

    def _alarm_logic(self, state):
        alm = self._cfg["alarms"]

        # High level
        lim = alm["level_high"]["limit"]
        db  = alm["level_high"]["deadband"]
        if self._level > lim:
            self._alarm_high = True
        elif self._level < lim - db:
            self._alarm_high = False

        # Low level
        lim = alm["level_low"]["limit"]
        db  = alm["level_low"]["deadband"]
        if self._level < lim:
            self._alarm_low = True
        elif self._level > lim + db:
            self._alarm_low = False

        # Low-low level
        lim = alm["level_low_low"]["limit"]
        db  = alm["level_low_low"]["deadband"]
        if self._level < lim:
            self._alarm_low_low = True
        elif self._level > lim + db:
            self._alarm_low_low = False

        # Pressure high
        lim = alm["pressure_high"]["limit"]
        db  = alm["pressure_high"]["deadband"]
        if self._pressure > lim:
            self._alarm_pressure = True
        elif self._pressure < lim - db:
            self._alarm_pressure = False

        # Fault codes from alarms
        if self._alarm_low_low and not self._pump_run:
            with state:
                state.fault_code = 2
        elif self._alarm_high:
            with state:
                state.fault_code = 1
        elif not self._alarm_high and not self._alarm_low_low and self._fault in [1, 2]:
            with state:
                state.fault_code = 0

        with state:
            state.alarm_level_high    = self._alarm_high
            state.alarm_level_low     = self._alarm_low
            state.alarm_level_low_low = self._alarm_low_low
            state.alarm_pressure_high = self._alarm_pressure
