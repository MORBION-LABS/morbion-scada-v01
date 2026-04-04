"""
MORBION SCADA Server — Historian Writer
Translates plant dict to InfluxDB line protocol points.
"""

import logging
from datetime import datetime

log = logging.getLogger(__name__)


class HistorianWriter:
    """
    Translates process snapshots to InfluxDB points.
    write_snapshot() expects plant dict from poller.
    """

    def __init__(self, influx_client):
        self._client = influx_client

    def write_snapshot(self, plant: dict) -> None:
        """
        Write a complete plant snapshot to InfluxDB.
        Each process becomes a measurement.
        """
        if self._client is None:
            return

        timestamp = datetime.now(datetime.timezone.utc)

        points = []
        for process_name, data in plant.items():
            if not data.get("online"):
                continue

            tags = {
                "process": process_name,
                "label": data.get("label", ""),
                "location": data.get("location", ""),
            }

            fields = {
                k: v for k, v in data.items()
                if k not in ("online", "process", "label", "location", "port")
            }

            from influxdb_client import Point
            point = (
                Point(process_name)
                .tag(**tags)
                .time(timestamp)
            )
            for field_name, field_value in fields.items():
                if isinstance(field_value, bool):
                    point.field(field_name, int(field_value))
                elif isinstance(field_value, (int, float)):
                    point.field(field_name, field_value)
                elif isinstance(field_value, str):
                    point.field(field_name, field_value)

            points.append(point)

        if points:
            try:
                self._client.write_points(points)
            except Exception as e:
                log.error("Failed to write to InfluxDB: %s", e)
