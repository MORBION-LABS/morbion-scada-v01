"""
main.py — Boiler Steam Generation Entry Point
EABL/Bidco Industrial Steam Plant.
Loads config. Instantiates all equipment. Runs scan loop.
Handles graceful shutdown.
"""

import json
import time
import signal
import logging
import sys
import os

from process_state   import ProcessState
from burner          import Burner
from drum            import Drum
from feedwater_pump  import FeedwaterPump
from steam_valve     import SteamValve
from feedwater_valve import FeedwaterValve
from blowdown_valve  import BlowdownValve
from plc_logic       import BoilerPLC
from modbus_server   import ModbusServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("boiler")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH  = os.path.join(BASE_DIR, "process_state.json")


def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def main():
    log.info("═" * 60)
    log.info("  MORBION Virtual ICS Lab")
    log.info("  Boiler Steam Generation — EABL/Bidco")
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
    burner         = Burner(config)
    drum           = Drum(config)
    fw_pump        = FeedwaterPump(config)
    steam_valve    = SteamValve(config)
    fw_valve       = FeedwaterValve(config)
    blowdown_valve = BlowdownValve(config)

    # ── PLC ───────────────────────────────────────────────────────
    plc = BoilerPLC(config, burner, fw_pump,
                    steam_valve, fw_valve, blowdown_valve)

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

        burner.update(scan_interval,         state)
        fw_pump.update(scan_interval,        state)
        steam_valve.update(scan_interval,    state)
        fw_valve.update(scan_interval,       state)
        blowdown_valve.update(scan_interval, state)
        drum.update(scan_interval,           state)
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

    burner.command(0)
    fw_pump.stop()
    modbus.stop()
    state.save(STATE_PATH)

    log.info("Boiler steam generation stopped cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
