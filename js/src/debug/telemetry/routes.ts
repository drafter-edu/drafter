import type { TelemetryRecord } from "./base";

export interface RouteAddedEvent extends TelemetryRecord {
	kind: "RouteAdded";
	url: string;
	signature: string;
	is_system_route: boolean;
}
