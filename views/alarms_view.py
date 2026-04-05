"""
MORBION — Alarms View
All active alarms. All processes. Sortable table.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QPushButton
)
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QColor

from views.base_view import BaseView
from theme import SEV_COLORS, C_MUTED, C_TEXT2, C_ACCENT


class AlarmsView(BaseView):

    def __init__(self, rest_client, parent=None):
        super().__init__(rest_client, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Summary bar
        bar = QHBoxLayout()
        self._total_lbl = QLabel("ACTIVE ALARMS: 0")
        self._total_lbl.setStyleSheet(
            f"color:{C_ACCENT};font-size:12px;letter-spacing:2px;font-weight:bold;")
        self._crit_lbl = QLabel("CRIT: 0")
        self._crit_lbl.setStyleSheet(f"color:#ff3333;font-size:11px;")
        self._high_lbl = QLabel("HIGH: 0")
        self._high_lbl.setStyleSheet(f"color:#ff8800;font-size:11px;")
        bar.addWidget(self._total_lbl)
        bar.addWidget(self._crit_lbl)
        bar.addWidget(self._high_lbl)
        bar.addStretch()
        layout.addLayout(bar)

        # Table
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["SEV", "PROCESS", "TAG", "DESCRIPTION", "TIME", "ID"])
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setSortingEnabled(True)
        self._table.setColumnWidth(0, 55)
        self._table.setColumnWidth(1, 140)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(4, 70)
        self._table.setColumnWidth(5, 70)
        layout.addWidget(self._table)

        # Empty message
        self._empty = QLabel("● ALL CLEAR — No active alarms across all processes")
        self._empty.setStyleSheet(
            f"color:{C_MUTED};font-size:12px;letter-spacing:1px;")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty)

    def update_data(self, plant: dict):
        alarms = plant.get("alarms", []) if isinstance(plant, dict) else plant
        if not isinstance(alarms, list):
            alarms = []

        crit = sum(1 for a in alarms if a.get("sev") == "CRIT")
        high = sum(1 for a in alarms if a.get("sev") == "HIGH")

        self._total_lbl.setText(f"ACTIVE ALARMS: {len(alarms)}")
        self._crit_lbl.setText(f"CRIT: {crit}")
        self._high_lbl.setText(f"HIGH: {high}")
        self._empty.setVisible(len(alarms) == 0)
        self._table.setVisible(len(alarms) > 0)

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(alarms))
        for row, a in enumerate(alarms):
            sev   = a.get("sev", "LOW")
            color = QColor(SEV_COLORS.get(sev, C_MUTED))
            vals  = [
                sev,
                a.get("process", "—").replace("_", " ").upper(),
                a.get("tag", "—"),
                a.get("desc", "—"),
                a.get("ts", "—"),
                a.get("id", "—"),
            ]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(str(text))
                item.setForeground(color)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, col, item)
        self._table.setSortingEnabled(True)
