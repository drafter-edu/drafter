import type { BaseEvent } from "./base";

export interface RouteAddedEvent extends BaseEvent {
    event_type: "RouteAdded";
    url: string;
    signature: string;
    is_system_route: boolean;
}
