import type { UpdatedStateEvent } from "./telemetry/state";
import type { RouteAddedEvent } from "./telemetry/routes";
import type {
    RequestEvent,
    ResponseEvent,
    OutcomeEvent,
    PageVisitEvent,
} from "./telemetry/request";
import type {
    DrafterError,
    DrafterWarning,
    DrafterInfo,
} from "./telemetry/errors";

export type TypedEvent =
    | RouteAddedEvent
    | UpdatedStateEvent
    | RequestEvent
    | ResponseEvent
    | OutcomeEvent
    | PageVisitEvent
    | DrafterError
    | DrafterWarning
    | DrafterInfo;

export interface TelemetryEvent {
    event_type: string;
    correlation: {
        causation_id?: number;
        route?: string;
        request_id?: number;
        response_id?: number;
        outcome_id?: number;
        dom_id?: string;
    };
    source: string;
    id: number;
    version: string;
    level?: string;
    timestamp: string;
    data?: TypedEvent;
}

