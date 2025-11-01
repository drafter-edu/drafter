from dataclasses import dataclass, field
import traceback
from typing import Optional
from drafter.data.errors import DrafterError, DrafterInfo, DrafterWarning
from drafter.monitor.bus import get_main_event_bus
from drafter.monitor.telemetry import TelemetryCorrelation, TelemetryEvent


@dataclass
class AuditLogger:
    errors: list[DrafterError] = field(default_factory=list)
    warnings: list[DrafterWarning] = field(default_factory=list)
    info: list[DrafterInfo] = field(default_factory=list)

    def log_error(
        self,
        event_type: str,
        message: str,
        source: str,
        details: str,
        exception: Optional[Exception] = None,
        causation_id: Optional[int] = None,
        request_id: Optional[int] = None,
        response_id: Optional[int] = None,
        outcome_id: Optional[int] = None,
        dom_id: Optional[str] = None,
        route: Optional[str] = None,
    ) -> DrafterError:
        print("Logging error:", message, source, details, route, exception)
        error = DrafterError(
            message=message,
            where=source,
            details=details,
            # TODO: Skulpt does not let me do format_traceback yet
            traceback="\n".join(traceback.format_exception(exception))
            if exception
            else traceback.format_exc(),
        )
        self.errors.append(error)
        get_main_event_bus().publish(
            TelemetryEvent(
                event_type=event_type,
                correlation=TelemetryCorrelation(
                    causation_id=causation_id,
                    route=route,
                    request_id=request_id,
                    response_id=response_id,
                    outcome_id=outcome_id,
                    dom_id=dom_id,
                ),
                source=source,
                level="error",
                data=error,
            )
        )
        return error

    def log_warning(
        self,
        event_type: str,
        message: str,
        source: str,
        details: str,
        exception: Optional[Exception] = None,
        causation_id: Optional[int] = None,
        request_id: Optional[int] = None,
        response_id: Optional[int] = None,
        outcome_id: Optional[int] = None,
        dom_id: Optional[str] = None,
        route: Optional[str] = None,
    ) -> DrafterWarning:
        warning = DrafterWarning(
            message=message,
            where=source,
            details=details,
            # TODO: Skulpt does not let me do format_traceback yet
            traceback="\n".join(traceback.format_exception(exception))
            if exception
            else traceback.format_exc(),
        )
        self.warnings.append(warning)
        get_main_event_bus().publish(
            TelemetryEvent(
                event_type=event_type,
                correlation=TelemetryCorrelation(
                    causation_id=causation_id,
                    route=route,
                    request_id=request_id,
                    response_id=response_id,
                    outcome_id=outcome_id,
                    dom_id=dom_id,
                ),
                source=source,
                level="warning",
                data=warning,
            )
        )
        return warning

    def log_info(
        self,
        event_type: str,
        message: str,
        source: str,
        details: str,
        exception: Optional[Exception] = None,
        causation_id: Optional[int] = None,
        request_id: Optional[int] = None,
        response_id: Optional[int] = None,
        outcome_id: Optional[int] = None,
        dom_id: Optional[str] = None,
        route: Optional[str] = None,
    ) -> DrafterInfo:
        info = DrafterInfo(message=message, where=source, details=details)
        self.info.append(info)
        get_main_event_bus().publish(
            TelemetryEvent(
                event_type=event_type,
                correlation=TelemetryCorrelation(
                    causation_id=causation_id,
                    route=route,
                    request_id=request_id,
                    response_id=response_id,
                    outcome_id=outcome_id,
                    dom_id=dom_id,
                ),
                source=source,
                level="info",
                data=info,
            )
        )
        return info
