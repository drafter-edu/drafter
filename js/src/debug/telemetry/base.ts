/**
 * Base telemetry record shapes, mirroring the Python TelemetryRecord,
 * TelemetryMetadata, and Correlation dataclasses in
 * src/drafter/data/telemetry.py and src/drafter/data/correlation.py.
 */

/** JSON shape of Python TelemetryMetadata.to_json(). */
export interface TelemetryMetadata {
	source: string;
	level: string;
	id: number;
	version: string;
	timestamp: string;
}

/** JSON shape of Python Correlation.to_json(). */
export interface Correlation {
	causation_id?: number | null;
	route?: string | null;
	request_id?: number | null;
	response_id?: number | null;
	dom_id?: string | null;
	phase?: string | null;
}

/**
 * Base class for all telemetry records. Subtypes narrow `kind` and add
 * more fields.
 */
export interface TelemetryRecord {
	kind: string;
	metadata: TelemetryMetadata;
	correlation: Correlation;
}
