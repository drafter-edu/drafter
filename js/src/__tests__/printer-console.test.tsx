/**
 * Jest DOM tests for the printer console (js/src/console/printer.tsx and
 * js/src/console/repl.ts): the panel that captures Python print()/stderr
 * output and offers an interactive REPL.
 *
 * Covers:
 *   - console-mode resolution from the window configuration objects,
 *   - the footer console: buffered replay, reveal-on-first-print, manual
 *     hide/toggle/clear, stderr styling, devtools mirroring,
 *   - the hover and toast modes (including toast expiry and capping),
 *   - the "devtools" mode (no DOM at all, mirror only),
 *   - the REPL flow against a faked Pyodide runtime: echo, results,
 *     multi-line "incomplete" continuation prompts, formatted errors,
 *     command history navigation, and the not-yet-loaded guard,
 *   - integration: DebugPanel's constructor mounts the shared console.
 */
import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	PrinterConsoleManager,
	attachPrinterConsole,
	getConsoleMode,
	getPrinterConsole,
} from "../console/printer";
import { ReplSession } from "../console/repl";
import { DebugPanel } from "../debug/index";
import { setSystemErrorSink } from "../bridge/engine";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";

const consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});
const consoleWarnSpy = jest
	.spyOn(console, "warn")
	.mockImplementation(() => {});

function setConsoleMode(mode: string | undefined): void {
	if (mode === undefined) {
		delete (window as any).DRAFTER_MODIFIED_CONFIGURATION;
	} else {
		(window as any).DRAFTER_MODIFIED_CONFIGURATION = {
			client_server: { console_mode: mode },
		};
	}
}

/** The site frame skeleton pieces the console mounts into. */
function mountSite(): void {
	document.body.innerHTML = [
		'<div class="drafter-site--">',
		'<form class="drafter-form--">',
		'<div class="drafter-footer--"><div class="drafter-footer-bar"></div></div>',
		"</form>",
		"</div>",
	].join("");
}

function footer(): HTMLElement {
	return document.querySelector(".drafter-footer--") as HTMLElement;
}

function consolePanel(): HTMLElement | null {
	return document.querySelector(".drafter-printer-console");
}

function outputText(): string {
	return (
		document.querySelector(".drafter-printer-console-output")
			?.textContent ?? ""
	);
}

interface FakeFutureOptions {
	syntax?: "complete" | "incomplete" | "syntax-error";
	value?: unknown;
	error?: Error;
	formattedError?: string;
}

/** A thenable standing in for Pyodide's ConsoleFuture PyProxy. */
function fakeFuture(options: FakeFutureOptions = {}) {
	return {
		syntax_check: options.syntax ?? "complete",
		formatted_error: options.formattedError,
		then(
			resolve: (value: unknown) => void,
			reject: (error: unknown) => void,
		) {
			if (options.error) {
				reject(options.error);
			} else {
				resolve(options.value);
			}
		},
	};
}

/**
 * Install a fake Pyodide whose REPL bootstrap yields a session with the
 * given push behavior. Returns the recorded pushed lines.
 */
function installFakePyodide(
	push: (line: string) => ReturnType<typeof fakeFuture>,
): string[] {
	const pushedLines: string[] = [];
	const factory = (
		_stdout: (text: string) => void,
		_stderr: (text: string) => void,
	) => ({
		push: (line: string) => {
			pushedLines.push(line);
			return push(line);
		},
		format_result: (value: unknown) => `repr(${String(value)})`,
	});
	(window as any).pyodide = {
		runPythonAsync: jest.fn(async () => factory),
	};
	return pushedLines;
}

afterEach(() => {
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	window.localStorage.clear();
	delete (window as any).DRAFTER_MODIFIED_CONFIGURATION;
	delete (window as any).DRAFTER_CONFIGURATION;
	delete (window as any).pyodide;
	consoleLogSpy.mockClear();
	consoleErrorSpy.mockClear();
	consoleWarnSpy.mockClear();
	jest.useRealTimers();
});

describe("getConsoleMode", () => {
	test("defaults to auto with no configuration", () => {
		expect(getConsoleMode()).toBe("auto");
	});

	test("reads the modified configuration", () => {
		setConsoleMode("hover");
		expect(getConsoleMode()).toBe("hover");
	});

	test("falls back to the embedded full configuration", () => {
		(window as any).DRAFTER_CONFIGURATION = {
			client_server: { console_mode: "toast" },
		};
		expect(getConsoleMode()).toBe("toast");
	});

	test("modified configuration wins over embedded", () => {
		(window as any).DRAFTER_CONFIGURATION = {
			client_server: { console_mode: "toast" },
		};
		setConsoleMode("devtools");
		expect(getConsoleMode()).toBe("devtools");
	});

	test("ignores unknown values", () => {
		setConsoleMode("everywhere");
		expect(getConsoleMode()).toBe("auto");
	});
});

describe("footer console (auto mode)", () => {
	test("attaches hidden into the footer with a footer-bar toggle button", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		const panel = consolePanel();
		expect(panel).not.toBeNull();
		expect(panel!.hidden).toBe(true);
		expect(panel!.classList.contains("drafter-printer-console-footer")).toBe(
			true,
		);
		expect(footer().contains(panel)).toBe(true);
		expect(
			document.querySelector(".drafter-footer-console-button"),
		).not.toBeNull();
	});

	test("first print reveals the console and renders the line", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		manager.recordOutput("stdout", "Hello, world!\n");

		expect(consolePanel()!.hidden).toBe(false);
		expect(outputText()).toContain("Hello, world!");
	});

	test("output recorded before attach is replayed and revealed", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.recordOutput("stdout", "early bird\n");

		manager.attach(document);

		expect(consolePanel()!.hidden).toBe(false);
		expect(outputText()).toContain("early bird");
	});

	test("stderr entries are tagged for styling", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		manager.recordOutput("stderr", "warning: oh no\n");

		expect(
			document.querySelector(
				".drafter-printer-console-entry.drafter-printer-console-stderr",
			)?.textContent,
		).toContain("warning: oh no");
	});

	test("always mirrors stdout/stderr to the devtools console", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		manager.recordOutput("stdout", "mirrored\n");
		manager.recordOutput("stderr", "mirrored error\n");

		expect(consoleLogSpy).toHaveBeenCalledWith("mirrored");
		expect(consoleErrorSpy).toHaveBeenCalledWith("mirrored error");
	});

	test("hide button suppresses re-reveal until toggled back on", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);
		manager.recordOutput("stdout", "one\n");

		(
			document.querySelector(
				".drafter-printer-console-hide",
			) as HTMLButtonElement
		).click();
		expect(consolePanel()!.hidden).toBe(true);

		manager.recordOutput("stdout", "two\n");
		expect(consolePanel()!.hidden).toBe(true);

		(
			document.querySelector(
				".drafter-footer-console-button",
			) as HTMLButtonElement
		).click();
		expect(consolePanel()!.hidden).toBe(false);
		expect(outputText()).toContain("two");
	});

	test("clear button empties the output but keeps the console", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);
		manager.recordOutput("stdout", "to be cleared\n");

		(
			document.querySelector(
				".drafter-printer-console-clear",
			) as HTMLButtonElement
		).click();

		expect(outputText()).toBe("");
		expect(consolePanel()).not.toBeNull();
	});

	test("re-attach after teardown builds a fresh console with the history", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);
		manager.recordOutput("stdout", "survivor\n");

		// Simulate an instance restart tearing down the site frame.
		document.body.innerHTML = "";
		mountSite();
		manager.attach(document);

		expect(consolePanel()).not.toBeNull();
		expect(outputText()).toContain("survivor");
		expect(consolePanel()!.hidden).toBe(false);
	});

	test("attach without a footer does nothing", () => {
		document.body.innerHTML = '<div class="drafter-site--"></div>';
		const manager = new PrinterConsoleManager();
		manager.attach(document);
		expect(consolePanel()).toBeNull();
	});

	test("Enter in the input is consumed, not submitted to the site form", () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		const input = document.querySelector(
			".drafter-printer-console-input",
		) as HTMLInputElement;
		const event = new KeyboardEvent("keydown", {
			key: "Enter",
			cancelable: true,
			bubbles: true,
		});
		input.dispatchEvent(event);
		expect(event.defaultPrevented).toBe(true);
	});
});

describe("hover mode", () => {
	test("mounts a floating console inside the site element", () => {
		mountSite();
		setConsoleMode("hover");
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		const panel = consolePanel();
		expect(panel).not.toBeNull();
		expect(panel!.classList.contains("drafter-printer-console-hover")).toBe(
			true,
		);
		expect(
			(document.querySelector(".drafter-site--") as HTMLElement).contains(
				panel,
			),
		).toBe(true);

		manager.recordOutput("stdout", "floating\n");
		expect(panel!.hidden).toBe(false);
	});
});

describe("toast mode", () => {
	test("printed lines appear as toasts and expire", () => {
		jest.useFakeTimers();
		mountSite();
		setConsoleMode("toast");
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		expect(consolePanel()).toBeNull();
		manager.recordOutput("stdout", "toasty\n");

		const toast = document.querySelector(".drafter-printer-toast");
		expect(toast?.textContent).toBe("toasty");

		jest.advanceTimersByTime(6001);
		expect(document.querySelector(".drafter-printer-toast")).toBeNull();
	});

	test("stderr toasts are tagged and the count is capped", () => {
		jest.useFakeTimers();
		mountSite();
		setConsoleMode("toast");
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		for (let i = 0; i < 7; i++) {
			manager.recordOutput("stdout", `line ${i}\n`);
		}
		manager.recordOutput("stderr", "bad news\n");

		const toasts = Array.from(
			document.querySelectorAll(".drafter-printer-toast"),
		);
		expect(toasts.length).toBeLessThanOrEqual(5);
		expect(
			toasts[toasts.length - 1].classList.contains(
				"drafter-printer-console-stderr",
			),
		).toBe(true);
	});

	test("blank lines do not produce toasts", () => {
		mountSite();
		setConsoleMode("toast");
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		manager.recordOutput("stdout", "\n");
		expect(document.querySelector(".drafter-printer-toast")).toBeNull();
	});
});

describe("devtools mode", () => {
	test("creates no DOM and only mirrors", () => {
		mountSite();
		setConsoleMode("devtools");
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		manager.recordOutput("stdout", "quiet\n");

		expect(consolePanel()).toBeNull();
		expect(document.querySelector(".drafter-printer-toast")).toBeNull();
		expect(consoleLogSpy).toHaveBeenCalledWith("quiet");
	});
});

describe("REPL", () => {
	test("guards when Pyodide is not loaded yet", async () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("1 + 1");

		expect(outputText()).toContain(">>> 1 + 1");
		expect(outputText()).toContain("Python is not running yet");
	});

	test("echoes the command and shows the repr of the result", async () => {
		mountSite();
		installFakePyodide(() => fakeFuture({ value: 4 }));
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("2 + 2");

		expect(outputText()).toContain(">>> 2 + 2");
		expect(outputText()).toContain("repr(4)");
	});

	test("statements with no value produce no result entry", async () => {
		mountSite();
		installFakePyodide(() => fakeFuture({ value: undefined }));
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("x = 1");

		expect(
			document.querySelector(".drafter-printer-console-result"),
		).toBeNull();
	});

	test("incomplete input switches to a continuation prompt", async () => {
		mountSite();
		let calls = 0;
		installFakePyodide(() =>
			calls++ === 0
				? fakeFuture({ syntax: "incomplete" })
				: fakeFuture({ value: undefined }),
		);
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("def f():");
		const prompt = document.querySelector(
			".drafter-printer-console-prompt",
		) as HTMLElement;
		expect(prompt.textContent).toBe("...");

		await manager.submitCommand("    return 1");
		expect(prompt.textContent).toBe(">>>");
		expect(outputText()).toContain("...     return 1");
	});

	test("runtime errors show the formatted traceback", async () => {
		mountSite();
		installFakePyodide(() =>
			fakeFuture({
				error: new Error("PythonError"),
				formattedError:
					'Traceback (most recent call last):\n  File "<console>"\nZeroDivisionError: division by zero\n',
			}),
		);
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("1 / 0");

		expect(outputText()).toContain("ZeroDivisionError: division by zero");
	});

	test("syntax errors are reported without executing", async () => {
		mountSite();
		const pushed = installFakePyodide(() =>
			fakeFuture({
				syntax: "syntax-error",
				formattedError: "SyntaxError: invalid syntax\n",
			}),
		);
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("1 +");

		expect(pushed).toEqual(["1 +"]);
		expect(outputText()).toContain("SyntaxError: invalid syntax");
	});

	test("ArrowUp recalls the previous command", async () => {
		mountSite();
		installFakePyodide(() => fakeFuture({ value: undefined }));
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		await manager.submitCommand("first = 1");
		await manager.submitCommand("second = 2");

		const input = document.querySelector(
			".drafter-printer-console-input",
		) as HTMLInputElement;
		input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
		expect(input.value).toBe("second = 2");
		input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
		expect(input.value).toBe("first = 1");
		input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
		expect(input.value).toBe("second = 2");
	});

	test("REPL output emitted through the session callbacks reaches the console", async () => {
		mountSite();
		const manager = new PrinterConsoleManager();
		manager.attach(document);

		// Drive a ReplSession directly with an emitter into the manager to
		// mimic PyodideConsole's stdout callback during a command.
		(window as any).pyodide = {
			runPythonAsync: jest.fn(
				async () =>
					(
						stdout: (text: string) => void,
						_stderr: (text: string) => void,
					) => ({
						push: (_line: string) => {
							stdout("printed from repl\n");
							return fakeFuture({ value: undefined });
						},
						format_result: (value: unknown) => String(value),
					}),
			),
		};
		const session = new ReplSession((stream, text) =>
			manager.recordOutput(stream, text),
		);
		await session.run("print('printed from repl')");

		expect(outputText()).toContain("printed from repl");
	});
});

describe("DebugPanel integration", () => {
	test("constructing the debug panel mounts the shared printer console", () => {
		document.body.innerHTML = [
			'<div class="drafter-header--"></div>',
			'<div class="drafter-footer--"></div>',
			'<div id="drafter-debug-container"></div>',
		].join("");
		const bridge = {
			goto: jest.fn(),
		} as unknown as ClientBridgeWrapperInterface;

		new DebugPanel("drafter-debug-container", bridge);

		expect(footer().querySelector(".drafter-printer-console")).not.toBeNull();

		getPrinterConsole().recordOutput("stdout", "via singleton\n");
		expect(outputText()).toContain("via singleton");
	});

	test("attachPrinterConsole never throws on a bare document", () => {
		document.body.innerHTML = "";
		expect(() => attachPrinterConsole(document)).not.toThrow();
	});
});
