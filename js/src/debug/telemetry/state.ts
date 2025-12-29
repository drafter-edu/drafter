export type StateItem = { name: string; type: string; value: string };

export interface UpdatedStateEvent extends BaseEvent {
    event_type: "UpdatedState";
    html: string;
    items?: StateItem[];
}
