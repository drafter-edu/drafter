/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/skulpt.js";
import "../../../src/drafter/assets/skulpt-stdlib.js";
import "../../../src/drafter/assets/skulpt-drafter.js";
import "../../../src/drafter/assets/drafter.js";
import { builtinRead, setupSkulpt } from "../skulpt-tools";

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
            .then(($d) => {
                // If we reach here, Skulpt ran successfully
                expect(true).toBe(true);
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
});
