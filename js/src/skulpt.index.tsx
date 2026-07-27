import { reportSystemError, type DrafterInitOptions } from "./bridge/engine";
import {
	getSkulptFile,
	setupDrafterConfigfile,
	setupSkulpt,
	startServer,
} from "./skulpt_bridge/skulpt-tools";
import { initializeRuntimeConfigurationOverrides } from "./config_overrides";
export * from "./common.index";

export { clearDrafterSiteRoot, reportSystemError } from "./bridge/engine";

const x: pyStr = new Sk.builtin.str("hello");

initializeRuntimeConfigurationOverrides();

export function runStudentCode(options: DrafterInitOptions) {
	try {
		setupSkulpt();
	} catch (error) {
		throw reportSystemError({
			id: "runtime.skulpt_setup_failed",
			category: "runtime",
			message: "Failed to set up Skulpt",
			error,
			context: { phase: "setup" },
		});
	}
	setupDrafterConfigfile();

	if (options.code) {
		return startServer(options.code, "main", options.presentErrors);
	} else if (options.url) {
		return fetch(options.url)
			.then((response) => {
				if (!response.ok) {
					throw new Error(
						"Network response was not ok " + response.statusText,
					);
				}
				return response.text(); // assuming the server returns text content
			})
			.then((contents) => {
				return startServer(contents, "main");
			});
	} else {
		throw new Error("Either code or url must be provided");
	}

	console.log("Drafter setup complete.");
}
