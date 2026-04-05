"""
drum.py — Steam Drum
Heart of the boiler. Water and steam coexist at saturation conditions.
Receives heat from burner. Generates steam. Maintains drum level.

Physics:
    Mass balance:
        dm/dt = m_feedwater - m_steam - m_blowdown
        All in kg/s

    Energy balance:
        dU/dt = Q_burner - m_steam × h_fg - Q_losses
        U = m_water × Cp × T_sat

    Saturation relationship (simplified Antoine-style):
        T_sat(P) = 100 + 28.6 × ln(P)   [P in bar, T in °C]
        Pressure rises when energy input exceeds steam output

    Drum level:
        level_pct = (m_water / m_water_full) × 100
        Shrink and swell effects simplified
"""

import math
import random


class Drum:

    def __init__(self, config: dict):
        cfg = config["drum"]
        op  = config["operating_conditions"]

        self._volume_m3      = cfg["volume_m3"]
        self._m_water_rated  = cfg["water_mass_kg"]
        self._P_nominal      = cfg["pressure_nominal_bar"]
        self._h_fg           = cfg["h_fg_kJkg"]
        self._h_f            = cfg["h_f_kJkg"]
        self._Cp             = cfg["Cp_water_kJkgK"]
        self._tau_thermal    = cfg["tau_thermal"]
        self._fw_temp        = op["feedwater_temp_C"]

        # State
        self.pressure_bar:   float = 0.5
        self.temp_C:         float = self._sat_temp(0.5)
        self.level_pct:      float = 50.0
        self.steam_flow_kghr:float = 0.0
        self._m_water:       float = self._m_water_rated * 0.5

        # Pressure dynamics
        self._energy_stored: float = self._m_water * self._Cp * self.temp_C

    def _sat_temp(self, pressure_bar: float) -> float:
        """Saturation temperature from pressure — simplified."""
        p = max(0.1, pressure_bar)
        return 100.0 + 28.6 * math.log(p)

    def _sat_pressure(self, temp_C: float) -> float:
        """Saturation pressure from temperature — inverse of above."""
        return math.exp((temp_C - 100.0) / 28.6)

    def update(self, dt: float, state):
        with state:
            Q_in          = state.Q_burner_kW
            fw_flow_kghr  = state.feedwater_flow_kghr
            sv_pos        = state.steam_valve_pos_pct
            bd_pos        = state.blowdown_valve_pos_pct

        fw_flow_kgs = fw_flow_kghr / 3600.0

        # Steam flow — driven by valve position and pressure
        # Steam releases when valve opens — proportional to pressure
        steam_flow_kgs = (sv_pos / 100.0) * (self.pressure_bar / self._P_nominal) * (
            self._m_water_rated * 0.5 / 3600.0)
        self.steam_flow_kghr = steam_flow_kgs * 3600.0

        # Blowdown flow — proportional to valve position and pressure
        blowdown_kgs = (bd_pos / 100.0) * (self.pressure_bar / 10.0) * 0.05

        # Mass balance
        dm_dt          = fw_flow_kgs - steam_flow_kgs - blowdown_kgs
        self._m_water += dm_dt * dt
        self._m_water  = max(100.0, self._m_water)

        # Energy balance
        Q_steam_kW     = steam_flow_kgs * self._h_fg
        Q_fw_kW        = fw_flow_kgs    * self._Cp * (self._fw_temp - self.temp_C)
        Q_losses_kW    = 0.02 * Q_in    # 2% radiation and convection losses

        dU_dt          = Q_in + Q_fw_kW - Q_steam_kW - Q_losses_kW
        self._energy_stored += dU_dt * dt

        # Temperature from energy
        if self._m_water > 0:
            T_new = self._energy_stored / (self._m_water * self._Cp)
            T_new = max(20.0, min(200.0, T_new))
            # First order lag — thermal mass slows temperature change
            self.temp_C += ((T_new - self.temp_C) / self._tau_thermal) * dt

        # Pressure from saturation temperature
        self.pressure_bar = self._sat_pressure(self.temp_C)
        self.pressure_bar = max(0.0, self.pressure_bar)
        self.pressure_bar += random.gauss(0, 0.01)

        # Drum level from water mass
        self.level_pct = (self._m_water / self._m_water_rated) * 100.0
        self.level_pct = max(0.0, min(100.0, self.level_pct))
        self.level_pct += random.gauss(0, 0.1)

        self._write_state(state)

    def _write_state(self, state):
        with state:
            state.drum_pressure_bar  = self.pressure_bar
            state.drum_temp_C        = self.temp_C + random.gauss(0, 0.2)
            state.drum_level_pct     = self.level_pct
            state.steam_flow_kghr    = self.steam_flow_kghr
            state.h_fg_kJkg          = self._h_fg
