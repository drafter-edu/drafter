import {
	afterAll,
	afterEach,
	beforeAll,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";
import * as fs from "fs";
import * as path from "path";
import { EditorView } from "@codemirror/view";

import { DRAFTER_PAGE_LOADED_EVENT } from "../components/events";
import { openCodeEditor } from "../debug/editor";
import { DebugPanel } from "../debug/index";
import { DebugFooterBar } from "../debug/footer";
import { applyTheme } from "../debug/theme_switch";
import { setSystemErrorSink } from "../bridge/engine";
import { t } from "../i18n";

import REQUEST_EVENT from "./fixtures/telemetry/request-event.json";

/**
 * Cross-language CustomEvent contract tests.
 *
 * The Python bridge (src/drafter/bridge/) registers window listeners for a
 * fixed set of "drafter-*" CustomEvents that the JS debug UI dispatches, and
 * itself dispatches "drafter-page-loaded" which JS components listen for.
 * These tests pin both sides: the Python source is parsed for the exact
 * registered names, and the JS dispatch sites are exercised in jsdom to
 * assert the names and detail shapes they emit.
 */

// The window events the Python ClientBridge registers in setup_events()
// (src/drafter/bridge/client_bridge.py). "popstate" is a browser event and is
// intentionally excluded here.
const PYTHON_LISTENED_EVENTS = [
	"drafter-toggle-frame",
	"drafter-toggle-debug-mode",
	"drafter-evict-persistent",
	"drafter-navigate",
	"drafter-replay-route",
	"drafter-replay-request",
	"drafter-save-state",
	"drafter-load-state",
	"drafter-set-theme",
];

// Jest's cwd is js/ (tests are always run via `npm test` from js/, matching
// the convention used by the pyodide/skulpt example suites).
const BRIDGE_DIR = path.resolve(
	process.cwd(),
	"..",
	"src",
	"drafter",
	"bridge",
);

// DebugPanel construction logs are routed through the suppressed console.log;
// keep console.error clean too in case a panel reports during teardown.
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});
const consoleWarnSpy = jest
	.spyOn(console, "warn")
	.mockImplementation(() => {});

function flush(): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, 0));
}

function captureWindowEvents(eventName: string): {
	events: CustomEvent[];
	dispose: () => void;
} {
	const events: CustomEvent[] = [];
	const listener = (event: Event) => {
		events.push(event as CustomEvent);
	};
	window.addEventListener(eventName, listener);
	return {
		events,
		dispose: () => window.removeEventListener(eventName, listener),
	};
}

const disposers: Array<() => void> = [];

function capture(eventName: string): CustomEvent[] {
	const { events, dispose } = captureWindowEvents(eventName);
	disposers.push(dispose);
	return events;
}

afterEach(async () => {
	while (disposers.length > 0) {
		disposers.pop()!();
	}
	// Close any dialogs left open (editor dialog etc.) so their document-level
	// keydown listeners and symbolicId registrations do not leak.
	document
		.querySelectorAll<HTMLButtonElement>(".drafter-dialog-close")
		.forEach((button) => button.click());
	await flush();
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	delete (window as { __drafterCurrentCode?: unknown }).__drafterCurrentCode;
	delete (window as { __drafterRestartToken?: unknown })
		.__drafterRestartToken;
	consoleErrorSpy.mockClear();
	consoleWarnSpy.mockClear();
});

afterAll(() => {
	consoleErrorSpy.mockRestore();
	consoleWarnSpy.mockRestore();
});

describe("Python bridge event-name contract", () => {
	test("client_bridge.py registers exactly the expected drafter-* window events", () => {
		const source = fs.readFileSync(
			path.join(BRIDGE_DIR, "client_bridge.py"),
			"utf-8",
		);
		// Matches the keys of the dict passed to events.setup_events(), e.g.
		//     "drafter-toggle-frame": lambda event: ...
		const registered = new Set<string>();
		for (const match of source.matchAll(/"(drafter-[a-z-]+)"\s*:/g)) {
			registered.add(match[1]);
		}
		expect([...registered].sort()).toEqual(
			[...PYTHON_LISTENED_EVENTS].sort(),
		);
	});

	test("JS DRAFTER_PAGE_LOADED_EVENT matches the Python dispatcher's constant", () => {
		const source = fs.readFileSync(
			path.join(BRIDGE_DIR, "events.py"),
			"utf-8",
		);
		const match = source.match(
			/DRAFTER_PAGE_LOADED_EVENT\s*=\s*"([^"]+)"/,
		);
		expect(match).not.toBeNull();
		expect(DRAFTER_PAGE_LOADED_EVENT).toBe(match![1]);
		expect(DRAFTER_PAGE_LOADED_EVENT).toBe("drafter-page-loaded");
	});
});

describe("debug panel dispatch sites", () => {
	function buildSiteScaffold(): void {
		document.body.innerHTML = [
			'<div class="drafter-header--"></div>',
			'<div class="drafter-footer--"></div>',
			'<div class="drafter-persist--" hidden></div>',
			'<div id="drafter-debug-container"></div>',
		].join("");
	}

	function createPanel(): DebugPanel {
		buildSiteScaffold();
		return new DebugPanel(
			"drafter-debug-container",
			// The bridge wrapper is only stored by the constructor; no methods
			// are invoked by the dispatch paths under test.
			{} as never,
			document,
		);
	}

	test("View > Production menu item dispatches drafter-toggle-debug-mode", () => {
		createPanel();
		const events = capture("drafter-toggle-debug-mode");

		(
			document.querySelector(
				".drafter-menu-item-production",
			) as HTMLButtonElement
		).click();

		expect(events).toHaveLength(1);
		expect(events[0].detail).toBeNull();
	});

	test("View > Toggle Frame menu item dispatches drafter-toggle-frame", () => {
		createPanel();
		const events = capture("drafter-toggle-frame");

		(
			document.querySelector(
				".drafter-menu-item-toggle-frame",
			) as HTMLButtonElement
		).click();

		expect(events).toHaveLength(1);
		expect(events[0].detail).toBeNull();
	});

	test("Navigate > Home and Reset menu items dispatch drafter-navigate with route details", () => {
		createPanel();
		const events = capture("drafter-navigate");

		const menubar = document.querySelector(
			".drafter-header-menubar",
		) as HTMLElement;
		(
			menubar.querySelector(
				".drafter-menu-item-home",
			) as HTMLButtonElement
		).click();
		(
			menubar.querySelector(
				".drafter-menu-item-reset",
			) as HTMLButtonElement
		).click();

		expect(events.map((event) => event.detail)).toEqual([
			"index",
			"--reset",
		]);
	});

	test("Navigate > About menu item dispatches drafter-navigate with --about", () => {
		createPanel();
		const events = capture("drafter-navigate");

		(
			document.querySelector(
				".drafter-header-- .drafter-menu-item-about",
			) as HTMLButtonElement
		).click();

		expect(events.map((event) => event.detail)).toEqual(["--about"]);
	});

	test("Navigate > Reload menu item dispatches drafter-navigate with --reload", () => {
		createPanel();
		const events = capture("drafter-navigate");

		(
			document.querySelector(
				".drafter-menu-item-reload",
			) as HTMLButtonElement
		).click();

		expect(events.map((event) => event.detail)).toEqual(["--reload"]);
	});

	test("Navigate > Replay Route menu item dispatches drafter-replay-route", () => {
		createPanel();
		const events = capture("drafter-replay-route");

		(
			document.querySelector(
				".drafter-menu-item-replay",
			) as HTMLButtonElement
		).click();

		expect(events).toHaveLength(1);
	});

	test("applyTheme dispatches drafter-set-theme with the theme name", () => {
		const events = capture("drafter-set-theme");
		try {
			applyTheme("sakura");
		} finally {
			// applyTheme also persists a config override; keep it out of
			// the other tests in this file.
			window.localStorage.clear();
		}

		expect(events).toHaveLength(1);
		expect(events[0].detail).toBe("sakura");
	});

	test("history Revisit button dispatches drafter-replay-request with the request id", () => {
		const panel = createPanel();
		panel.handleEvent({
			...(REQUEST_EVENT as object),
			request_id: 42,
		} as never);
		const events = capture("drafter-replay-request");

		(
			document.querySelector(
				".request-recreate-link",
			) as HTMLButtonElement
		).click();

		expect(events).toHaveLength(1);
		expect(events[0].detail).toEqual({
			request_id: 42,
			url: "index",
			kwargs_json: '{"name": "Ada"}',
		});
	});

	test("footer evict button dispatches drafter-evict-persistent with the persist key", () => {
		document.body.innerHTML = [
			'<div class="drafter-footer--"></div>',
			'<div class="drafter-persist--" hidden>',
			'<audio data-drafter-persist-key="theme-song"></audio>',
			"</div>",
		].join("");

		const footer = new DebugFooterBar(document);
		const events = capture("drafter-evict-persistent");

		// Open the persisted-components panel so the rows (and their evict
		// buttons) are rendered.
		(
			document.querySelector(
				".drafter-footer-persist-button",
			) as HTMLButtonElement
		).click();

		const evictButton = document.querySelector(
			".drafter-footer-persist-evict",
		) as HTMLButtonElement;
		expect(evictButton).not.toBeNull();
		evictButton.click();

		expect(events).toHaveLength(1);
		expect(events[0].detail).toBe("theme-song");
		expect(footer).toBeDefined();
	});
});

describe("editor restart dispatch (drafter-restart-student-code)", () => {
	// CodeMirror 6 measures text geometry through Range client rects, which
	// jsdom's Range does not implement. Stubbing them with zero-size rects is
	// enough for EditorView to mount and edit documents in jsdom; only pixel
	// geometry (coordsAtPos etc.) is meaningless, and nothing here uses it.
	beforeAll(() => {
		const zeroRect = {
			x: 0,
			y: 0,
			width: 0,
			height: 0,
			top: 0,
			left: 0,
			right: 0,
			bottom: 0,
			toJSON: () => ({}),
		} as DOMRect;
		const emptyRectList = {
			length: 0,
			item: () => null,
			[Symbol.iterator]: Array.prototype[
				Symbol.iterator
			] as () => IterableIterator<DOMRect>,
		} as unknown as DOMRectList;

		Range.prototype.getBoundingClientRect = () => zeroRect;
		Range.prototype.getClientRects = () => emptyRectList;
		if (typeof Element.prototype.getClientRects !== "function") {
			Element.prototype.getClientRects = () => emptyRectList;
		}
	});

	function openEditorAndGetView(): EditorView {
		openCodeEditor();
		const container = document.querySelector(
			".drafter-code-editor-container",
		) as HTMLElement;
		expect(container).not.toBeNull();
		const view = EditorView.findFromDOM(container);
		if (!view) {
			throw new Error("CodeMirror view was not mounted");
		}
		return view;
	}

	function clickDialogButton(label: string): void {
		const buttons = Array.from(
			document.querySelectorAll<HTMLButtonElement>(
				".drafter-dialog-button",
			),
		);
		const match = buttons.find(
			(button) => button.textContent?.trim() === label,
		);
		if (!match) {
			throw new Error(`No dialog button labeled '${label}'`);
		}
		match.click();
	}

	test("Run dispatches the edited code with the window restart token", async () => {
		(window as { __drafterCurrentCode?: string }).__drafterCurrentCode =
			"print('original')";
		(window as { __drafterRestartToken?: string }).__drafterRestartToken =
			"token-abc-123";
		const events = capture("drafter-restart-student-code");

		const view = openEditorAndGetView();
		expect(view.state.doc.toString()).toBe("print('original')");

		view.dispatch({
			changes: {
				from: 0,
				to: view.state.doc.length,
				insert: "print('edited')",
			},
		});

		clickDialogButton(t("editor.run"));
		await flush();

		expect(events).toHaveLength(1);
		expect(events[0].detail).toEqual({
			code: "print('edited')",
			_token: "token-abc-123",
		});
		// The global code snapshot is kept in sync for later editor sessions.
		expect(
			(window as { __drafterCurrentCode?: string }).__drafterCurrentCode,
		).toBe("print('edited')");
		// The dialog closed after Run.
		expect(document.querySelector(".drafter-dialog")).toBeNull();
	});

	test("Cancel closes the editor without dispatching a restart", async () => {
		(window as { __drafterCurrentCode?: string }).__drafterCurrentCode =
			"x = 1";
		(window as { __drafterRestartToken?: string }).__drafterRestartToken =
			"token-abc-123";
		const events = capture("drafter-restart-student-code");

		openEditorAndGetView();
		clickDialogButton(t("editor.cancel"));
		await flush();

		expect(events).toHaveLength(0);
		expect(document.querySelector(".drafter-dialog")).toBeNull();
		// Cancel must not clobber the stored code.
		expect(
			(window as { __drafterCurrentCode?: string }).__drafterCurrentCode,
		).toBe("x = 1");
	});

	test("editor falls back to a placeholder when no code is available", () => {
		const events = capture("drafter-restart-student-code");

		const view = openEditorAndGetView();
		expect(view.state.doc.toString()).toBe("# Source code not available");
		expect(events).toHaveLength(0);
	});
});
