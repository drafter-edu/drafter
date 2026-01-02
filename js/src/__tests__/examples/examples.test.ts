/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../../src/drafter/assets/js/skulpt.js";
import "../../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../../src/drafter/assets/js/drafter.js";
import "./d3.6.3.1.min.js";
import { builtinRead, setupSkulpt } from "../../skulpt-tools.js";
import { runStudentCode } from "../../skulpt.index.js";
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

const SKIP_EXAMPLES = [
    "file_upload.py",
    "file_upload_testing.py",
    "handle_image_upload.py",
    "pil_image.py",
];

const examples = getAllFiles().filter(
    ({ fileName }) => !SKIP_EXAMPLES.includes(fileName)
);

describe.each(examples)(
    "Example Test: %s",
    ({ fileName, contents }: { fileName: string; contents: string }) => {
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
    }
);
