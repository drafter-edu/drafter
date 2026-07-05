/**
 * Test status event types for tracking student test results.
 */
import type { TelemetryRecord } from "./base";

export interface TestCaseEvent extends TelemetryRecord {
	kind: "TestCaseEvent";
	line: number;
	caller: string;
	passed: boolean;
	given: string;
	expected: string;
	given_formatted: string;
	expected_formatted: string;
	diff_html: string;
	assertion_kind: string;
}
