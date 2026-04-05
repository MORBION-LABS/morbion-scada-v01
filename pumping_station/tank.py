"""
tank.py — Storage Tank
Elevated cylindrical storage tank.
Receives pumped water on inlet side.
Supplies demand on outlet side.

Physics:
    Mass balance:
        dV/dt = Q_in - Q_out - Q_demand
        Q_in     = pump flow when inlet valve open
        Q_out    = demand flow through outlet valve
        Q_demand = constant background community demand

    Level from volume:
        level_pct = (V / V_max) × 100
        V_max = π/4 × D² × H

    Conservation law for leak detection:
        Q_pump × dt = ΔV + Q_demand × dt
        Violation = sensor manipulation or real leak
"""

import math
import random


class Tank:

    def __init__(self, config: dict):
        cfg = config["tank"]

        self._D           = cfg["diameter_m"]
        self._H           = cfg["height_m"]
        self._demand      = cfg["demand_flow_m3hr"] / 3600.0   # m³/s
        self._A           = math.pi / 4.0 * self._D ** 2
        self._V_max       = self._A * self._H

        # State
        initial_pct   = cfg["initial_level_pct"] / 100.0
        self._volume  = self._V_max * initial_pct

        self.level_pct:   float = cfg["initial_level_pct"]
        self.volume_m3:   float = self._volume
        self.level_mm:    float = (self._volume / self._A) * 1000.0

    def update(self, dt: float, state):
        with state:
            inlet_open   = state.inlet_valve_open
            inlet_pos    = state.inlet_valve_pos_pct / 100.0
            outlet_pos   = state.outlet_valve_pos_pct / 100.0
            pump_flow    = state.flow_m3hr / 3600.0   # m³/s
            running      = state.pump_running

        # Inflow — pump delivers when inlet valve open
        Q_in = pump_flow * inlet_pos if (inlet_open and running) else 0.0

        # Outflow — demand always draws + outlet valve modulates
        Q_out = self._demand * outlet_pos

        # Volume change
        dV_dt      = Q_in - Q_out
        self._volume += dV_dt * dt
        self._volume  = max(0.0, min(self._V_max, self._volume))

        # Level from volume
        self.volume_m3 = self._volume
        self.level_pct = (self._volume / self._V_max) * 100.0
        self.level_mm  = (self._volume / self._A) * 1000.0

        # Net flow for conservation law
        net_flow_m3hr = (Q_in - Q_out) * 3600.0

        self._write_state(state, Q_out * 3600.0, net_flow_m3hr)

    def _write_state(self, state, demand_m3hr: float, net_m3hr: float):
        with state:
            state.tank_level_pct   = self.level_pct + random.gauss(0, 0.05)
            state.tank_volume_m3   = self.volume_m3
            state.demand_flow_m3hr = demand_m3hr
            state.net_flow_m3hr    = net_m3hr
            state.level_sensor_pct = self.level_pct + random.gauss(0, 0.15)
            state.level_sensor_mm  = self.level_mm  + random.gauss(0, 5.0)
