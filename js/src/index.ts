import { getSkulptFile, setupSkulpt, startServer } from "./skulpt-tools";

export interface DrafterInitOptions {
    code?: string;
    url?: string;
}

const x: pyStr = new Sk.builtin.str("hello");

export function runStudentCode(options: DrafterInitOptions) {
    setupSkulpt();

    if (options.code) {
        return startServer(options.code, "main");
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
