/**
 * State snapshot events for the Save/Load feature: Python reduces the
 * current state + route invocation to plain JSON data and ships it here
 * for the SaveLoadManager to store (localStorage slot) or download (file).
 * Loading sends the same plain data back; Python rebuilds the state with
 * the route-parameter converter registry and replays the route.
 *
 * Mirrors StateSnapshotEvent.to_json in
 * src/drafter/data/details/snapshot.py.
 */
import type { TelemetryRecord } from "./base";

export interface StateSnapshotEvent extends TelemetryRecord {
	kind: "StateSnapshot";
	route: string;
	/** JSON-encoded kwargs of the captured route invocation. */
	kwargs_json: string;
	/**
	 * JSON-encoded plain data of the captured state (opaque to JS), as it
	 * is now: after the captured route ran.
	 */
	state_json: string;
	/**
	 * The state as it was just before the captured route ran, encoded the
	 * same way, or "" when Python could not capture it. Sent since
	 * snapshot format version 2.
	 */
	state_before_json?: string;
	/** The state's class name at capture time (labels/diagnostics). */
	state_type: string;
	/** Recursive representation of the state, for slot previews. */
	representation: unknown;
	reason: "save" | "download";
	slot: string;
	app_title: string;
	version: number;
}
