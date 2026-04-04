"""
MORBION SCADA Server — Entry Point
Wires everything. Starts poller thread. Starts Flask.
Nothing else.

Usage:
    python3 main.py
    python3 main.py --config /path/to/config.json
"""

import json
import sys
import time
import threading
import logging
import argparse

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt= "%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("morbion.main")


def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        log.critical("Config file not found: %s", path)
        sys.exit(1)
    except json.JSONDecodeError as e:
        log.critical("Config file invalid JSON: %s", e)
        sys.exit(1)


def _ws_broadcast_loop(state, broadcast_fn, poll_rate: float) -> None:
    """Push updated state to all WS clients after every poll cycle."""
    import json as _json
    while True:
        try:
            broadcast_fn(_json.dumps(state.snapshot()))
        except Exception as e:
            log.error("WS broadcast error: %s", e)
        time.sleep(poll_rate)


def main() -> None:
    parser = argparse.ArgumentParser(description="MORBION SCADA Server v3.0")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    args = parser.parse_args()

    config = load_config(args.config)

    # ── Banner ────────────────────────────────────────────────────────────────
    print("━" * 64)
    print("  MORBION SCADA Server v3.0")
    print("  Intelligence. Precision. Vigilance.")
    print("━" * 64)
    print(f"  PLC host    : {config['plc_host']}")
    print(f"  Poll rate   : {config['poll_rate_s']}s")
    print(f"  Server port : {config['server_port']}")
    print("━" * 64)

    # ── Historian (optional) ──────────────────────────────────────────────────
    historian_writer = None
    if config.get("influxdb", {}).get("enabled"):
        try:
            from historian.historian import HistorianClient, HistorianWriter
            hc = HistorianClient(
                url    = config["influxdb"]["url"],
                token  = config["influxdb"]["token"],
                org    = config["influxdb"]["org"],
                bucket = config["influxdb"]["bucket"],
            )
            historian_writer = HistorianWriter(hc)
            print("  InfluxDB    : connected")
        except Exception as e:
            print(f"  InfluxDB    : disabled ({e})")
    else:
        print("  InfluxDB    : disabled in config")

    print("━" * 64)

    # ── Plant state ───────────────────────────────────────────────────────────
    from plant_state import PlantState
    state = PlantState()

    # ── Poller ────────────────────────────────────────────────────────────────
    from poller import Poller
    poller = Poller(config, state, historian_writer)
    poller.start()

    # Allow one full poll cycle before Flask opens for clients
    time.sleep(config["poll_rate_s"] + 0.5)

    # ── WS broadcast thread ───────────────────────────────────────────────────
    from server import app, init_server, broadcast
    init_server(state, config["plc_host"])

    broadcast_thread = threading.Thread(
        target  = _ws_broadcast_loop,
        args    = (state, broadcast, config["poll_rate_s"]),
        name    = "MorbionWSBroadcast",
        daemon  = True,
    )
    broadcast_thread.start()

    # ── Flask ─────────────────────────────────────────────────────────────────
    print(f"  REST        : http://192.168.100.30:{config['server_port']}/data")
    print(f"  WebSocket   : ws://192.168.100.30:{config['server_port']}/ws")
    print(f"  Control     : POST /control")
    print("━" * 64)

    app.run(
        host     = config["server_host"],
        port     = config["server_port"],
        debug    = False,
        threaded = True,
        use_reloader = False,
    )


if __name__ == "__main__":
    main()
