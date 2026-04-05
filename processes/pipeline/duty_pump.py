"""
duty_pump.py — Duty Pump
Primary centrifugal pump. Boosts petroleum product pressure
from inlet to outlet of pipeline segment.

Physics:
    Affinity laws:
        Q  ∝  N        flow proportional to speed
        H  ∝  N²       head proportional to speed squared
        P  ∝  N³       power proportional to speed cubed

    System curve intersection:
        H_pump(Q) = H_system(Q)
        H_system  = static_head + friction_losses
        friction  = f × (L/D) × (v²/2g)  Darcy-Weisbach

    Power and current:
        P_shaft = ρ × g × Q × H / η
        I       = P / (√3 × V × PF × η_motor)
"""

import math
import random


class DutyPump:

    def __init__(self, config: dict):
        cfg      = config["duty_pump"]
        pipe_cfg = config["pipeline"]

        # Nameplate
        self._N_rated   = cfg["rated_speed_rpm"]
        self._Q_rated   = cfg["rated_flow_m3hr"] / 3600.0   # m³/s
        self._H_rated   = cfg["rated_head_bar"] * 1e5 / (850 * 9.81)  # metres
        self._eta       = cfg["rated_efficiency"]
        self._tau       = cfg["tau"]
        self._SG        = cfg["specific_gravity"]
        self._rho       = self._SG * 1000.0                 # kg/m³

        # Pipeline parameters for system curve
        self._D         = pipe_cfg["diameter_m"]
        self._L         = pipe_cfg["length_m"]
        self._f         = pipe_cfg["friction_factor"]
        self._elev      = pipe_cfg["elevation_m"]
        self._A_pipe    = math.pi / 4.0 * self._D ** 2

        # Motor constants
        self._P_rated_kW = (self._rho * 9.81 *
                            self._Q_rated * self._H_rated) / (self._eta * 1000)
        self._I_rated_A  = self._P_rated_kW * 1000 / (math.sqrt(3) * 6600 * 0.9 * 0.95)

        # State
        self.speed_rpm:   float = 0.0
        self.flow_m3s:    float = 0.0
        self.head_bar:    float = 0.0
        self.power_kW:    float = 0.0
        self.current_A:   float = 0.0
        self.running:     bool  = False
        self.fault:       bool  = False

        self._speed_setpoint: float = 0.0

    def set_speed(self, rpm: float):
        self._speed_setpoint = max(0.0, min(rpm, self._N_rated))

    def start(self):
        self.running = True

    def stop(self):
        self.running          = False
        self._speed_setpoint  = 0.0

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
        self.flow_m3s = self._Q_rated * ratio

        # Head from affinity law
        H_metres      = (self._H_rated * ratio ** 2)
        self.head_bar = H_metres * self._rho * 9.81 / 1e5

        # Shaft power and motor current
        self.power_kW  = self._P_rated_kW * ratio ** 3
        self.current_A = self._I_rated_A  * ratio ** 2

        # Add realistic noise
        self.flow_m3s  = max(0.0, self.flow_m3s  + random.gauss(0, 0.001))
        self.head_bar  = max(0.0, self.head_bar   + random.gauss(0, 0.05))
        self.current_A = max(0.0, self.current_A  + random.gauss(0, 0.2))

        self._write_state(state)

    def _write_state(self, state):
        with state:
            state.duty_pump_speed_rpm = self.speed_rpm
            state.duty_pump_running   = self.running
            state.duty_pump_fault     = self.fault
            state.duty_pump_current_A = self.current_A
            state.duty_pump_power_kW  = self.power_kW
            state.duty_pump_head_bar  = self.head_bar
            # Flow feeds into flow meter
            state.flow_rate_m3hr      = self.flow_m3s * 3600.0
            if self._A_pipe > 0:
                state.flow_velocity_ms = self.flow_m3s / self._A_pipe
