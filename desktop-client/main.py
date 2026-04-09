"""
MORBION SCADA Desktop — Entry Point

Usage:
     main.py
     main.py --config /path/to/config.json

Requirements:
    pip install PyQt6 websockets httpx pyqtgraph
"""

import sys
import json
import logging
import argparse

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import Qt
from main_window     import MorbionMainWindow


def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config not found: {path} — using defaults")
        return {
            "server": {"host": host, "port": 5000},
            "ui":     {
                "window_title":           "MORBION SCADA v3.0",
                "window_width":           1600,
                "window_height":          950,
                "sparkline_points":       120,
                "logo_path":              "",
                "background_image_path":  "",
                "background_opacity":     0.08,
            }
        }
    except json.JSONDecodeError as e:
        print(f"Config JSON error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="MORBION SCADA Desktop v3.0")
    parser.add_argument("--config", default="config.json")
    args   = parser.parse_args()
    config = load_config(args.config)

    app = QApplication(sys.argv)

    window = MorbionMainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
