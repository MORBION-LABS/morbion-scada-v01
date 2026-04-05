"""
pump.py — Centrifugal Pump
Draws water from source and delivers to storage tank.
VFD controlled — variable speed.

Physics:
    Affinity laws:
        Q ∝ N       flow proportional to speed
        H ∝ N²      head proportional to speed squared
        P ∝ N³      power proportional to speed cubed

    System curve intersection:
        H_pump = H_system
        H_system = H_static + H_friction
        H_friction = f × (L/D) × (v²/2g)  Darcy-Weisbach

    Motor current from shaft power:
        P_shaft = ρ × g × Q × H / η
        I = P / (√3 × V × PF × η_motor)

    Discharge pressure:
        P_discharge = ρ × g × H_pump / 1e5  [bar]
"""

import math
import random


class Pump:

    def __init__(self, config: dict):
        cfg = config["pump"]

        self._N_rated   = cfg["rated_speed_rpm"]
        self._Q_rated   = cfg["rated_flow_m3hr"] / 3600.0   # m³/s
        self._H_rated   = cfg["rated_head_m"]               # metres
        self._eta       = cfg["rated_efficiency"]
        self._tau       = cfg["tau"]
        self._D         = cfg["pipe_diameter_m"]
        self._L         = cfg["pipe_length_m"]
        self._f         = cfg["friction_factor"]
        self._H_static  = cfg["static_head_m"]
        self._A_pipe    = math.pi / 4.0 * self._D ** 2

        # Derived nameplate values
        self._P_rated_kW = (1000 * 9.81 * self._Q_rated * self._H_rated) / (
                            self._eta * 1000.0)
        self._I_rated_A  = self._P_rated_kW * 1000.0 / (
                            math.sqrt(3) * 400.0 * 0.88 * 0.92)

        # State
        self.speed_rpm:    float = 0.0
        self.flow_m3hr:    float = 0.0
        self.head_m:       float = 0.0
        self.power_kW:     float = 0.0
        self.current_A:    float = 0.0
        self.pressure_bar: float = 0.0
        self.running:      bool  = False
        self.fault:        bool  = False

        self._speed_setpoint: float = 0.0
        self._starts_today:   int   = 0

    def set_speed(self, rpm: float):
        self._speed_setpoint = max(0.0, min(rpm, self._N_rated))

    def start(self):
        if not self.running:
            self.running       = True
            self._starts_today += 1

    def stop(self):
        self.running         = False
        self._speed_setpoint = 0.0

    def update(self, dt: float, state):
        if self.fault:
            self._write_state(state)
            return

        if not self.running:
            self.speed_rpm = max(
                0.0, self.speed_rpm - (self._N_rated / self._tau) * dt)
        else:
            error = self._speed_setpoint - self.speed_rpm
            self.speed_rpm += (error / self._tau) * dt
            self.speed_rpm  = max(0.0, min(self.speed_rpm, self._N_rated))

        ratio = self.speed_rpm / self._N_rated if self._N_rated > 0 else 0.0

        # Affinity laws from rated point
        Q_m3s      = self._Q_rated   * ratio
        self.head_m= self._H_rated   * ratio ** 2

        # System curve — actual operating point
        if Q_m3s > 0 and self._A_pipe > 0:
            velocity   = Q_m3s / self._A_pipe
            H_friction = (self._f * (self._L / self._D) *
                          (velocity ** 2) / (2.0 * 9.81))
        else:
            H_friction = 0.0

        # Net head available for delivery
        H_net = max(0.0, self.head_m - self._H_static - H_friction)

        self.flow_m3hr  = Q_m3s * 3600.0
        self.power_kW   = self._P_rated_kW * ratio ** 3
        self.current_A  = self._I_rated_A  * ratio ** 2
        self.pressure_bar = (1000 * 9.81 * self.head_m) / 1e5

        # Add realistic noise
        self.flow_m3hr  = max(0.0, self.flow_m3hr  + random.gauss(0, 0.8))
        self.current_A  = max(0.0, self.current_A  + random.gauss(0, 0.1))
        self.pressure_bar = max(0.0, self.pressure_bar + random.gauss(0, 0.01))

        self._write_state(state)

    def _write_state(self, state):
        with state:
            state.pump_speed_rpm        = self.speed_rpm
            state.pump_running          = self.running
            state.pump_fault            = self.fault
            state.pump_current_A        = self.current_A
            state.pump_power_kW         = self.power_kW
            state.pump_head_m           = self.head_m
            state.pump_starts_today     = self._starts_today
            state.flow_m3hr             = self.flow_m3hr
            state.discharge_pressure_bar = self.pressure_bar
