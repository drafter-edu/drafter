/**
 * Test status event types for tracking student test results.
 */

export interface TestCaseEvent extends BaseEvent {
    event_type: "TestCaseEvent";
    line: number;
    caller: string;
    passed: boolean;
    given: string;
    expected: string;
    diff_html: string;
}
