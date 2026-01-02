import type {
    DrafterError,
    DrafterWarning,
    DrafterInfo,
} from "./telemetry/errors";
import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
    PageVisitEvent,
} from "./telemetry/requests";
import type { RouteAddedEvent } from "./telemetry/routes";
import type { UpdatedStateEvent } from "./telemetry/state";
import type { TestCaseEvent } from "./telemetry/tests";

export type TypedEvent =
    | RouteAddedEvent
    | UpdatedStateEvent
    | RequestEvent
    | RequestParseEvent
    | ResponseEvent
    | PageVisitEvent
    | DrafterError
    | DrafterWarning
    | DrafterInfo
    | TestCaseEvent;

export interface TelemetryEvent {
    event_type: string;
    correlation: {
        causation_id?: number;
        route?: string;
        request_id?: number;
        response_id?: number;
        dom_id?: string;
    };
    source: string;
    id: number;
    version: string;
    level?: string;
    timestamp: string;
    data?: TypedEvent;
}
