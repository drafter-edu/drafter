const MAIN_FILENAME = "main";

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

Sk.configure({ read: builtinRead, __future__: Sk.python3 });

Sk.inBrowser = false;

if (typeof Sk.console === "undefined") {
    Sk.console = {};
}

Sk.console = {
    // TODO: Move handleError into this object, and make it so that drafter is a function that creates the object
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

function startWebserver(pythonSite) {
    Sk.console.drafter.handleError = function (code, message) {
        document.body.innerHTML = `<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div><pre style="${preStyle}">${code}: ${message}</pre></div>`;
    };
    try {
        Sk.misceval
            .asyncToPromise(() =>
                Sk.importMainWithBody(
                    MAIN_FILENAME,
                    false,
                    pythonSite,
                    true
                )
            )
            .then((result) => {
                console.log(result.$d);
                handleRedirectNavigation();
            })
            .catch((e) => {
                showError(e, MAIN_FILENAME+".py", pythonSite);
            });
    } catch (e) {
        showError(e, MAIN_FILENAME+".py", pythonSite);
    }
}

function handleRedirectNavigation() {
    console.log("Handling redirect navigation if needed");
    const pathMatch = window.location.search.match(/\?(\/.+)/);
    if (pathMatch) {
        // Navigate to the target path using the Bottle mechanism
        const target = pathMatch[1].replace(/~and~/g, '&');
        Sk.bottle.changeLocation(target);
    }
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
	if (
        Sk.builtinFiles !== undefined &&
        Sk.builtinFiles["files"]["main.py"] !== undefined
    ) {
		startWebserver(Sk.builtinFiles["files"]["main.py"]);
    } else if (document.querySelector("iframe")) {
        let iframe = document.getElementsByTagName("iframe")[0];
        iframe.onload = ev => {
            let code = iframe.contentWindow.document.querySelector("pre").textContent;
            startWebserver(code);
        };
    } else {
        $.ajax({
            type: "GET",
            url: "website.py",
            success: function(contents) {
                startWebserver(contents);
            }
        });
    }
});
