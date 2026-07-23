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
	projects: [
		{
			...sharedConfig,
			displayName: "pyodide",
			testMatch: [
				"**/__tests__/pyodide/**/*.test.{ts,tsx}",
				"**/__tests__/engine.test.ts",
				"**/__tests__/timer.test.ts",
				"**/__tests__/clock.test.ts",
				"**/__tests__/audio.test.ts",
				"**/__tests__/map.test.ts",
				"**/__tests__/media.test.ts",
				"**/__tests__/persistence.test.ts",
			],
		},
		{
			...sharedConfig,
			displayName: "skulpt",
			testMatch: ["**/__tests__/skulpt/**/*.test.{ts,tsx}"],
		},
	],
};
export default config;
