"""
main.py — Pipeline Pump Station Entry Point
Kenya Pipeline Company — Mombasa to Nairobi segment.
Loads config. Instantiates all equipment. Runs scan loop.
Handles graceful shutdown.
"""

import json
import time
import signal
import logging
import sys
import os

from process_state    import ProcessState
from duty_pump        import DutyPump
from standby_pump     import StandbyPump
from inlet_valve      import InletValve
from outlet_valve     import OutletValve
from flow_meter       import FlowMeter
from pressure_sensors import PressureSensors
from plc_logic        import PipelinePLC
from modbus_server    import ModbusServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("pipeline")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH  = os.path.join(BASE_DIR, "process_state.json")


def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def main():
    log.info("═" * 60)
    log.info("  MORBION Virtual ICS Lab")
    log.info("  Pipeline Pump Station — Kenya Pipeline Company")
    log.info("═" * 60)

    config        = load_config()
    scan_interval = config["process"]["scan_interval_ms"] / 1000.0
    log.info(f"Port: {config['process']['port']} | "
             f"Scan: {config['process']['scan_interval_ms']}ms")

    # ── State ─────────────────────────────────────────────────────
    state = ProcessState()
    state.restore(STATE_PATH)
    log.info("Process state restored")

    # ── Equipment ─────────────────────────────────────────────────
    duty_pump    = DutyPump(config)
    standby_pump = StandbyPump(config)
    inlet_valve  = InletValve(config)
    outlet_valve = OutletValve(config)
    flow_meter   = FlowMeter(config)
    pressures    = PressureSensors(config)

    # ── PLC ───────────────────────────────────────────────────────
    plc = PipelinePLC(config, duty_pump, standby_pump,
                      inlet_valve, outlet_valve)

    # ── Modbus Server ─────────────────────────────────────────────
    modbus = ModbusServer(config)
    modbus.start()

    # ── Start ─────────────────────────────────────────────────────
    with state:
        state.process_running = True

    log.info("Process started — all equipment initialising")

    # ── Shutdown Handler ──────────────────────────────────────────
    running = [True]

    def shutdown(sig, frame):
        log.info("Shutdown signal received")
        running[0] = False

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT,  shutdown)

    # ── Scan Loop ─────────────────────────────────────────────────
    last_save = time.time()

    while running[0]:
        t_start = time.time()

        duty_pump.update(scan_interval,    state)
        standby_pump.update(scan_interval, state)
        inlet_valve.update(scan_interval,  state)
        outlet_valve.update(scan_interval, state)
        flow_meter.update(scan_interval,   state)
        pressures.update(scan_interval,    state)
        plc.scan(state)
        modbus.update_from_state(state)

        if time.time() - last_save > 30:
            state.save(STATE_PATH)
            last_save = time.time()

        elapsed = time.time() - t_start
        time.sleep(max(0.0, scan_interval - elapsed))

    # ── Shutdown ──────────────────────────────────────────────────
    log.info("Stopping process...")
    with state:
        state.process_running = False

    duty_pump.stop()
    standby_pump.stop()
    modbus.stop()
    state.save(STATE_PATH)

    log.info("Pipeline pump station stopped cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
