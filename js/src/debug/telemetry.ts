import type {
	InitialConfigurationEvent,
	UpdatedConfigurationEvent,
} from "./telemetry/config";
import type { ErrorTelemetryRecord } from "./telemetry/errors";
import type {
	RequestEvent,
	RequestParseEvent,
	ResponseEvent,
} from "./telemetry/requests";
import type { RouteAddedEvent } from "./telemetry/routes";
import type { UpdatedStateEvent } from "./telemetry/state";
import type { TestCaseEvent } from "./telemetry/tests";
import type { TelemetryRecord } from "./telemetry/base";

export type { TelemetryRecord } from "./telemetry/base";

/**
 * Records with a literal `kind`, usable as a discriminated union.
 */
export type TypedRecord =
	| RouteAddedEvent
	| UpdatedStateEvent
	| RequestEvent
	| RequestParseEvent
	| ResponseEvent
	| TestCaseEvent
	| InitialConfigurationEvent
	| UpdatedConfigurationEvent;

/**
 * Any record the debug panel may receive: a known typed record or an
 * error record (whose `kind` is the error's stable id).
 */
export type AnyTelemetryRecord =
	| TypedRecord
	| ErrorTelemetryRecord
	| TelemetryRecord;
