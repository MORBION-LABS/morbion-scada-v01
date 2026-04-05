"""
MORBION SCADA Desktop — REST Client
Synchronous httpx calls for /control endpoint.
Runs in a worker thread — never on UI thread.
"""

import httpx
import logging
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

log = logging.getLogger(__name__)


class ControlResult(QObject):
    """Carries result back to UI thread via signal."""
    finished = pyqtSignal(dict)


class ControlWorker(QRunnable):
    """
    Executes POST /control in thread pool.
    Emits result dict: {ok, process, register, value, confirmed, error?}
    """

    def __init__(self, url: str, process: str, register: int, value: int, result: ControlResult):
        super().__init__()
        self._url      = url
        self._process  = process
        self._register = register
        self._value    = value
        self._result   = result

    def run(self):
        payload = {
            "process":  self._process,
            "register": self._register,
            "value":    self._value,
        }
        try:
            resp = httpx.post(self._url, json=payload, timeout=5.0)
            data = resp.json()
        except httpx.TimeoutException:
            data = {"ok": False, "error": "Request timeout"}
        except httpx.ConnectError:
            data = {"ok": False, "error": "Cannot reach server"}
        except Exception as e:
            data = {"ok": False, "error": str(e)}

        self._result.finished.emit(data)


class RestClient:
    """
    Sends control commands to server.
    Non-blocking — uses Qt thread pool.
    callback(result_dict) called on completion.
    """

    def __init__(self, host: str, port: int):
        self._control_url = f"http://{host}:{port}/control"
        self._pool        = QThreadPool.globalInstance()

    def write_register(self, process: str, register: int, value: int, callback):
        result = ControlResult()
        result.finished.connect(callback)
        worker = ControlWorker(self._control_url, process, register, value, result)
        self._pool.start(worker)
