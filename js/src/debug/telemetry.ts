export interface TelemetryEvent {
    event_type: string;
    correlation: {
        causation_id?: number;
        route?: string;
        request_id?: number;
        response_id?: number;
        outcome_id?: number;
        dom_id?: string;
    };
    source: string;
    id: number;
    version: string;
    level?: string;
    timestamp: string;
    data?: any;
}
