import type { TelemetryRecord } from "./base";

export type JsonType =
	| string
	| number
	| boolean
	| null
	| JsonType[]
	| { [key: string]: JsonType };

export interface InitialConfigurationEvent extends TelemetryRecord {
	kind: "InitialConfiguration";
	config: Record<string, JsonType>;
}

export interface UpdatedConfigurationEvent extends TelemetryRecord {
	kind: "UpdatedConfiguration";
	key: string;
	value: JsonType;
	update_default: boolean;
}
