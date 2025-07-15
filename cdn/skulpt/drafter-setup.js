const MAIN_FILENAME = "anonymous";

if (typeof Sk.environ == "undefined") {
    Sk.environ = new Sk.builtin.dict();
}
Sk.environ.set$item(new Sk.builtin.str("DRAFTER_SKULPT"), Sk.builtin.bool.true$);

function builtinRead(x) {
    if (
        Sk.builtinFiles === undefined ||
        Sk.builtinFiles["files"][x] === undefined
    )
        throw "File not found: '" + x + "'";
    return Sk.builtinFiles["files"][x];
}
// (Sk.TurtleGraphics || (Sk.TurtleGraphics = {})).target = "mycanvas";
Sk.BottleSiteTarget = "#website";

// Sk.configure({ read: builtinRead, __future__: Sk.python3 });
Sk.configure({ read: builtinRead, python3: true });
Sk.syspath.push("src/student")

Sk.inBrowser = false;

Sk.console = {
    drafter: {},
    printPILImage: function (img) {
        document.body.append(img.image);
    },
    plot: function (chart) {
        let container = document.createElement("div");
        document.body.append(container);
        return {"html": [container]};
    },
    getWidth: function() {
        return 300;
    },
    getHeight: function() {
        return 300;
    }
};

$.ajaxSetup({ cache: false });

const preStyle = `background-color: #f0f0f0; padding: 4px; border: 1px solid lightgrey; margin: 0px`;

let module = {}

function startWebserver(route) {
    execPython(`
import main
from drafter import get_main_server

ORIGINAL_STATE = get_main_server().dump_state()
`)
        .then(() => {
            localStorage.setItem("original-state", module.ORIGINAL_STATE.v);
            localStorage.setItem("state", localStorage.getItem("state") ||
                localStorage.getItem("original-state"));
            localStorage.setItem("page-history",
                localStorage.getItem("page-history") || "");
            goToRoute(route);
        })
}

async function execPython(python) {
    Sk.console.drafter.handleError = function (code, message) {
        document.body.innerHTML = `<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div><pre style="${preStyle}">${code}: ${message}</pre></div>`;
    };
    try {
        await Sk.misceval.asyncToPromise(() =>
            Sk.importMainWithBody(MAIN_FILENAME, false, python, true)
        )
        .then((result) => console.log(module = result.$d))
        .catch((e) => {
            showError(e, MAIN_FILENAME+".py", python);
        });
    } catch (e) {
        showError(e, MAIN_FILENAME+".py", python);
    }
}

function goToRoute(route, args=btoa("[]"), kwargs=btoa("{}")) {
    python = `
import main
from drafter import render_route

SITE, STATE, PAGE_HISTORY = render_route('${route}',
                           '''${localStorage.getItem("state")}''',
                           '''${localStorage.getItem("page-history")}''',
                           '${args}', '${kwargs}',
                           '${getAllInputs()}')
`
    execPython(python).then(() => {
        document.getElementById("website").innerHTML = module.SITE.v;
        localStorage.setItem("state", module.STATE.v);
        localStorage.setItem("page-history", module.PAGE_HISTORY.v);
        localStorage.setItem("route", route);
    });
}

function getAllInputs() {
    const inputs = document.getElementsByTagName("input");
    let parsedInputs = {};
    for (let input of inputs) {
        parsedInputs[input.name] = input.value;
    }
    return btoa(JSON.stringify(parsedInputs));
}

function showError(err, filenameExecuted, code) {
    console.error(err);
    console.error(err.args.v[0].v);
    document.body.innerHTML = [
        "<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div>",
        presentRunError(err, filenameExecuted, code),
        "</div>"].join("\n");
}

function presentRunError(error, filenameExecuted, code) {
    let label = error.tp$name;
    let category = "runtime";
    let message = convertSkulptError(error, filenameExecuted, code);

    return message;

    /*let linesError = [];
    if (lineno !== undefined && lineno !== null) {
        linesError.push(lineno);
    }*/
}

function buildTraceback(error, filenameExecuted, code) {
    return error.traceback.map(frame => {
        if (!frame) {
            return "??";
        }
        let lineno = frame.lineno;
        let file = `File <code class="filename">"${frame.filename}"</code>, `;
        let line = `on line <code class="lineno">${lineno}</code>, `;
        let scope = (frame.scope !== "<module>" &&
        frame.scope !== undefined) ? `in scope ${frame.scope}` : "";
        let source = "";
        console.log(filenameExecuted, frame.filename, code);
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

function convertSkulptError(error, filenameExecuted, code) {
    let name = error.tp$name;
    let args = Sk.ffi.remapToJs(error.args);
    let top = `${name}: ${args[0]}`;
    let traceback = "";
    if (name === "TimeoutError") {
        if (error.err && error.err.traceback && error.err.traceback.length) {
            const allFrames = buildTraceback(error.err, filenameExecuted, code);
            const result = ["Traceback:"];
            if (allFrames.length > 5) {
                result.push(...allFrames.slice(0, 3),
                            `... Hiding ${allFrames.length - 3} other stack frames ...,`,
                            ...allFrames.slice(-3, -2));
            } else {
                result.push(...allFrames);
            }
            traceback = result.join("\n<br>");
        }
    } else if (error.traceback && error.traceback.length) {
        traceback = "<strong>Traceback:</strong><br>\n" + buildTraceback(error, filenameExecuted, code).join("\n<br>");
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

$(document).ready(function() {
    try {
        compilePython(); // should be defined in index.html, but catch it if it isn't
        // execPython("import main");
        localStorage.setItem("route", localStorage.getItem("route") || "/");
        startWebserver(localStorage.getItem("route"));
    }
    catch {
        if (Sk.builtinFiles !== undefined) {
            const files = Sk.builtinFiles["files"];
            const main = files["main.py"] || files["src/student/main.py"];
            if (main) {
                execPython(main);
                return;
            }
        }
        if (document.querySelector("iframe")) {
            let iframe = document.getElementsByTagName("iframe")[0];
            iframe.onload = ev => {
                let code = iframe.contentWindow.document.querySelector("pre").textContent;
                execPython(code);
            };
        } else {
            $.ajax({
                type: "GET",
                url: "website.py",
                success: function(contents) {
                    execPython(contents);
                }
            });
        }
    }
});
