"""
modbus_server.py — Heat Exchanger Modbus TCP Server
Our own implementation. No pymodbus. Pure sockets.
Exposes all process registers to any Modbus TCP master.
Reads live values from ProcessState every scan.

Register Map:
    40001  T_hot_in           °C × 10
    40002  T_hot_out          °C × 10
    40003  T_cold_in          °C × 10
    40004  T_cold_out         °C × 10
    40005  flow_hot           L/min × 10
    40006  flow_cold          L/min × 10
    40007  pressure_hot_in    bar × 100
    40008  pressure_hot_out   bar × 100
    40009  pressure_cold_in   bar × 100
    40010  pressure_cold_out  bar × 100
    40011  Q_duty_kW          kW (integer)
    40012  efficiency         % × 10
    40013  hot_pump_speed     RPM
    40014  cold_pump_speed    RPM
    40015  hot_valve_pos      % × 10
    40016  cold_valve_pos     % × 10
    40017  fault_code         0=OK 1=PUMP 2=SENSOR 3=OVERTEMP
"""

import socket
import struct
import threading
import logging

log = logging.getLogger("modbus_server")


class ModbusServer:
    """
    Pure socket Modbus TCP server.
    Holds a register bank updated from ProcessState.
    Handles multiple concurrent client connections.
    Supports FC03 (Read Holding Registers) and FC06 (Write Single Register).
    """

    REGISTER_COUNT = 64

    def __init__(self, config: dict):
        self._host = "0.0.0.0"
        self._port = config["process"]["port"]
        self._uid  = config["process"]["unit_id"]

        self._registers = [0] * self.REGISTER_COUNT
        self._lock      = threading.Lock()
        self._running   = False
        self._server    = None

    # ── Register Update (called from main loop) ───────────────────

    def update_from_state(self, state):
        """
        Pull live values from ProcessState.
        Scale to uint16 and store in register bank.
        """
        with state:
            regs = {
                0:  self._scale(state.T_hot_in,           10.0),   # 40001
                1:  self._scale(state.T_hot_out,          10.0),   # 40002
                2:  self._scale(state.T_cold_in,          10.0),   # 40003
                3:  self._scale(state.T_cold_out,         10.0),   # 40004
                4:  self._scale(state.flow_hot,           10.0),   # 40005
                5:  self._scale(state.flow_cold,          10.0),   # 40006
                6:  self._scale(state.pressure_hot_in,   100.0),   # 40007
                7:  self._scale(state.pressure_hot_out,  100.0),   # 40008
                8:  self._scale(state.pressure_cold_in,  100.0),   # 40009
                9:  self._scale(state.pressure_cold_out, 100.0),   # 40010
                10: self._scale(state.Q_duty_kW,           1.0),   # 40011
                11: self._scale(state.efficiency,         10.0),   # 40012
                12: self._scale(state.hot_pump_speed_rpm,  1.0),   # 40013
                13: self._scale(state.cold_pump_speed_rpm, 1.0),   # 40014
                14: self._scale(state.hot_valve_position_pct,  10.0),  # 40015
                15: self._scale(state.cold_valve_position_pct, 10.0),  # 40016
                16: int(state.fault_code),                          # 40017
            }

        with self._lock:
            for idx, val in regs.items():
                self._registers[idx] = val

    @staticmethod
    def _scale(value: float, factor: float) -> int:
        """Scale float to uint16. Clamp to valid range."""
        return max(0, min(65535, int(round(value * factor))))

    # ── Server Lifecycle ──────────────────────────────────────────

    def start(self):
        self._running = True
        t = threading.Thread(target=self._serve, daemon=True)
        t.start()
        log.info(f"Modbus TCP server listening on port {self._port}")

    def stop(self):
        self._running = False
        if self._server:
            self._server.close()

    def _serve(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self._host, self._port))
        self._server.listen(5)

        while self._running:
            try:
                conn, addr = self._server.accept()
                log.info(f"Client connected: {addr}")
                t = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True)
                t.start()
            except OSError:
                break

    # ── Client Handler ────────────────────────────────────────────

    def _handle_client(self, conn: socket.socket, addr):
        with conn:
            while self._running:
                try:
                    header = self._recv_exact(conn, 7)
                    if not header:
                        break

                    tid, pid, length, uid = struct.unpack('>HHHB', header)
                    pdu = self._recv_exact(conn, length - 1)
                    if not pdu:
                        break

                    response_pdu = self._process_pdu(pdu)
                    resp_length  = 1 + len(response_pdu)
                    response     = struct.pack('>HHHB', tid, pid, resp_length, uid)
                    response    += response_pdu
                    conn.sendall(response)

                except (ConnectionError, struct.error, OSError):
                    break

        log.info(f"Client disconnected: {addr}")

    def _process_pdu(self, pdu: bytes) -> bytes:
        fc = pdu[0]

        if fc == 0x03:  # Read Holding Registers
            return self._fc03(pdu)
        elif fc == 0x06:  # Write Single Register
            return self._fc06(pdu)
        else:
            return bytes([fc | 0x80, 0x01])  # Illegal function

    def _fc03(self, pdu: bytes) -> bytes:
        addr, count = struct.unpack('>HH', pdu[1:5])
        if addr + count > self.REGISTER_COUNT:
            return bytes([0x83, 0x02])  # Illegal data address

        with self._lock:
            values = self._registers[addr:addr + count]

        data = struct.pack(f'>{count}H', *values)
        return bytes([0x03, len(data)]) + data

    def _fc06(self, pdu: bytes) -> bytes:
        addr, value = struct.unpack('>HH', pdu[1:5])
        if addr >= self.REGISTER_COUNT:
            return bytes([0x86, 0x02])

        with self._lock:
            self._registers[addr] = value

        log.info(f"FC06 Write: register {addr + 40001} = {value}")
        return pdu  # Echo back

    @staticmethod
    def _recv_exact(conn: socket.socket, n: int) -> bytes:
        data = b''
        while len(data) < n:
            chunk = conn.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Disconnected")
            data += chunk
        return data
