export type JsonValue =
	| string
	| number
	| boolean
	| null
	| JsonValue[]
	| { [key: string]: JsonValue };

export type JsonObject = Record<string, JsonValue>;

const OVERRIDES_STORAGE_KEY = "drafter.debug.configuration-overrides.v1";
const MERGE_INTO_KEY = "client_server";

function isObject(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

function sanitizeJsonObject(value: unknown): JsonObject {
	if (!isObject(value)) {
		return {};
	}
	return value as JsonObject;
}

function getStorage(): Storage | null {
	try {
		return window.localStorage;
	} catch (error) {
		console.warn(
			"[Drafter Config Overrides] localStorage unavailable",
			error,
		);
		return null;
	}
}

function cloneJsonObject(value: JsonObject): JsonObject {
	return JSON.parse(JSON.stringify(value)) as JsonObject;
}

export function getEmbeddedModifiedConfiguration(): JsonObject {
	const existingEmbedded = sanitizeJsonObject(
		(window as any).DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION,
	);
	if (Object.keys(existingEmbedded).length > 0) {
		return cloneJsonObject(existingEmbedded);
	}

	const embeddedFromTemplate = sanitizeJsonObject(
		(window as any).DRAFTER_MODIFIED_CONFIGURATION,
	);
	return cloneJsonObject(embeddedFromTemplate);
}

export function getStoredConfigurationOverrides(): JsonObject {
	const storage = getStorage();
	if (!storage) {
		return {};
	}

	const rawValue = storage.getItem(OVERRIDES_STORAGE_KEY);
	if (!rawValue) {
		return {};
	}

	try {
		const parsed = JSON.parse(rawValue) as unknown;
		return sanitizeJsonObject(parsed);
	} catch (error) {
		console.warn(
			"[Drafter Config Overrides] Failed to parse persisted overrides",
			error,
		);
		return {};
	}
}

export function setStoredConfigurationOverrides(overrides: JsonObject): void {
	const storage = getStorage();
	if (!storage) {
		return;
	}
	storage.setItem(OVERRIDES_STORAGE_KEY, JSON.stringify(overrides));
}

export function clearStoredConfigurationOverrides(): void {
	const storage = getStorage();
	if (!storage) {
		return;
	}
	storage.removeItem(OVERRIDES_STORAGE_KEY);
}

export function syncWindowConfigurationOverrides(
	overrides: JsonObject,
): JsonObject {
	const embedded = getEmbeddedModifiedConfiguration();
	const embeddedMergeTarget = sanitizeJsonObject(
		embedded[MERGE_INTO_KEY] || {},
	);
	const effective = {
		...embedded,
		[MERGE_INTO_KEY]: { ...embeddedMergeTarget, ...overrides },
	};

	(window as any).DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES =
		cloneJsonObject(overrides);
	(window as any).DRAFTER_MODIFIED_CONFIGURATION = cloneJsonObject(effective);

	return effective;
}

export function initializeRuntimeConfigurationOverrides(): void {
	const embedded = getEmbeddedModifiedConfiguration();
	(window as any).DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION =
		cloneJsonObject(embedded);

	const overrides = getStoredConfigurationOverrides();
	syncWindowConfigurationOverrides(overrides);
}
