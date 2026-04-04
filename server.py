"""
MORBION SCADA Server — Flask HTTP + WebSocket Layer
Thin. Reads from PlantState only.
Writes to PLC only via POST /control.
Knows nothing about Modbus except what ModbusClient exposes.
"""

import json
import threading
import logging
from flask        import Flask, jsonify, request
from flask_cors   import CORS
from flask_sock   import Sock
from plant_state  import PlantState

log = logging.getLogger(__name__)

app  = Flask(__name__)
CORS(app, origins="*")   # allow file:// and any origin — OT lab only
sock = Sock(app)

# Module-level refs — set by init_server()
_state:    PlantState = None
_plc_host: str        = "192.168.100.20"

# WebSocket client registry
_ws_clients: set            = set()
_ws_lock:    threading.Lock = threading.Lock()

_PORT_MAP = {
    "pumping_station": 502,
    "heat_exchanger":  506,
    "boiler":          507,
    "pipeline":        508,
}

# Register index validation bounds per process
# {process: max_register_index}  (0-based, inclusive)
_MAX_REG = {
    "pumping_station": 14,
    "heat_exchanger":  16,
    "boiler":          14,
    "pipeline":        14,
}


def init_server(state: PlantState, plc_host: str) -> None:
    global _state, _plc_host
    _state    = state
    _plc_host = plc_host


def broadcast(payload: str) -> None:
    """Push payload string to all connected WebSocket clients."""
    dead = set()
    with _ws_lock:
        for ws in list(_ws_clients):
            try:
                ws.send(payload)
            except Exception:
                dead.add(ws)
        _ws_clients -= dead


# ── REST — Read ───────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    snap = _state.snapshot()
    return jsonify({
        "server":           "MORBION SCADA v3.0",
        "status":           "online",
        "processes_online": _state.processes_online(),
        "processes_total":  4,
        "poll_count":       snap["poll_count"],
        "poll_rate_ms":     snap["poll_rate_ms"],
        "server_time":      snap["server_time"],
    })


@app.route("/data")
def data_all():
    return jsonify(_state.snapshot())


@app.route("/data/<process>")
def data_process(process: str):
    valid = ("pumping_station", "heat_exchanger", "boiler", "pipeline")
    if process not in valid:
        return jsonify({"error": f"Unknown process '{process}'"}), 404
    return jsonify(_state.snapshot().get(process, {}))


@app.route("/data/alarms")
def data_alarms():
    return jsonify(_state.snapshot().get("alarms", []))


# ── REST — Control ────────────────────────────────────────────────────────────

@app.route("/control", methods=["POST"])
def control():
    """
    Write a single Modbus register via FC06.
    Body (JSON):
        process  : "pumping_station" | "heat_exchanger" | "boiler" | "pipeline"
        register : 0-based register index (integer)
        value    : 16-bit unsigned integer 0-65535
    Response:
        {ok, process, port, register, value, confirmed, error?}
    """
    if not request.is_json:
        return jsonify({"ok": False, "error": "Content-Type must be application/json"}), 400

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"ok": False, "error": "Empty or invalid JSON body"}), 400

    # ── Validate fields ───────────────────────────────────────────────────────
    process  = body.get("process")
    register = body.get("register")
    value    = body.get("value")

    if process is None or register is None or value is None:
        return jsonify({
            "ok":    False,
            "error": "Required fields: process, register, value",
        }), 400

    if process not in _PORT_MAP:
        return jsonify({
            "ok":    False,
            "error": f"Unknown process '{process}'. Valid: {list(_PORT_MAP.keys())}",
        }), 400

    if not isinstance(register, int) or not isinstance(value, int):
        return jsonify({
            "ok":    False,
            "error": "register and value must be integers",
        }), 400

    if not (0 <= register <= _MAX_REG[process]):
        return jsonify({
            "ok":    False,
            "error": f"register {register} out of range for {process} (0-{_MAX_REG[process]})",
        }), 400

    if not (0 <= value <= 65535):
        return jsonify({
            "ok":    False,
            "error": "value must be 0-65535",
        }), 400

    # ── Execute write ─────────────────────────────────────────────────────────
    port = _PORT_MAP[process]
    try:
        from modbus.client import ModbusClient, ModbusError
        client    = ModbusClient(_plc_host, port, timeout=3.0)
        confirmed = client.write_register(register, value)
        log.info("CONTROL  %s  reg=%d  val=%d  confirmed=%s", process, register, value, confirmed)
        return jsonify({
            "ok":        True,
            "process":   process,
            "port":      port,
            "register":  register,
            "value":     value,
            "confirmed": confirmed,
        })
    except Exception as e:
        log.error("CONTROL FAILED  %s  reg=%d  val=%d  error=%s", process, register, value, e)
        return jsonify({
            "ok":       False,
            "process":  process,
            "register": register,
            "value":    value,
            "error":    str(e),
        }), 500


# ── WebSocket ─────────────────────────────────────────────────────────────────

@sock.route("/ws")
def ws_endpoint(ws):
    """
    WebSocket endpoint.
    On connect: send current state immediately.
    Stay open: client sends keep-alive pings. Server ignores content.
    On disconnect: remove from registry.
    """
    with _ws_lock:
        _ws_clients.add(ws)

    # Send current state immediately on connect
    try:
        ws.send(json.dumps(_state.snapshot()))
    except Exception:
        pass

    try:
        while True:
            msg = ws.receive(timeout=60)
            if msg is None:
                break
            # client ping — ignore content, connection still alive
    except Exception:
        pass
    finally:
        with _ws_lock:
            _ws_clients.discard(ws)


# ── Root ──────────────────────────────────────────────────────────────────────

@app.route("/")
def root():
    return jsonify({
        "name":      "MORBION SCADA Server",
        "version":   "3.0",
        "endpoints": [
            "GET  /health",
            "GET  /data",
            "GET  /data/{process}",
            "GET  /data/alarms",
            "POST /control",
            "WS   /ws",
        ],
    })
