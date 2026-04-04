"""
MORBION SCADA Server — Alarm Evaluators
One class per process. Limits from lab reference document.
"""

from alarms.base import BaseAlarmEvaluator


# ── Pumping Station ───────────────────────────────────────────────────────────

class PumpingStationAlarms(BaseAlarmEvaluator):

    def __init__(self):
        super().__init__("pumping_station")

    def evaluate(self, data: dict) -> list[dict]:
        if not data.get("online"):
            return []

        alarms = []
        level    = data.get("tank_level_pct", 50.0)
        pressure = data.get("discharge_pressure_bar", 0.0)
        fault    = data.get("fault_code", 0)

        # Level — CRIT above 90%, HIGH above 80%
        if level >= 90.0:
            alarms.append(self._alarm(
                "PS-001", "tank_level_pct", "CRIT",
                f"Tank CRITICAL HIGH {level:.1f}% — overflow risk, restrict outlet"))
        elif level >= 80.0:
            alarms.append(self._alarm(
                "PS-002", "tank_level_pct", "HIGH",
                f"Tank level high {level:.1f}% — approaching pump stop"))

        # Level — CRIT below 5%, HIGH below 10%
        if level <= 5.0:
            alarms.append(self._alarm(
                "PS-003", "tank_level_pct", "CRIT",
                f"Tank CRITICAL LOW {level:.1f}% — dry run imminent"))
        elif level <= 10.0:
            alarms.append(self._alarm(
                "PS-004", "tank_level_pct", "HIGH",
                f"Tank level low {level:.1f}% — pump start imminent"))

        # Discharge pressure
        if pressure >= 8.0:
            alarms.append(self._alarm(
                "PS-005", "discharge_pressure_bar", "HIGH",
                f"Discharge pressure high {pressure:.2f} bar — limit 8.0 bar"))

        # PLC fault
        if fault != 0:
            alarms.append(self._alarm(
                "PS-006", "fault_code", "HIGH",
                f"PLC fault active: {data.get('fault_text', str(fault))}"))

        return alarms


# ── Heat Exchanger ────────────────────────────────────────────────────────────

class HeatExchangerAlarms(BaseAlarmEvaluator):

    def __init__(self):
        super().__init__("heat_exchanger")

    def evaluate(self, data: dict) -> list[dict]:
        if not data.get("online"):
            return []

        alarms     = []
        t_cold_out = data.get("T_cold_out_C", 0.0)
        t_hot_out  = data.get("T_hot_out_C",  0.0)
        efficiency = data.get("efficiency_pct", 100.0)
        fault      = data.get("fault_code", 0)

        # Cold outlet overtemp — CRIT
        if t_cold_out >= 95.0:
            alarms.append(self._alarm(
                "HX-001", "T_cold_out_C", "CRIT",
                f"Cold outlet OVERTEMP {t_cold_out:.1f}°C — limit 95°C"))

        # Hot outlet high — HIGH
        if t_hot_out >= 160.0:
            alarms.append(self._alarm(
                "HX-002", "T_hot_out_C", "HIGH",
                f"Hot outlet temp high {t_hot_out:.1f}°C — limit 160°C"))

        # Efficiency low — MED (fouling indicator)
        if efficiency < 60.0:
            alarms.append(self._alarm(
                "HX-003", "efficiency_pct", "MED",
                f"Efficiency low {efficiency:.1f}% — possible tube fouling"))

        # PLC fault
        if fault != 0:
            alarms.append(self._alarm(
                "HX-004", "fault_code", "HIGH",
                f"PLC fault active: {data.get('fault_text', str(fault))}"))

        return alarms


# ── Boiler ────────────────────────────────────────────────────────────────────

class BoilerAlarms(BaseAlarmEvaluator):

    def __init__(self):
        super().__init__("boiler")

    def evaluate(self, data: dict) -> list[dict]:
        if not data.get("online"):
            return []

        alarms   = []
        pressure = data.get("drum_pressure_bar", 8.0)
        level    = data.get("drum_level_pct",   50.0)
        fault    = data.get("fault_code", 0)

        # Overpressure — CRIT safety interlock
        if pressure >= 10.0:
            alarms.append(self._alarm(
                "BL-001", "drum_pressure_bar", "CRIT",
                f"Drum OVERPRESSURE {pressure:.2f} bar — safety trip limit 10 bar"))
        elif pressure <= 6.0:
            alarms.append(self._alarm(
                "BL-002", "drum_pressure_bar", "HIGH",
                f"Drum pressure low {pressure:.2f} bar — steam supply at risk"))

        # Low water — CRIT safety interlock
        if level <= 20.0:
            alarms.append(self._alarm(
                "BL-003", "drum_level_pct", "CRIT",
                f"Drum LOW WATER {level:.1f}% — burner trip active"))
        elif level >= 80.0:
            alarms.append(self._alarm(
                "BL-004", "drum_level_pct", "HIGH",
                f"Drum level high {level:.1f}% — carryover risk"))

        # PLC fault
        if fault != 0:
            alarms.append(self._alarm(
                "BL-005", "fault_code", "HIGH",
                f"PLC fault active: {data.get('fault_text', str(fault))}"))

        return alarms


# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineAlarms(BaseAlarmEvaluator):

    def __init__(self):
        super().__init__("pipeline")

    def evaluate(self, data: dict) -> list[dict]:
        if not data.get("online"):
            return []

        alarms  = []
        outlet  = data.get("outlet_pressure_bar", 40.0)
        inlet   = data.get("inlet_pressure_bar",   2.0)
        flow    = data.get("flow_rate_m3hr",       450.0)
        leak    = data.get("leak_flag",             False)
        fault   = data.get("fault_code", 0)

        # Outlet overpressure — CRIT
        if outlet >= 55.0:
            alarms.append(self._alarm(
                "PL-001", "outlet_pressure_bar", "CRIT",
                f"Outlet OVERPRESSURE {outlet:.1f} bar — limit 55 bar"))
        elif outlet <= 38.0:
            alarms.append(self._alarm(
                "PL-002", "outlet_pressure_bar", "HIGH",
                f"Outlet pressure low {outlet:.1f} bar — delivery at risk"))

        # Inlet low — HIGH
        if inlet <= 1.0:
            alarms.append(self._alarm(
                "PL-003", "inlet_pressure_bar", "HIGH",
                f"Inlet pressure low {inlet:.2f} bar — pump cavitation risk"))

        # Flow low — MED
        if flow <= 200.0:
            alarms.append(self._alarm(
                "PL-004", "flow_rate_m3hr", "MED",
                f"Flow rate low {flow:.1f} m³/hr — possible blockage"))

        # Leak — CRIT
        if leak:
            alarms.append(self._alarm(
                "PL-005", "leak_flag", "CRIT",
                "Leak suspected — flow discrepancy >15 m³/hr — investigate immediately"))

        # PLC fault
        if fault != 0:
            alarms.append(self._alarm(
                "PL-006", "fault_code", "HIGH",
                f"PLC fault active: {data.get('fault_text', str(fault))}"))

        return alarms
