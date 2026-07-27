import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	clearStoredConfigurationOverrides,
	getEmbeddedModifiedConfiguration,
	getStoredConfigurationOverrides,
	initializeRuntimeConfigurationOverrides,
	setStoredConfigurationOverrides,
	syncWindowConfigurationOverrides,
} from "../config_overrides";

const STORAGE_KEY = "drafter.debug.configuration-overrides.v1";

const anyWindow = window as any;

function withBrokenLocalStorage(callback: () => void): void {
	const original = Object.getOwnPropertyDescriptor(window, "localStorage");
	Object.defineProperty(window, "localStorage", {
		configurable: true,
		get() {
			throw new Error("localStorage access denied");
		},
	});
	try {
		callback();
	} finally {
		if (original) {
			Object.defineProperty(window, "localStorage", original);
		}
	}
}

describe("config overrides", () => {
	let warnSpy: ReturnType<typeof jest.spyOn>;

	beforeEach(() => {
		localStorage.clear();
		delete anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION;
		delete anyWindow.DRAFTER_MODIFIED_CONFIGURATION;
		delete anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES;
		warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
	});

	afterEach(() => {
		warnSpy.mockRestore();
		localStorage.clear();
		delete anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION;
		delete anyWindow.DRAFTER_MODIFIED_CONFIGURATION;
		delete anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES;
	});

	describe("getEmbeddedModifiedConfiguration", () => {
		test("returns an empty object when no window globals are set", () => {
			expect(getEmbeddedModifiedConfiguration()).toEqual({});
		});

		test("falls back to DRAFTER_MODIFIED_CONFIGURATION template", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = { theme: "dark" };
			expect(getEmbeddedModifiedConfiguration()).toEqual({ theme: "dark" });
		});

		test("prefers a non-empty embedded snapshot over the template", () => {
			anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION = { a: 1 };
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = { b: 2 };
			expect(getEmbeddedModifiedConfiguration()).toEqual({ a: 1 });
		});

		test("an empty embedded snapshot falls back to the template", () => {
			anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION = {};
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = { b: 2 };
			expect(getEmbeddedModifiedConfiguration()).toEqual({ b: 2 });
		});

		test("non-object globals are sanitized to an empty object", () => {
			anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION = ["not", "obj"];
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = "nope";
			expect(getEmbeddedModifiedConfiguration()).toEqual({});

			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = null;
			expect(getEmbeddedModifiedConfiguration()).toEqual({});

			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = 42;
			expect(getEmbeddedModifiedConfiguration()).toEqual({});
		});

		test("returns a deep clone, not the live window object", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				nested: { value: 1 },
			};
			const result = getEmbeddedModifiedConfiguration();
			(result.nested as Record<string, number>).value = 99;
			expect(anyWindow.DRAFTER_MODIFIED_CONFIGURATION.nested.value).toBe(1);
		});
	});

	describe("getStoredConfigurationOverrides", () => {
		test("returns an empty object when nothing is stored", () => {
			expect(getStoredConfigurationOverrides()).toEqual({});
		});

		test("parses a stored JSON object", () => {
			localStorage.setItem(
				STORAGE_KEY,
				JSON.stringify({ debug: true, port: 8080 }),
			);
			expect(getStoredConfigurationOverrides()).toEqual({
				debug: true,
				port: 8080,
			});
		});

		test("tolerates corrupt JSON with a warning", () => {
			localStorage.setItem(STORAGE_KEY, "{not valid json!");
			expect(getStoredConfigurationOverrides()).toEqual({});
			expect(warnSpy).toHaveBeenCalledWith(
				expect.stringContaining("Failed to parse persisted overrides"),
				expect.anything(),
			);
		});

		test("sanitizes stored non-object JSON to an empty object", () => {
			for (const raw of ["[1,2]", '"str"', "42", "null", "true"]) {
				localStorage.setItem(STORAGE_KEY, raw);
				expect(getStoredConfigurationOverrides()).toEqual({});
			}
		});

		test("returns an empty object with a warning when localStorage throws", () => {
			withBrokenLocalStorage(() => {
				expect(getStoredConfigurationOverrides()).toEqual({});
			});
			expect(warnSpy).toHaveBeenCalledWith(
				expect.stringContaining("localStorage unavailable"),
				expect.anything(),
			);
		});
	});

	describe("setStoredConfigurationOverrides", () => {
		test("persists overrides under the versioned storage key", () => {
			setStoredConfigurationOverrides({ debug: true });
			expect(localStorage.getItem(STORAGE_KEY)).toEqual(
				JSON.stringify({ debug: true }),
			);
		});

		test("round-trips through getStoredConfigurationOverrides", () => {
			const overrides = { a: 1, nested: { b: [1, 2, 3] } };
			setStoredConfigurationOverrides(overrides);
			expect(getStoredConfigurationOverrides()).toEqual(overrides);
		});

		test("does not throw when localStorage is unavailable", () => {
			withBrokenLocalStorage(() => {
				expect(() =>
					setStoredConfigurationOverrides({ a: 1 }),
				).not.toThrow();
			});
		});
	});

	describe("clearStoredConfigurationOverrides", () => {
		test("removes the stored key", () => {
			setStoredConfigurationOverrides({ a: 1 });
			clearStoredConfigurationOverrides();
			expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
			expect(getStoredConfigurationOverrides()).toEqual({});
		});

		test("is a no-op when nothing is stored", () => {
			expect(() => clearStoredConfigurationOverrides()).not.toThrow();
		});

		test("does not throw when localStorage is unavailable", () => {
			withBrokenLocalStorage(() => {
				expect(() => clearStoredConfigurationOverrides()).not.toThrow();
			});
		});
	});

	describe("syncWindowConfigurationOverrides", () => {
		test("with no embedded config, nests overrides under client_server", () => {
			const effective = syncWindowConfigurationOverrides({ debug: true });
			expect(effective).toEqual({ client_server: { debug: true } });
			expect(anyWindow.DRAFTER_MODIFIED_CONFIGURATION).toEqual({
				client_server: { debug: true },
			});
			expect(anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES).toEqual({
				debug: true,
			});
		});

		test("merges overrides into the embedded client_server section", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: { port: 8080, debug: false },
				other_section: { keep: "me" },
			};
			const effective = syncWindowConfigurationOverrides({ debug: true });
			expect(effective).toEqual({
				client_server: { port: 8080, debug: true },
				other_section: { keep: "me" },
			});
		});

		test("sanitizes a non-object embedded client_server value", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: "corrupt",
				other: 1,
			};
			const effective = syncWindowConfigurationOverrides({ a: 1 });
			expect(effective).toEqual({ client_server: { a: 1 }, other: 1 });
		});

		test("empty overrides leave the embedded config unchanged", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: { port: 8080 },
			};
			const effective = syncWindowConfigurationOverrides({});
			expect(effective).toEqual({ client_server: { port: 8080 } });
			expect(anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES).toEqual(
				{},
			);
		});

		test("window globals are clones, detached from inputs and return value", () => {
			const overrides = { debug: true };
			const effective = syncWindowConfigurationOverrides(overrides);

			overrides.debug = false;
			expect(
				anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES.debug,
			).toBe(true);

			(effective.client_server as Record<string, boolean>).debug = false;
			expect(
				anyWindow.DRAFTER_MODIFIED_CONFIGURATION.client_server.debug,
			).toBe(true);
		});

		test("uses the embedded snapshot in preference to the mutated template", () => {
			anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION = {
				client_server: { source: "embedded" },
			};
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: { source: "template" },
			};
			const effective = syncWindowConfigurationOverrides({});
			expect(effective).toEqual({
				client_server: { source: "embedded" },
			});
		});
	});

	describe("initializeRuntimeConfigurationOverrides", () => {
		test("with nothing set, installs empty defaults", () => {
			initializeRuntimeConfigurationOverrides();
			expect(anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION).toEqual({});
			expect(anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES).toEqual(
				{},
			);
			expect(anyWindow.DRAFTER_MODIFIED_CONFIGURATION).toEqual({
				client_server: {},
			});
		});

		test("snapshots the template and applies stored overrides", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: { port: 8080 },
				extra: "kept",
			};
			setStoredConfigurationOverrides({ debug: true });

			initializeRuntimeConfigurationOverrides();

			expect(anyWindow.DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION).toEqual({
				client_server: { port: 8080 },
				extra: "kept",
			});
			expect(anyWindow.DRAFTER_MODIFIED_CONFIGURATION).toEqual({
				client_server: { port: 8080, debug: true },
				extra: "kept",
			});
			expect(anyWindow.DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES).toEqual({
				debug: true,
			});
		});

		test("repeated initialization keeps merging against the original snapshot", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: { port: 8080 },
			};
			setStoredConfigurationOverrides({ debug: true });
			initializeRuntimeConfigurationOverrides();

			// The template global has now been replaced by the merged result;
			// a second initialization must still merge against the original
			// embedded snapshot, not the merged output.
			setStoredConfigurationOverrides({ verbose: true });
			initializeRuntimeConfigurationOverrides();

			expect(anyWindow.DRAFTER_MODIFIED_CONFIGURATION).toEqual({
				client_server: { port: 8080, verbose: true },
			});
			expect(
				anyWindow.DRAFTER_MODIFIED_CONFIGURATION.client_server.debug,
			).toBeUndefined();
		});

		test("corrupt stored overrides fall back to the embedded config", () => {
			anyWindow.DRAFTER_MODIFIED_CONFIGURATION = {
				client_server: { port: 8080 },
			};
			localStorage.setItem(STORAGE_KEY, "{{{");

			initializeRuntimeConfigurationOverrides();

			expect(anyWindow.DRAFTER_MODIFIED_CONFIGURATION).toEqual({
				client_server: { port: 8080 },
			});
			expect(warnSpy).toHaveBeenCalled();
		});
	});
});
