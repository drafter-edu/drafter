/**
 * TEMPORARY repro for file upload "borrowed proxy destroyed" bug.
 */

import { describe, test, expect, beforeAll, beforeEach } from "@jest/globals";
import { within, waitFor } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import {
	resetPyodideDrafterRuntime,
	setupPyodideWithLocalDrafter,
} from "./pyodide-test-harness";
import { runStudentCode } from "../../pyodide.index";

const FILE_UPLOAD_CODE = `
from drafter import *

@dataclass
class State:
    current_text: str

@route
def index(state: State):
    return Page(state, [
        "Upload a text file:",
        FileUpload("new_text"),
        Div(f"CONTENT:{state.current_text}:END"),
        Button("Save", save_text),
    ])

@route
def save_text(state: State, new_text: bytes):
    state.current_text = new_text.decode("utf-8")
    return index(state)

start_server(State(""))
`;

describe("Pyodide file upload repro", () => {
	beforeAll(async () => {
		// jsdom's Blob may not implement arrayBuffer(); polyfill for the test.
		if (typeof Blob.prototype.arrayBuffer !== "function") {
			Blob.prototype.arrayBuffer = function () {
				return new Promise<ArrayBuffer>((resolve, reject) => {
					const reader = new FileReader();
					reader.onload = () => {
						const result = reader.result as ArrayBuffer;
						console.log(
							"POLYFILL arrayBuffer bytes:",
							result.byteLength,
						);
						resolve(result);
					};
					reader.onerror = () => reject(reader.error);
					reader.readAsArrayBuffer(this);
				});
			};
		}
		await setupPyodideWithLocalDrafter();
	}, 120000);

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
	});

	test("uploading a file does not destroy proxies", async () => {
		await runStudentCode({ code: FILE_UPLOAD_CODE, presentErrors: false });
		const root = document.getElementById("drafter-root--")!;
		const app = within(root);

		await waitFor(() => {
			expect(root.textContent || "").toMatch(/CONTENT::END/);
		});

		const fileInput = root.querySelector(
			"input[type=file]",
		) as HTMLInputElement;
		expect(fileInput).not.toBeNull();

		const file = new File(["hello upload"], "hello.txt", {
			type: "text/plain",
		});
		await userEvent.upload(fileInput, file);

		// TEMP DEBUG: verify jsdom FormData carries the file
		const form = root.querySelector("form");
		if (form) {
			const fd = new FormData(form);
			for (const [k, v] of fd.entries()) {
				console.log(
					"FORMDATA ENTRY:",
					k,
					typeof v,
					v instanceof File
						? `File(${v.name}, ${v.size}b)`
						: String(v),
				);
			}
		} else {
			console.log("FORMDATA: no form element found");
		}

		const button = await app.findByRole("button", { name: /save/i });
		await userEvent.click(button);

		await waitFor(
			() => {
				const errorPage = root.querySelector(".error-page");
				if (errorPage) {
					throw new Error(
						"Page shows error: " +
							(errorPage.textContent || "").slice(0, 2000),
					);
				}
				expect(root.textContent || "").toMatch(
					/CONTENT:hello upload:END/,
				);
			},
			{ timeout: 15000 },
		);
	}, 60000);
});
