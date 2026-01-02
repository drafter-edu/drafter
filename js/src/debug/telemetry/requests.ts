/**
 * Request/Response event types for tracking page visits.
 */

export interface RequestEvent extends BaseEvent {
    event_type: "RequestEvent";
    url: string;
    action: string;
    event: string;
    kwargs: string;
    request_id: number;
}

export interface RequestParseEvent extends BaseEvent {
    event_type: "RequestParseEvent";
    request_id: number;
    representation: string;
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
    formatted_page_content: string;
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
