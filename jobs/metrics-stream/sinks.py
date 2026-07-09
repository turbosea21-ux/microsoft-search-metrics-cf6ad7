"""Sinks for emitted metric rows and anomaly events."""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Protocol

from .aggregations import MetricRow
from .anomaly import Anomaly


class MetricSink(Protocol):
    def emit(self, row: MetricRow) -> None: ...
    def emit_anomaly(self, anomaly: Anomaly) -> None: ...


class StdoutSink:
    def emit(self, row: MetricRow) -> None:
        print(json.dumps({"metric": asdict(row)}))

    def emit_anomaly(self, anomaly: Anomaly) -> None:
        print(json.dumps({"anomaly": asdict(anomaly)}))


class BufferedSink:
    """Collects rows and anomalies for a batched DB flush."""

    def __init__(self) -> None:
        self.rows: list[MetricRow] = []
        self.anomalies: list[Anomaly] = []

    def emit(self, row: MetricRow) -> None:
        self.rows.append(row)

    def emit_anomaly(self, anomaly: Anomaly) -> None:
        self.anomalies.append(anomaly)

    def drain(self) -> tuple[list[MetricRow], list[Anomaly]]:
        rows, anomalies = self.rows, self.anomalies
        self.rows, self.anomalies = [], []
        return rows, anomalies
