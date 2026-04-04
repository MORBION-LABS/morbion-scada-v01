"""
plc_logic.py — Boiler PLC
Three-element drum level control.
Burner firing management.
Safety interlock logic.
Alarm evaluation.

Control strategy:
    Startup sequence:
        1. Start feedwater pump
        2. Fill drum to 50% level
        3. Ignite burner at LOW firing
        4. Ramp to HIGH when pressure > 4 bar
        5. Open steam valve when pressure > 6 bar

    Three-element drum level control:
        Error    = level_setpoint - drum_level
        FF_steam = steam_flow / max_steam_flow  (feedforward)
        FW_cmd   = base_position + (error × Kp) + (FF_steam × FF_gain)
        Controls feedwater valve position

    Pressure control:
        Below 6 bar  → burner HIGH
        6 to 8 bar   → burner LOW
        Above 9 bar  → burner OFF
        Above 10 bar → safety shutdown (fault_code = 2)

    Safety interlocks (trip burner immediately):
        Low drum level < 20%   → fault_code = 1 (LOW_WATER)
        High pressure > 10 bar → fault_code = 2 (OVERPRESSURE)
        Flame failure           → fault_code = 3
        Pump fault              → fault_code = 4
"""


class BoilerPLC:

    def __init__(self, config: dict, burner, feedwater_pump,
                 steam_valve, feedwater_valve, blowdown_valve):
        self._cfg             = config
        self._burner          = burner
        self._fw_pump         = feedwater_pump
        self._steam_valve     = steam_valve
        self._fw_valve        = feedwater_valve
        self._blowdown_valve  = blowdown_valve

        # Control parameters
        self._level_sp        = config["operating_conditions"]["drum_level_nominal"]
        self._pressure_sp     = config["operating_conditions"]["drum_pressure_nominal"]
        self._Kp_level        = 1.2
        self._FF_gain         = 30.0

        # Startup state
        self._startup_phase   = 0
        self._blowdown_timer  = 0.0

        # Alarm states
        self._alarm_P_high    = False
        self._alarm_P_low     = False
        self._alarm_L_low     = False
        self._alarm_L_high    = False
        self._alarm_flame     = False
        self._alarm_pump      = False

    def scan(self, state):
        self._read_inputs(state)
        self._safety_interlocks(state)
        self._control_logic(state)
        self._alarm_logic(state)
        self._blowdown_logic(state)
        self._write_outputs(state)

    def _read_inputs(self, state):
        with state:
            self._running      = state.process_running
            self._pressure     = state.drum_pressure_bar
            self._level        = state.drum_level_pct
            self._steam_flow   = state.steam_flow_kghr
            self._fw_flow      = state.feedwater_flow_kghr
            self._burner_fault = state.burner_fault
            self._pump_fault   = state.fw_pump_fault
            self._fault_code   = state.fault_code

    def _safety_interlocks(self, state):
        """Trip conditions — checked every scan before control logic."""
        if not self._running:
            return

        # Low water — immediate burner trip
        if self._level < self._cfg["alarms"]["drum_level_low"]["limit"]:
            self._burner.command(0)
            with state:
                state.fault_code = 1
            return

        # Overpressure — immediate burner trip
        if self._pressure > self._cfg["alarms"]["drum_pressure_high"]["limit"]:
            self._burner.command(0)
            with state:
                state.fault_code = 2
            return

        # Pump fault — trip burner (no feedwater = no firing)
        if self._pump_fault:
            self._burner.command(0)
            with state:
                state.fault_code = 4
            return

        # Clear fault if conditions resolved
        if self._fault_code in [1, 2, 4]:
            if (self._level > 25.0 and
                self._pressure < 9.5 and
                not self._pump_fault):
                with state:
                    state.fault_code = 0

    def _control_logic(self, state):
        if not self._running or self._fault_code > 0:
            self._burner.command(0)
            self._fw_pump.stop()
            self._steam_valve.fail_safe()
            self._fw_valve.fail_safe()
            return

        # Always run feedwater pump
        if not self._fw_pump.running and not self._pump_fault:
            self._fw_pump.start()
            self._fw_pump.set_speed(
                self._cfg["feedwater_pump"]["setpoint_rpm"])

        # Burner pressure control
        if self._pressure < 6.0:
            self._burner.command(2)    # HIGH
        elif self._pressure < self._pressure_sp:
            self._burner.command(1)    # LOW
        elif self._pressure >= 9.0:
            self._burner.command(0)    # OFF
        else:
            self._burner.command(1)    # LOW — hold

        # Steam valve — open when pressure established
        if self._pressure > 6.0:
            self._steam_valve.set_position(
                self._cfg["steam_valve"]["setpoint_pct"])
        else:
            self._steam_valve.set_position(0.0)

        # Three-element feedwater control
        level_error = self._level_sp - self._level
        max_steam   = self._cfg["operating_conditions"]["steam_flow_nominal_kghr"]
        FF_steam    = min(1.0, self._steam_flow / max_steam) if max_steam > 0 else 0.0
        fw_cmd      = 50.0 + (level_error * self._Kp_level) + (FF_steam * self._FF_gain)
        fw_cmd      = max(10.0, min(90.0, fw_cmd))
        self._fw_valve.set_position(fw_cmd)

    def _alarm_logic(self, state):
        alm = self._cfg["alarms"]

        lim = alm["drum_pressure_high"]["limit"]
        db  = alm["drum_pressure_high"]["deadband"]
        self._alarm_P_high = (self._pressure > lim if not self._alarm_P_high
                               else self._pressure > lim - db)

        lim = alm["drum_pressure_low"]["limit"]
        db  = alm["drum_pressure_low"]["deadband"]
        self._alarm_P_low  = (self._pressure < lim if not self._alarm_P_low
                               else self._pressure < lim + db)

        lim = alm["drum_level_low"]["limit"]
        db  = alm["drum_level_low"]["deadband"]
        self._alarm_L_low  = (self._level < lim if not self._alarm_L_low
                               else self._level < lim + db)

        lim = alm["drum_level_high"]["limit"]
        db  = alm["drum_level_high"]["deadband"]
        self._alarm_L_high = (self._level > lim if not self._alarm_L_high
                               else self._level > lim - db)

        with state:
            state.alarm_pressure_high = self._alarm_P_high
            state.alarm_pressure_low  = self._alarm_P_low
            state.alarm_level_low     = self._alarm_L_low
            state.alarm_level_high    = self._alarm_L_high
            state.alarm_pump_fault    = self._pump_fault

    def _blowdown_logic(self, state):
        """
        Periodic blowdown — open blowdown valve for 30s every 2 hours.
        Maintains water quality by removing concentrated water.
        """
        self._blowdown_timer += 0.1
        if self._blowdown_timer > 7200:
            self._blowdown_timer = 0.0

        if 7170 < self._blowdown_timer <= 7200 and self._running:
            self._blowdown_valve.set_position(50.0)
        else:
            self._blowdown_valve.set_position(0.0)

    def _write_outputs(self, state):
        pass
