import type { BaseEvent } from "./base";

export type JsonType =
    | string
    | number
    | boolean
    | null
    | JsonType[]
    | { [key: string]: JsonType };

export interface InitialConfigurationEvent extends BaseEvent {
    event_type: "InitialConfiguration";
    config: Record<string, JsonType>;
}

export interface UpdatedConfigurationEvent extends BaseEvent {
    event_type: "UpdatedConfiguration";
    key: string;
    value: JsonType;
    update_default: boolean;
}
