interface RouteAddedEvent extends BaseEvent {
    event_type: "RouteAdded";
    url: string;
    signature: string;
}
