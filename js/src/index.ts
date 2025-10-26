import { getSkulptFile, setupSkulpt, startServer } from "./skulpt-tools";

export interface DrafterInitOptions {
    target: HTMLElement | string;
    code?: string;
    url?: string;
}

export function startDrafter(options: DrafterInitOptions) {
    setupSkulpt();

    const targetElement: HTMLElement | null =
        typeof options.target === "string"
            ? document.querySelector(options.target)
            : options.target;

    if (!targetElement) {
        throw new Error("Target element not found");
    }

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

    // const mainFile = getSkulptFile("main.py");
    // if (mainFile) {
    //     console.log("Loaded main.py from skulpt builtinFiles.");
    //     startServer(mainFile);
    // } else if (document.querySelector("iframe")) {
    //     let iframe = document.getElementsByTagName("iframe")[0];
    //     iframe.onload = () => {
    //         let code =
    //             iframe.contentWindow?.document.querySelector(
    //                 "pre"
    //             )?.textContent;
    //         if (!code) {
    //             console.error("No code found in iframe.");
    //             return;
    //         }
    //         console.log("Loaded code from iframe.");
    //         startServer(code);
    //     };
    // } else {
    //     fetch("website.py")
    //         .then((response) => {
    //             if (!response.ok) {
    //                 throw new Error(
    //                     "Network response was not ok " + response.statusText
    //                 );
    //             }
    //             return response.text(); // assuming the server returns text content
    //         })
    //         .then((contents) => {
    //             console.log("Loaded code from webserver.");
    //             startServer(contents);
    //         })
    //         .catch((error) => {
    //             console.error("Fetch error:", error);
    //         });
    // }

    console.log("Drafter setup complete.");
}
