import type { Config } from "jest";

const sharedConfig = {
	preset: "ts-jest/presets/default-esm",
	testEnvironment: "<rootDir>/jest.jsdom-env.cjs",
	extensionsToTreatAsEsm: [".ts", ".tsx"],
	setupFilesAfterEnv: ["<rootDir>/src/__tests__/setup.ts"],
	moduleNameMapper: {
		"^pyodide$": "<rootDir>/src/test-utils/pyodide-shim.ts",
		// Leaflet needs real layout; components built on it are tested
		// against the recording shim instead.
		"^leaflet$": "<rootDir>/src/test-utils/leaflet-shim.ts",
		// CSS is imported as text for shadow-root injection (tsup loader);
		// tests get an empty string instead of the real stylesheet.
		"\\.css$": "<rootDir>/src/test-utils/css-stub.ts",
		"^(\\.{1,2}/.*)\\.js$": "$1",
	},
	transform: {
		"^.+\\.tsx?$": [
			"ts-jest",
			{
				useESM: true,
				tsconfig: "tsconfig.jest.json",
			},
		],
		"^.+\\.html$": "<rootDir>/src/services/tools/rawTransformer.js",
		"^.+\\.py$": "<rootDir>/src/services/tools/rawTransformer.js",
	},
	testMatch: [
		"**/__tests__/**/*.test.{ts,tsx}",
		"**/__tests__/**/*.test.{js,jsx}",
	],
	collectCoverageFrom: [
		"src/**/*.{ts,tsx}",
		"!src/**/*.d.ts",
		"!src/**/__tests__/**",
	],
	testTimeout: 30000,
};

const config: Config = {
	// Recycle a worker between test files once it holds this much memory.
	// Defense in depth only: pyodide integration files must NOT share a
	// process at all (leftover render loops from one file spike the heap
	// mid-file in later ones, which this limit cannot catch), so
	// scripts/run-integration-tests.mjs runs each of them in its own Jest
	// process. Ignored under --runInBand.
	workerIdleMemoryLimit: "1GB",
	projects: [
		{
			// Fast unit/component tests: jsdom only, no Pyodide runtime.
			...sharedConfig,
			displayName: "unit",
			testMatch: [
				// Everything directly in __tests__/ (components, engine, brokers)
				"**/__tests__/*.test.{ts,tsx}",
				"**/__tests__/transpiler/**/*.test.{ts,tsx}",
			],
		},
		{
			// Integration tests against a real Pyodide interpreter. The custom
			// environment boots Pyodide per test file when loadPyodide is set.
			...sharedConfig,
			displayName: "pyodide",
			testEnvironmentOptions: {
				loadPyodide: true,
			},
			testMatch: ["**/__tests__/pyodide/**/*.test.{ts,tsx}"],
		},
		{
			...sharedConfig,
			displayName: "skulpt",
			testMatch: ["**/__tests__/skulpt/**/*.test.{ts,tsx}"],
		},
	],
};
export default config;
