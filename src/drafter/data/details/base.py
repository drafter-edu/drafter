"""Compatibility shim: the telemetry base classes now live in drafter.data.telemetry."""

from drafter.data.telemetry import TelemetryMetadata, TelemetryRecord

__all__ = ["TelemetryMetadata", "TelemetryRecord"]
