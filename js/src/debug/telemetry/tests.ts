/**
 * Test status event types for tracking student test results.
 */

import type { BaseEvent } from "./base";

export interface TestCaseEvent extends BaseEvent {
    event_type: "TestCaseEvent";
    line: number;
    caller: string;
    passed: boolean;
    given: string;
    expected: string;
    diff_html: string;
}

export interface TestSummaryEvent extends BaseEvent {
    event_type: "TestSummaryEvent";
    total: number;
    passed: number;
    failed: number;
}
