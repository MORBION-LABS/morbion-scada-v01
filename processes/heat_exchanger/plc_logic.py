"""
plc_logic.py — Heat Exchanger PLC
Simulates the PLC controlling the heat exchanger station.
Reads all sensor values from ProcessState.
Makes control decisions.
Writes commands back to equipment via ProcessState.
Evaluates alarms.

Control strategy:
    - Start/stop pumps based on process_running flag
    - Maintain hot pump speed at config setpoint
    - Maintain cold pump speed at config setpoint
    - Modulate valves to maintain temperature targets
    - Evaluate all alarms every scan
    - Write fault code on any critical alarm
"""


class HeatExchangerPLC:
    """
    The PLC. Controls everything. Reads from state, writes to state.
    Scan cycle: read inputs → evaluate logic → write outputs.
    """

    def __init__(self, config: dict, hot_pump, cold_pump,
                 hot_valve, cold_valve):
        self._cfg        = config
        self._hot_pump   = hot_pump
        self._cold_pump  = cold_pump
        self._hot_valve  = hot_valve
        self._cold_valve = cold_valve

        # Alarm state tracking (deadband logic)
        self._alarm_T_hot_out_active:  bool = False
        self._alarm_T_cold_out_active: bool = False
        self._alarm_eff_active:        bool = False

    def scan(self, state):
        """
        One PLC scan cycle.
        Called every scan_interval_ms from main loop.
        """
        self._read_inputs(state)
        self._control_logic(state)
        self._alarm_logic(state)
        self._write_outputs(state)

    def _read_inputs(self, state):
        """Snapshot all process values from state."""
        with state:
            self._process_running = state.process_running
            self._T_hot_out       = state.T_hot_out
            self._T_cold_out      = state.T_cold_out
            self._efficiency      = state.efficiency
            self._hot_pump_fault  = state.hot_pump_fault
            self._cold_pump_fault = state.cold_pump_fault

    def _control_logic(self, state):
        """Main control decisions."""
        if not self._process_running:
            self._hot_pump.stop()
            self._cold_pump.stop()
            self._hot_valve.fail_safe()
            self._cold_valve.fail_safe()
            return

        # Critical fault — both pumps faulted
        if self._hot_pump_fault and self._cold_pump_fault:
            self._hot_pump.stop()
            self._cold_pump.stop()
            with state:
                state.fault_code = 1
            return

        # Start pumps at configured setpoints
        if not self._hot_pump.running and not self._hot_pump_fault:
            self._hot_pump.start()
            self._hot_pump.set_speed(
                self._cfg["hot_pump"]["setpoint_rpm"])

        if not self._cold_pump.running and not self._cold_pump_fault:
            self._cold_pump.start()
            self._cold_pump.set_speed(
                self._cfg["cold_pump"]["setpoint_rpm"])

        # Valve control — maintain at configured positions
        self._hot_valve.set_position(
            self._cfg["hot_valve"]["setpoint_pct"])
        self._cold_valve.set_position(
            self._cfg["cold_valve"]["setpoint_pct"])

    def _alarm_logic(self, state):
        """Evaluate all alarms with deadband."""
        alm_cfg = self._cfg["alarms"]

        # T_hot_out high alarm
        limit    = alm_cfg["T_hot_out_high"]["limit"]
        deadband = alm_cfg["T_hot_out_high"]["deadband"]
        if self._T_hot_out > limit:
            self._alarm_T_hot_out_active = True
        elif self._T_hot_out < (limit - deadband):
            self._alarm_T_hot_out_active = False

        # T_cold_out high alarm
        limit    = alm_cfg["T_cold_out_high"]["limit"]
        deadband = alm_cfg["T_cold_out_high"]["deadband"]
        if self._T_cold_out > limit:
            self._alarm_T_cold_out_active = True
        elif self._T_cold_out < (limit - deadband):
            self._alarm_T_cold_out_active = False

        # Efficiency low alarm
        limit    = alm_cfg["efficiency_low"]["limit"]
        deadband = alm_cfg["efficiency_low"]["deadband"]
        if self._efficiency < limit and self._process_running:
            self._alarm_eff_active = True
        elif self._efficiency > (limit + deadband):
            self._alarm_eff_active = False

        with state:
            state.alarm_T_hot_out_high  = self._alarm_T_hot_out_active
            state.alarm_T_cold_out_high = self._alarm_T_cold_out_active
            state.alarm_efficiency_low  = self._alarm_eff_active
            state.alarm_hot_pump_fault  = self._hot_pump_fault
            state.alarm_cold_pump_fault = self._cold_pump_fault

            # Overtemp fault code
            if self._alarm_T_hot_out_active or self._alarm_T_cold_out_active:
                state.fault_code = 3
            elif not self._hot_pump_fault and not self._cold_pump_fault:
                state.fault_code = 0

    def _write_outputs(self, state):
        """No direct register writes here — equipment classes handle their own state."""
        pass
