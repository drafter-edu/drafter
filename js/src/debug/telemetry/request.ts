/**
 * Request/Response/Outcome event types for tracking page visits.
 */

import type { BaseEvent } from "./base";

export interface RequestEvent extends BaseEvent {
    event_type: "RequestEvent";
    url: string;
    action: string;
    args: string;
    kwargs: string;
    request_id: number;
}

export interface ResponseEvent extends BaseEvent {
    event_type: "ResponseEvent";
    status_code: number;
    payload_type: string;
    body_length: number;
    has_errors: boolean;
    has_warnings: boolean;
    duration_ms: number;
    response_id: number;
    request_id: number;
}

export interface OutcomeEvent extends BaseEvent {
    event_type: "OutcomeEvent";
    message: string;
    success: boolean;
    outcome_id: number;
    response_id: number;
}

export interface PageVisitEvent extends BaseEvent {
    event_type: "PageVisitEvent";
    url: string;
    function_name: string;
    arguments: string;
    status_code: number;
    duration_ms: number;
    timestamp: string;
    button_pressed: string;
}
