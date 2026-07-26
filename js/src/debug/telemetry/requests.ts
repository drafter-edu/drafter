/**
 * Request/Response event types for tracking page visits.
 */
import type { TelemetryRecord } from "./base";

export interface RequestEvent extends TelemetryRecord {
	kind: "RequestEvent";
	url: string;
	action: string;
	event: string;
	kwargs: string;
	/** JSON encoding of the kwargs ("" when not JSON-serializable); used by
	 * the history Revisit button to rebuild requests after a bridge reset. */
	kwargs_json: string;
	request_id: number;
}

/** Where one bound route argument came from and how it was converted. */
export interface ArgumentProvenance {
	name: string;
	/** "form_field" | "event_detail" | "component_argument" |
	 * "framework_meta" | "state" | "default" | "framework_injected" */
	source: string;
	source_detail: string;
	/** Short repr of the raw value. */
	value: string;
	/** Display name of the annotation, or "". */
	expected_type: string;
	/** Short repr of the converted value, or null when unchanged. */
	converted: string | null;
	changed: boolean;
}

export interface RequestParseEvent extends TelemetryRecord {
	kind: "RequestParseEvent";
	request_id: number;
	representation: string;
	arguments: ArgumentProvenance[];
}

export interface ResponseEvent extends TelemetryRecord {
	kind: "ResponseEvent";
	status_code: string;
	payload_type: string;
	body_length: number;
	has_errors: boolean;
	has_warnings: boolean;
	duration_ms: number;
	response_id: number;
	request_id: number;
	formatted_page_content: string;
}
