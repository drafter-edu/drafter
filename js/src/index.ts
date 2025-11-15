import { getSkulptFile, setupSkulpt, startServer } from "./skulpt-tools";
import { initDebugPanel } from "./debug";

export interface DrafterInitOptions {
    code?: string;
    url?: string;
    presentErrors?: boolean;
}

const x: pyStr = new Sk.builtin.str("hello");

export function runStudentCode(options: DrafterInitOptions) {
    setupSkulpt();
    
    // Initialize debug panel
    initDebugPanel('drafter-debug--');

    if (options.code) {
        return startServer(options.code, "main", options.presentErrors);
    } else if (options.url) {
        return fetch(options.url)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        "Network response was not ok " + response.statusText
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
