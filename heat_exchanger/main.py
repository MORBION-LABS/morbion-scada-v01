"""
main.py — Heat Exchanger Station Entry Point
Loads config. Instantiates all equipment. Runs the scan loop.
Handles graceful shutdown.
"""

import json
import time
import signal
import logging
import sys
import os

from process_state  import ProcessState
from hot_pump       import HotPump
from cold_pump      import ColdPump
from control_valve  import ControlValve
from shell_and_tube import ShellAndTube
from plc_logic      import HeatExchangerPLC
from modbus_server  import ModbusServer

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("heat_exchanger")

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH  = os.path.join(BASE_DIR, "process_state.json")


def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def main():
    log.info("═" * 60)
    log.info("  MORBION Virtual ICS Lab")
    log.info("  Heat Exchanger Station — KenGen Olkaria")
    log.info("═" * 60)

    # ── Load Config ───────────────────────────────────────────────
    config = load_config()
    scan_interval = config["process"]["scan_interval_ms"] / 1000.0
    log.info(f"Port: {config['process']['port']} | "
             f"Scan: {config['process']['scan_interval_ms']}ms")

    # ── Instantiate State ─────────────────────────────────────────
    state = ProcessState()
    state.restore(STATE_PATH)
    log.info("Process state restored")

    # ── Instantiate Equipment ─────────────────────────────────────
    hot_pump    = HotPump(config)
    cold_pump   = ColdPump(config)
    hot_valve   = ControlValve("hot_valve",  config)
    cold_valve  = ControlValve("cold_valve", config)
    exchanger   = ShellAndTube(config)

    # ── Instantiate PLC ───────────────────────────────────────────
    plc = HeatExchangerPLC(config, hot_pump, cold_pump,
                           hot_valve, cold_valve)

    # ── Instantiate Modbus Server ─────────────────────────────────
    modbus = ModbusServer(config)
    modbus.start()

    # ── Start Process ─────────────────────────────────────────────
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

    # ── Main Scan Loop ────────────────────────────────────────────
    last_save = time.time()

    while running[0]:
        t_start = time.time()

        # Update all equipment (each owns its own physics)
        hot_pump.update(scan_interval,   state)
        cold_pump.update(scan_interval,  state)
        hot_valve.update(scan_interval)
        cold_valve.update(scan_interval)
        exchanger.update(scan_interval,  state)

        # PLC scan cycle
        plc.scan(state)

        # Update Modbus registers from live state
        modbus.update_from_state(state)

        # Periodic state persistence (every 30 seconds)
        if time.time() - last_save > 30:
            state.save(STATE_PATH)
            last_save = time.time()

        # Maintain scan rate
        elapsed = time.time() - t_start
        sleep   = max(0.0, scan_interval - elapsed)
        time.sleep(sleep)

    # ── Graceful Shutdown ─────────────────────────────────────────
    log.info("Stopping process...")
    with state:
        state.process_running = False

    hot_pump.stop()
    cold_pump.stop()
    modbus.stop()
    state.save(STATE_PATH)

    log.info("Heat exchanger station stopped cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
