import { getSkulptFile, setupSkulpt, startServer } from "./skulpt-tools";
import { setupPyodide, startServerPyodide, installPyodidePackage } from "./pyodide-tools";

export interface DrafterInitOptions {
    code?: string;
    url?: string;
    presentErrors?: boolean;
    runtime?: "skulpt" | "pyodide";
}

const x: pyStr = new Sk.builtin.str("hello");

export function runStudentCode(options: DrafterInitOptions) {
    const runtime = options.runtime || "skulpt";
    
    if (runtime === "pyodide") {
        return runStudentCodePyodide(options);
    } else {
        return runStudentCodeSkulpt(options);
    }
}

function runStudentCodeSkulpt(options: DrafterInitOptions) {
    setupSkulpt();

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

async function runStudentCodePyodide(options: DrafterInitOptions) {
    await setupPyodide();

    if (options.code) {
        return startServerPyodide(options.code, "main", options.presentErrors);
    } else if (options.url) {
        const response = await fetch(options.url);
        if (!response.ok) {
            throw new Error(
                "Network response was not ok " + response.statusText
            );
        }
        const contents = await response.text();
        return startServerPyodide(contents, "main", options.presentErrors);
    } else {
        throw new Error("Either code or url must be provided");
    }
}

// Export Pyodide-specific functions
export { setupPyodide, startServerPyodide, installPyodidePackage };

// Export Skulpt-specific functions
export { setupSkulpt, startServer as startServerSkulpt, getSkulptFile };
