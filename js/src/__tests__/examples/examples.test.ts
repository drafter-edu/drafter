/**
 * Basic unit tests for TypeScript client functionality
 */

import "../../../../src/drafter/assets/js/skulpt.js";
import "../../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../../src/drafter/assets/js/drafter.js";
import "./d3.6.3.1.min.js";
import { builtinRead, setupSkulpt } from "../../skulpt_bridge/skulpt-tools.js";
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
const INTENTIONAL_ERROR_EXAMPLES: string[] = [
    "error_non_string_page.py",
    "state_conversion.py",
];

const examples = getAllFiles().filter(
    ({ fileName }) =>
        !SKIP_EXAMPLES.includes(fileName) &&
        !INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
);

const errorExamples = getAllFiles().filter(({ fileName }) =>
    INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
);

describe.each(examples)(
    "Example Test: %s",
    ({ fileName, contents }: { fileName: string; contents: string }) => {
        test(`can run example ${fileName}`, async () => {
            document.body.innerHTML = "<div id='drafter-root--'></div>";
            await runStudentCode({ code: contents, presentErrors: false });
            const drafterBody = await document.querySelector("#drafter-root--");
            expect(drafterBody).toBeInTheDocument();
            // The Debug Panel should load
            const debugPanel = drafterBody?.querySelector(".drafter-debug--");
            expect(debugPanel).toBeInTheDocument();
            // Should not say "Error" in the drafter-form-- body
            const formBody = drafterBody?.querySelector(".drafter-form--");
            expect(formBody?.textContent).not.toMatch(/error/i);
        });
    },
);

describe.each(errorExamples)(
    "Example Test (Expected Errors): %s",
    ({ fileName, contents }: { fileName: string; contents: string }) => {
        test(`can run example with expected errors ${fileName}`, async () => {
            document.body.innerHTML = "<div id='drafter-root--'></div>";
            await runStudentCode({ code: contents, presentErrors: true });
            const drafterBody = await document.querySelector("#drafter-root--");
            expect(drafterBody).toBeInTheDocument();
            // The Debug Panel should not load
            // const debugPanel = drafterBody?.querySelector(".drafter-debug--");
            // expect(debugPanel).not.toBeInTheDocument();
            // Should say "Error" in the drafter-form-- body
            const formBody = drafterBody?.querySelector(".drafter-form--");
            expect(formBody?.textContent).toMatch(/error/i);
        });
    },
);
