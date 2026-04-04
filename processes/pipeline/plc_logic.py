"""
plc_logic.py — Pipeline Pump Station PLC
Controls duty/standby pump logic, valve sequencing,
pressure management, alarm evaluation and leak detection.

Control strategy:
    Startup sequence:
        1. Open inlet valve
        2. Start duty pump at rated speed
        3. Open outlet valve to setpoint
        4. Monitor pressures and flow

    Duty/Standby logic:
        Duty pump faults → start standby immediately
        Both fault → emergency shutdown, fault_code = 2

    Leak detection:
        Continuity equation: flow_in ≈ flow_out
        If pump flow vs meter discrepancy > threshold → leak flag

    Pressure control:
        Outlet pressure high → modulate outlet valve closed
        Outlet pressure low  → modulate outlet valve open
"""


class PipelinePLC:

    def __init__(self, config: dict, duty_pump, standby_pump,
                 inlet_valve, outlet_valve):
        self._cfg          = config
        self._duty         = duty_pump
        self._standby      = standby_pump
        self._inlet_valve  = inlet_valve
        self._outlet_valve = outlet_valve

        # Alarm state tracking
        self._alarm_outlet_high: bool = False
        self._alarm_outlet_low:  bool = False
        self._alarm_inlet_low:   bool = False
        self._alarm_flow_low:    bool = False
        self._alarm_leak:        bool = False

        self._standby_started:   bool = False

    def scan(self, state):
        self._read_inputs(state)
        self._control_logic(state)
        self._alarm_logic(state)
        self._leak_detection(state)
        self._write_outputs(state)

    def _read_inputs(self, state):
        with state:
            self._process_running    = state.process_running
            self._outlet_pressure    = state.outlet_pressure_bar
            self._inlet_pressure     = state.inlet_pressure_bar
            self._flow               = state.flow_rate_m3hr
            self._duty_fault         = state.duty_pump_fault
            self._standby_fault      = state.standby_pump_fault
            self._duty_running       = state.duty_pump_running
            self._standby_running    = state.standby_pump_running

    def _control_logic(self, state):
        if not self._process_running:
            self._duty.stop()
            self._standby.stop()
            self._inlet_valve.close()
            self._outlet_valve.fail_safe()
            return

        # Both pumps faulted — emergency shutdown
        if self._duty_fault and self._standby_fault:
            self._duty.stop()
            self._standby.stop()
            self._inlet_valve.close()
            with state:
                state.fault_code = 2
            return

        # Duty pump faulted — start standby
        if self._duty_fault and not self._standby_started:
            self._duty.stop()
            if not self._standby_fault:
                self._standby.start()
                self._standby.set_speed(
                    self._cfg["standby_pump"]["setpoint_rpm"])
                self._standby_started = True
            with state:
                state.fault_code = 1
            return

        # Normal operation — duty pump running
        self._inlet_valve.open()

        if not self._duty_running and not self._duty_fault:
            self._duty.start()
            self._duty.set_speed(
                self._cfg["duty_pump"]["setpoint_rpm"])

        # Outlet valve pressure control
        op_cfg   = self._cfg["operating_conditions"]
        target_P = op_cfg["outlet_pressure_nominal"]
        current_P= self._outlet_pressure

        # Simple proportional pressure control via valve
        error    = target_P - current_P
        new_pos  = self._cfg["outlet_valve"]["setpoint_pct"] + (error * 1.5)
        new_pos  = max(20.0, min(95.0, new_pos))
        self._outlet_valve.set_position(new_pos)

    def _alarm_logic(self, state):
        alm = self._cfg["alarms"]

        # Outlet pressure high
        lim = alm["outlet_pressure_high"]["limit"]
        db  = alm["outlet_pressure_high"]["deadband"]
        if self._outlet_pressure > lim:
            self._alarm_outlet_high = True
        elif self._outlet_pressure < lim - db:
            self._alarm_outlet_high = False

        # Outlet pressure low
        lim = alm["outlet_pressure_low"]["limit"]
        db  = alm["outlet_pressure_low"]["deadband"]
        if self._outlet_pressure < lim and self._process_running:
            self._alarm_outlet_low = True
        elif self._outlet_pressure > lim + db:
            self._alarm_outlet_low = False

        # Inlet pressure low
        lim = alm["inlet_pressure_low"]["limit"]
        db  = alm["inlet_pressure_low"]["deadband"]
        if self._inlet_pressure < lim:
            self._alarm_inlet_low = True
        elif self._inlet_pressure > lim + db:
            self._alarm_inlet_low = False

        # Flow low
        lim = alm["flow_low"]["limit"]
        db  = alm["flow_low"]["deadband"]
        if self._flow < lim and self._process_running:
            self._alarm_flow_low = True
        elif self._flow > lim + db:
            self._alarm_flow_low = False

        # Overpressure fault
        if self._alarm_outlet_high:
            with state:
                state.fault_code = 3

        with state:
            state.alarm_outlet_high = self._alarm_outlet_high
            state.alarm_outlet_low  = self._alarm_outlet_low
            state.alarm_inlet_low   = self._alarm_inlet_low
            state.alarm_flow_low    = self._alarm_flow_low

    def _leak_detection(self, state):
        """
        Continuity equation leak detection.
        Pump output flow vs meter reading discrepancy.
        Threshold from config.
        """
        with state:
            pump_flow   = state.duty_pump_speed_rpm  # proxy via speed
            meter_flow  = state.flow_rate_m3hr
            running     = state.duty_pump_running

        if not running:
            return

        threshold = self._cfg["alarms"]["leak_suspected"]["threshold"]

        # In a real pipeline: compare upstream meter to downstream meter
        # Here: compare flow meter reading to expected from pump curve
        # Simplified: noise-driven variation — real leak would be larger
        with state:
            expected_flow = (state.duty_pump_speed_rpm /
                             self._cfg["duty_pump"]["rated_speed_rpm"] *
                             self._cfg["duty_pump"]["rated_flow_m3hr"])
            discrepancy   = abs(expected_flow - meter_flow)
            state.flow_balance_error = discrepancy

            if discrepancy > threshold:
                self._alarm_leak = True
                state.leak_flag  = 1
                state.alarm_leak = True
            else:
                self._alarm_leak = False
                state.leak_flag  = 0
                state.alarm_leak = False

    def _write_outputs(self, state):
        pass
