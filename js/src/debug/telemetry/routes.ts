import type { TelemetryRecord } from "./base";

/** Structured request-parameter metadata for one route parameter. */
export interface RouteParameterInfo {
	name: string;
	/** Display name of the annotation, or "" when unannotated. */
	type: string;
	required: boolean;
	/** repr() of the default value, or null when there is no default. */
	default: string | null;
}

export interface RouteAddedEvent extends TelemetryRecord {
	kind: "RouteAdded";
	url: string;
	signature: string;
	parameters: RouteParameterInfo[];
	is_system_route: boolean;
}
