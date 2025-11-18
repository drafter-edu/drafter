import Sk from "./types/skulpt/";
import type { pyBaseException, pyStr } from "./types/skulpt/";
import { DebugPanel } from "./debug";

export function builtinRead(path: string) {
    if (
        Sk.builtinFiles === undefined ||
        Sk.builtinFiles["files"][path] === undefined
    )
        throw "File not found: '" + path + "'";
    return Sk.builtinFiles["files"][path];
}

const preStyle = `background-color: #f0f0f0; padding: 4px; border: 1px solid lightgrey; margin: 0px`;

export function setupSkulpt() {
    if (typeof Sk === "undefined") {
        console.error(
            "Skulpt (global `Sk`) not found. Ensure skulpt.js and skulpt-stdlib.js are loaded before drafter.js (served from your Python assets or a CDN)."
        );
        throw new Error("Skulpt not found");
    }
    // console.log(Sk);
    if (typeof Sk.environ == "undefined") {
        Sk.environ = new Sk.builtin.dict();
    }
    Sk.environ.set$item(
        new Sk.builtin.str("DRAFTER_SKULPT"),
        Sk.builtin.bool.true$
    );

    Sk.configure({
        read: builtinRead,
        __future__: Sk.python3,
    });

    Sk.inBrowser = false;

    if (typeof Sk.console === "undefined") {
        Sk.console = {};
    }
    Sk.console.drafter = {};
    Sk.console.printPILImage = function (tag: any) {
        document.body.append(tag.image);
    };
    Sk.console.plot = function (chart: any) {
        let container = document.createElement("div");
        document.body.append(container);
        return { html: [container] };
    };
    Sk.console.getWidth = function () {
        return 300;
    };
    Sk.console.getHeight = function () {
        return 300;
    };
    Sk.console.drafter.handleError = function (code: any, message: any) {
        document.body.innerHTML = `<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div><pre style="${preStyle}">${code}: ${message}</pre></div>`;
    };

    Sk.DebugPanel = DebugPanel;

    // Example: touch the global so TS keeps types and users see it's available
    // (no-op to avoid side effects)
    void Sk;
}

export function saveSkulptFile(path: string, contents: string) {
    if (Sk.builtinFiles === undefined) {
        Sk.builtinFiles = { files: {} };
    }
    Sk.builtinFiles["files"][path] = contents;
}

export async function startServer(
    pythonCode: string,
    mainFilename = "main",
    presentErrors = true
): Promise<void> {
    saveSkulptFile(mainFilename + ".py", pythonCode);
    try {
        return Sk.misceval
            .asyncToPromise(() => {
                return Sk.importMainWithBody(
                    mainFilename,
                    false,
                    pythonCode,
                    true
                );
            })
            .then((result) => {
                console.log(result.$d);
                return result;
            })
            .catch((error) => {
                if (!presentErrors) {
                    //throw error;
                    const errorMessage = convertSkulptError(
                        error as pyBaseException,
                        mainFilename + ".py",
                        pythonCode,
                        false
                    );
                    throw errorMessage;
                }
                showError(error, mainFilename + ".py", pythonCode);
            });
    } catch (error) {
        if (!presentErrors) {
            // throw error;
            const errorMessage = convertSkulptError(
                error as pyBaseException,
                mainFilename + ".py",
                pythonCode,
                false
            );
            throw errorMessage;
        }
        showError(error as pyBaseException, mainFilename + ".py", pythonCode);
    }
}

function showError(
    err: pyBaseException,
    filenameExecuted: string,
    code: string
) {
    console.error(err);
    console.error(err.args.v[0].v);
    document.body.innerHTML = [
        "<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div>",
        presentRunError(err, filenameExecuted, code),
        "</div>",
    ].join("\n");
}

function presentRunError(
    error: pyBaseException,
    filenameExecuted: string,
    code: string
) {
    let label = error.tp$name;
    let category = "runtime";
    let message = convertSkulptError(error, filenameExecuted, code);

    return message;
}

function buildTraceback(
    error: pyBaseException,
    filenameExecuted: string,
    code: string
) {
    return error.traceback.reverse().map((frame) => {
        if (!frame) {
            return "??";
        }
        let lineno = frame.lineno;
        let file = `File <code class="filename">"${frame.filename}"</code>, `;
        let line = `on line <code class="lineno">${lineno}</code>, `;
        let scope =
            frame.scope !== "<module>" && frame.scope !== undefined
                ? `in scope ${frame.scope}`
                : "";
        let source = "";
        // console.log(filenameExecuted, frame.filename, code);
        if (frame.source !== undefined) {
            source = `\n<pre style="${preStyle}"><code>${frame.source}</code></pre>`;
        } else if (filenameExecuted === frame.filename && code) {
            const lines = code.split("\n");
            const lineIndex = lineno - 1;
            const lineContent = lines[lineIndex];
            source = `\n<pre style="${preStyle}"><code>${lineContent}</code></pre>`;
        }
        return file + line + scope + source;
    });
}

function buildTracebackNoHTML(
    error: pyBaseException,
    filenameExecuted: string,
    code: string
) {
    return error.traceback.reverse().map((frame) => {
        if (!frame) {
            return "??";
        }
        let lineno = frame.lineno;
        let file = `File "${frame.filename}", `;
        let line = `on line ${lineno}, `;
        let scope =
            frame.scope !== "<module>" && frame.scope !== undefined
                ? `in scope ${frame.scope}`
                : "";
        let source = "";
        // console.log(filenameExecuted, frame.filename, code);
        if (frame.source !== undefined) {
            source = "" + frame.source;
        } else if (filenameExecuted === frame.filename && code) {
            const lines = code.split("\n");
            const lineIndex = lineno - 1;
            const lineContent = lines[lineIndex];
            source = lineContent;
        }
        return file + line + scope + source;
    });
}

function convertSkulptError(
    error: pyBaseException,
    filenameExecuted: string,
    code: string,
    withFrame: boolean = true
) {
    let name = error.tp$name;
    let args = Sk.ffi.remapToJs(error.args);
    let top = `${name}: ${args[0]}`;
    let traceback = "";
    if (name === "TimeoutError") {
        if (error.err && error.err.traceback && error.err.traceback.length) {
            const allFrames = (
                withFrame ? buildTraceback : buildTracebackNoHTML
            )(error.err, filenameExecuted, code);
            const result = ["Traceback:"];
            if (allFrames.length > 5) {
                result.push(
                    ...allFrames.slice(0, 3),
                    `... Hiding ${
                        allFrames.length - 3
                    } other stack frames ...,`,
                    ...allFrames.slice(-3, -2)
                );
            } else {
                result.push(...allFrames);
            }
            traceback = result.join("\n<br>");
        }
    } else if (error.traceback && error.traceback.length) {
        traceback =
            (withFrame ? "<strong>Traceback:</strong><br>\n" : "Traceback:\n") +
            (withFrame ? buildTraceback : buildTracebackNoHTML)(
                error,
                filenameExecuted,
                code
            ).join("\n<br>");
    }
    if (!withFrame) {
        return top + "\n" + traceback;
    }
    return `<pre style="${preStyle}">${top}</pre>\n<br>\n${traceback}\n<br>\n<div>
    <p><strong>Advice:</strong><br>
    Some common things to check:
    <ul>
    <li>Check your site to make sure it has no errors and runs fine when not deployed.</li>
    <li>Make sure you are not using third party libraries or modules that are not supported (e.g., <code>threading</code>).</li>
    <li>Check that you are correctly referencing any files or images you are using.</li>
    </ul>
    </p>
    </div>`;
}

export function getSkulptFile(
    path: string,
    okayIfNotFound = true
): string | undefined {
    if (
        Sk.builtinFiles !== undefined &&
        Sk.builtinFiles["files"][path] !== undefined
    ) {
        return Sk.builtinFiles["files"][path];
    } else {
        if (okayIfNotFound) {
            return undefined;
        } else {
            throw new Error("File not found: '" + path + "'");
        }
    }
}
