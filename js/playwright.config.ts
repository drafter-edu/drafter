import { defineConfig } from "playwright/test";

export default defineConfig({
	testDir: "./e2e",
	// Each spec boots a real Pyodide runtime in the browser; give it room.
	timeout: 180_000,
	expect: { timeout: 15_000 },
	fullyParallel: true,
	workers: process.env.CI ? 2 : 3,
	retries: process.env.CI ? 1 : 0,
	reporter: [["list"]],
	use: {
		baseURL: "http://127.0.0.1:8787",
		trace: "retain-on-failure",
	},
	webServer: {
		command: "node e2e/server.mjs",
		url: "http://127.0.0.1:8787/harness.html",
		reuseExistingServer: true,
		timeout: 30_000,
	},
	projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
