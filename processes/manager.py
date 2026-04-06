"""
manager.py - MORBION Processes Central Manager
OOP implementation for starting, stopping, and managing all 4 processes.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class Process:
    """
    Represents a single MORBION process.
    """
    name: str
    port: int
    folder: str
    base_path: str
    running: bool = False
    process: Optional[subprocess.Popen] = field(default=None, repr=False)
    log_file: Optional[object] = field(default=None, repr=False)

    def get_path(self) -> str:
        return os.path.join(self.base_path, self.folder)

    def get_log_path(self) -> str:
        log_dir = os.path.join(self.base_path, "logs")
        return os.path.join(log_dir, f"{self.folder}.log")

    def start(self, log_dir: str) -> bool:
        """Start the process."""
        # Check if already running (scan by port)
        existing_pid = self.find_by_port()
        if existing_pid:
            print(f"[{self.name}] Already running on port {self.port} (PID: {existing_pid})")
            return True

        if self.running and self.process:
            print(f"[{self.name}] Already running on port {self.port}")
            return True

        main_py = os.path.join(self.get_path(), "main.py")
        if not os.path.exists(main_py):
            print(f"[{self.name}] ERROR: main.py not found at {main_py}")
            return False

        os.makedirs(log_dir, exist_ok=True)
        log_path = self.get_log_path()

        try:
            log_file = open(log_path, "a")
            self.process = subprocess.Popen(
                [sys.executable, main_py],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=self.get_path(),
                start_new_session=True
            )
            self.running = True
            self.log_file = log_file
            print(f"[{self.name}] Started on port {self.port} (PID: {self.process.pid})")
            return True
        except Exception as e:
            print(f"[{self.name}] ERROR starting: {e}")
            return False

    def stop(self) -> bool:
        """Stop the process gracefully."""
        if self.running and self.process is not None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()

                if self.log_file:
                    self.log_file.close()
                    self.log_file = None

                self.running = False
                self.process = None
                print(f"[{self.name}] Stopped")
                return True
            except Exception as e:
                print(f"[{self.name}] ERROR stopping: {e}")
                return False

        # Fallback: scan for process by port
        found_pid = self.find_by_port()
        if found_pid:
            try:
                import signal
                os.kill(found_pid, signal.SIGTERM)
                time.sleep(1)
                try:
                    import psutil
                    p = psutil.Process(found_pid)
                    p.terminate()
                    p.wait(timeout=5)
                except:
                    pass
                print(f"[{self.name}] Stopped (found by port scan)")
                return True
            except Exception as e:
                print(f"[{self.name}] ERROR stopping: {e}")
                return False

        print(f"[{self.name}] Not running")
        return True

    def is_running(self) -> bool:
        """Check if process is running - ALWAYS check system state."""
        try:
            import psutil
            if self.process is not None:
                return psutil.pid_exists(self.process.pid)
            return False
        except:
            return False

    def find_by_port(self) -> Optional[int]:
        """Find process PID by port - scans system for processes listening on port."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline') or []
                    if 'main.py' in ' '.join(cmdline):
                        connections = proc.net_connections()
                        for conn in connections:
                            if conn.laddr.port == self.port:
                                return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except:
            return None

    def get_status(self) -> Dict:
        """Get process status."""
        actual_pid = self.process.pid if self.process else (self.find_by_port() if self.running else None)
        return {
            "name": self.name,
            "port": self.port,
            "running": self.running or self.find_by_port() is not None,
            "pid": actual_pid,
            "folder": self.folder
        }

    def get_logs(self, lines: int = 50) -> str:
        """Get last N lines of log."""
        log_path = self.get_log_path()
        if not os.path.exists(log_path):
            return f"[{self.name}] No log file found"

        try:
            with open(log_path, "r") as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return f"=== {self.name} (last {len(last_lines)} lines) ===\n" + "".join(last_lines)
        except Exception as e:
            return f"[{self.name}] Error reading log: {e}"


class ProcessManager:
    """
    Manages all 4 MORBION processes.
    """

    def __init__(self, base_path: str, config: Dict):
        self.base_path = base_path
        self.config = config
        self.processes: Dict[str, Process] = {}
        self._load_processes()
        self._scan_by_port()

    def _load_processes(self) -> None:
        """Load processes from config."""
        proc_config = self.config.get("processes", {})
        settings = self.config.get("settings", {})

        for key, cfg in proc_config.items():
            if cfg.get("enabled", True):
                self.processes[key] = Process(
                    name=cfg.get("name", key),
                    port=cfg.get("port", 5000),
                    folder=cfg.get("folder", key),
                    base_path=self.base_path
                )

    def _get_pid_file(self) -> str:
        return os.path.join(self.base_path, ".process_pids.json")

    def _scan_by_port(self) -> None:
        """Scan for running processes by port."""
        import psutil
        for key, proc in self.processes.items():
            found_pid = proc.find_by_port()
            if found_pid:
                try:
                    proc.process = psutil.Process(found_pid)
                    proc.running = True
                except:
                    pass

    def start_all(self) -> bool:
        """Start all enabled processes."""
        settings = self.config.get("settings", {})
        log_dir = os.path.join(self.base_path, settings.get("log_dir", "logs"))

        print("\n" + "=" * 50)
        print("  Starting all MORBION processes")
        print("=" * 50)

        success = True
        for key, proc in self.processes.items():
            if not proc.start(log_dir):
                success = False
            time.sleep(0.5)

        print("=" * 50)
        return success

    def stop_all(self) -> bool:
        """Stop all processes gracefully."""
        print("\n" + "=" * 50)
        print("  Stopping all MORBION processes")
        print("=" * 50)

        success = True
        for key, proc in self.processes.items():
            if not proc.stop():
                success = False
            time.sleep(0.5)

        print("=" * 50)
        return success

    def restart_all(self) -> bool:
        """Restart all processes."""
        print("\n" + "=" * 50)
        print("  Restarting all MORBION processes")
        print("=" * 50)

        self.stop_all()
        time.sleep(2)
        return self.start_all()

    def status_all(self) -> Dict:
        """Get status of all processes."""
        status = {}
        for key, proc in self.processes.items():
            status[key] = proc.get_status()
        return status

    def print_status(self) -> None:
        """Print status of all processes."""
        print("\n" + "=" * 60)
        print("  MORBION Processes Status")
        print("=" * 60)

        for key, proc in self.processes.items():
            status = proc.get_status()
            running = "RUNNING" if status["running"] else "STOPPED"
            pid = f"PID: {status['pid']}" if status["pid"] else ""
            print(f"  {status['name']:20} | {running:10} | Port: {status['port']:4} | {pid}")

        print("=" * 60)

    def logs_all(self, lines: int = 50, follow: bool = False) -> None:
        """Get logs from all processes."""
        if follow:
            self._follow_logs(lines)
        else:
            for key, proc in self.processes.items():
                print(proc.get_logs(lines))
                print()

    def _follow_logs(self, lines: int) -> None:
        """Follow logs from all processes (live)."""
        print("Following logs... (Press Ctrl+C to exit)")

        class LogFollower:
            def __init__(self, processes):
                self.processes = processes
                self.positions = {}
                for key, proc in processes.items():
                    log_path = proc.get_log_path()
                    if os.path.exists(log_path):
                        self.positions[key] = os.path.getsize(log_path)

            def read_new(self):
                for key, proc in self.processes.items():
                    log_path = proc.get_log_path()
                    if os.path.exists(log_path):
                        current_size = os.path.getsize(log_path)
                        if key in self.positions:
                            if current_size > self.positions[key]:
                                with open(log_path, "r") as f:
                                    f.seek(self.positions[key])
                                    new_data = f.read()
                                    if new_data:
                                        print(f"\n=== {proc.name} ===")
                                        print(new_data)
                                self.positions[key] = current_size
                        else:
                            self.positions[key] = current_size

        follower = LogFollower(self.processes)
        try:
            while True:
                follower.read_new()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped following logs")


class ConfigLoader:
    """Loads config from YAML file."""

    @staticmethod
    def load(config_path: str) -> Dict:
        """Load config from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        import yaml
        with open(config_path, "r") as f:
            return yaml.safe_load(f)


def main():
    """Main entry point."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config.yaml")

    if len(sys.argv) < 2:
        print("Usage: python manager.py <command>")
        print("Commands: start, stop, restart, status, logs, logs-f")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        config = ConfigLoader.load(config_path)
    except Exception as e:
        print(f"ERROR loading config: {e}")
        sys.exit(1)

    manager = ProcessManager(base_path, config)

    if command == "start":
        manager.start_all()
    elif command == "stop":
        manager.stop_all()
    elif command == "restart":
        manager.restart_all()
    elif command == "status":
        manager.print_status()
    elif command == "logs":
        lines = 50
        if len(sys.argv) > 2 and sys.argv[2] == "-f":
            manager.logs_all(lines=lines, follow=True)
        else:
            manager.logs_all(lines=lines)
    elif command == "logs-f":
        manager.logs_all(lines=50, follow=True)
    else:
        print(f"Unknown command: {command}")
        print("Commands: start, stop, restart, status, logs, logs-f")
        sys.exit(1)


if __name__ == "__main__":
    main()
