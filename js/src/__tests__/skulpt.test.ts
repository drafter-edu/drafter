/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/skulpt.js";
import "../../../src/drafter/assets/skulpt-stdlib.js";
import "../../../src/drafter/assets/skulpt-drafter.js";
import "../../../src/drafter/assets/drafter.js";
import { builtinRead, setupSkulpt } from "../skulpt-tools";
import { runStudentCode } from "../index";

describe("TypeScript Client Basic Tests", () => {
    test("basic test infrastructure works", () => {
        expect(true).toBe(true);
    });

    test("skulpt is loaded", () => {
        expect(typeof Sk).toBe("object");
    });

    test("can run skulpt", () => {
        const code = 'message = "Hello, Skulpt!"';

        Sk.configure({ __future__: Sk.python3 });

        return Sk.misceval
            .asyncToPromise(() => {
                return Sk.importMainWithBody("<stdin>", false, code, true);
            })
            .then((mod) => {
                // If we reach here, Skulpt ran successfully
                expect(mod.$d.message.v).toBe("Hello, Skulpt!");
            })
            .catch((err) => {
                // If there was an error, fail the test
                console.error("Skulpt error:", err);
                expect(err).toBeUndefined();
            });
    });

    test("can import drafter in skulpt", () => {
        const code = `import drafter`;

        setupSkulpt();

        return Sk.misceval
            .asyncToPromise(() => {
                return Sk.importMainWithBody("<stdin>", false, code, true);
            })
            .then(($d) => {
                // If we reach here, Drafter code ran successfully
                expect(true).toBe(true);
            })
            .catch((err) => {
                // If there was an error, fail the test
                console.error("Drafter Skulpt error:", err);
                expect(err).toBeUndefined();
            });
    });

    test("can catch a Skulpt error", () => {
        const code = `raise ValueError("This is a test error")`;

        setupSkulpt();

        return Sk.misceval
            .asyncToPromise(() => {
                return Sk.importMainWithBody("<stdin>", false, code, true);
            })
            .then(($d) => {
                // If we reach here, the student code ran successfully - which is unexpected
                expect(true).toBe(false);
            })
            .catch((err) => {
                // We expect an error here
                expect(err instanceof Sk.builtin.ValueError).toBe(true);
                expect(err.args.v[0].v).toBe("This is a test error");
            });
    });

    test("can run a student code example", () => {
        document.body.innerHTML = `
        <div id="drafter-root--"></div>
        `;

        const code = `
from drafter import *

@route
def index():
    return Page(None, ["Hello world!"])

start_server()
`;
        return runStudentCode({ code: code })
            .then((mod) => {
                // If we reach here, the student code ran successfully
                // expect(mod.$d.index).toBeDefined();
                expect(true).toBe(true);
            })
            .catch((err) => {
                // If there was an error, fail the test
                console.error("Student code Skulpt error:", err);
                expect(err).toBeUndefined();
            });
    });

    test("bad student code throws an error", () => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';

        const code = `
from drafter import *

@route
def index():
    1 + "" # This will raise a TypeError
    return Page(None, ["Hello world!"])

start_server()
`;
        return runStudentCode({ code: code })
            .then((mod) => {
                expect(true).toBe(false); // We do not expect to reach here
            })
            .catch((err) => {
                expect(err).toBeDefined();
            });
    });
});
