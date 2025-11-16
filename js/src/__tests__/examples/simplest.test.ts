/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../../src/drafter/assets/js/skulpt.js";
import "../../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../../src/drafter/assets/js/drafter.js";
import { builtinRead, setupSkulpt } from "../../skulpt-tools.js";
import { runStudentCode } from "../../index";
import * as fs from "fs";
import * as path from "path";

// Import fs and read all the files ../../../examples/
function getAllFiles() {
    const examplesDir = "../examples/";
    const fileNames = fs.readdirSync(examplesDir);
    return fileNames
        .filter((fileName: string) => fileName.endsWith(".py"))
        .map((fileName: string) => {
            const filePath = path.join(examplesDir, fileName);
            const contents = fs.readFileSync(filePath, "utf-8");
            return { fileName, contents };
        });
}

const examples = getAllFiles(); // Limit to first 3 examples for faster tests

examples.forEach(
    ({ fileName, contents }: { fileName: string; contents: string }) => {
        describe(`Example Test: ${fileName}`, () => {
            test(`can run example ${fileName}`, () => {
                document.body.innerHTML = "<div id='drafter-root--'></div>";
                return runStudentCode({ code: contents, presentErrors: false })
                    .then((mod) => {
                        // If we reach here, the student code ran successfully
                        // expect(mod.$d.index).toBeDefined();
                        expect(true).toBe(true);
                    })
                    .catch((err) => {
                        // If there was an error, fail the test
                        // expect(err).toBeUndefined();
                        throw err;
                    });
            });
        });
    }
);
