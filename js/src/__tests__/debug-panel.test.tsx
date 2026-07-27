/**
 * Jest DOM tests for the debug panel (js/src/debug/index.tsx and its
 * sub-panels in js/src/debug/panels/, plus the header/footer bars).
 *
 * These complement js/src/__tests__/telemetry-adapters.test.ts, which feeds
 * the same fixtures through DebugPanel.handleEvent and asserts the
 * adapter-level outcomes plus the per-record DOM basics. This file focuses
 * on everything else the panel renders and does:
 *   - construction/mounting: the base structure (five tab areas holding the
 *     sections, header menu bar/footer decoration), root scoping, and the
 *     constructor contract used by the Python bridge
 *     (create_debug_panel(debug_id, client_bridge, scope) in
 *     src/drafter/bridge/runtime.py -> new DebugPanel(id, bridge, scope),
 *     where scope arrives as null for the non-shadow-DOM case),
 *   - interactions feasible in jsdom: tab switching, the header menu
 *     items' CustomEvents, history pagination/clear/expansion,
 *     config override editing, files-panel refresh/preview, footer
 *     persisted-components popup,
 *   - the full matrix of state representation renderers,
 *   - i18n (i18next initializes at module import in js/src/i18n.ts, so no
 *     test-side setup is required; language switching is exercised here),
 *   - the event-log DOM for handled and unhandled records, including
 *     TS-side system errors delivered through the engine sink.
 *
 * TabBar and HeaderMenuBar internals (keyboard navigation, badges,
 * outside-click dismissal, localStorage persistence) have their own suites
 * in debug-tabs.test.tsx and debug-menubar.test.tsx.
 *
 * Notes on current production behavior discovered while writing these
 * tests (documented, not fixed, per task rules):
 *   - renderRepresentation has no case for the declared "class" and "union"
 *     representation kinds; both fall through to the default renderer, which
 *     shows only kind/type (fields/options are silently dropped).
 *   - createPanelStructure produces a nested duplicate: the outer
 *     document.createElement div and the inner JSX div both carry the
 *     drafter-debug-panel class.
 */
import {
	afterAll,
	afterEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import { DebugPanel } from "../debug/index";
import { reportSystemError, setSystemErrorSink } from "../bridge/engine";
import { i18n } from "../i18n";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { RouteAddedEvent } from "../debug/telemetry/routes";
import type { RequestEvent, ResponseEvent } from "../debug/telemetry/requests";
import type {
	InitialConfigurationEvent,
	UpdatedConfigurationEvent,
} from "../debug/telemetry/config";
import type {
	Primitive,
	SpecificRepresentation,
	UpdatedStateEvent,
} from "../debug/telemetry/state";
import type { TelemetryRecord } from "../debug/telemetry";

import ROUTE_ADDED from "./fixtures/telemetry/route-added.json";
import REQUEST_EVENT from "./fixtures/telemetry/request-event.json";
import RESPONSE_EVENT from "./fixtures/telemetry/response-event.json";
import INITIAL_CONFIGURATION from "./fixtures/telemetry/initial-configuration.json";
import UPDATED_CONFIGURATION from "./fixtures/telemetry/updated-configuration.json";
import UPDATED_STATE from "./fixtures/telemetry/updated-state.json";

const CONTAINER_ID = "drafter-debug-container";
const OVERRIDES_STORAGE_KEY = "drafter.debug.configuration-overrides.v1";

// Section DOM-id prefixes and their titles, in DOM order: tabpanels appear
// in tab order (current, history, overview, tests, environment) and each
// tab's sections in composition order.
const PANEL_SECTIONS: Array<[string, string]> = [
	["drafter-debug-current", "Current Page"],
	["drafter-debug-current-state", "Current State"],
	["drafter-debug-history", "Page History"],
	["drafter-debug-routes", "Registered Routes"],
	["drafter-debug-route-graph", "Route Graph"],
	["drafter-debug-tests", "Your Tests"],
	// ["drafter-debug-coverage", "Coverage"],
	// ["drafter-debug-test-wizard", "Create a Test"],
	["drafter-debug-files", "File Systems"],
	["drafter-debug-packages", "Installed Packages"],
	["drafter-debug-config", "Configuration"],
	["drafter-debug-runtime", "Runtime Info"],
	["drafter-debug-log", "Event Log"],
	["drafter-debug-storage", "Browser Storage"],
	["drafter-debug-internals", "Advanced"],
];

// The five tab areas: [tab id, English label, section id prefixes it holds].
const TABS: Array<[string, string, string[]]> = [
	[
		"current",
		"Current",
		["drafter-debug-current", "drafter-debug-current-state"],
	],
	["history", "History", ["drafter-debug-history"]],
	[
		"overview",
		"Overview",
		["drafter-debug-routes", "drafter-debug-route-graph"],
	],
	[
		"tests",
		"Tests",
		[
			"drafter-debug-tests",
			// "drafter-debug-coverage",
			// "drafter-debug-test-wizard",
		],
	],
	[
		"environment",
		"Environment",
		[
			"drafter-debug-files",
			"drafter-debug-packages",
			"drafter-debug-config",
			"drafter-debug-runtime",
			"drafter-debug-log",
			"drafter-debug-storage",
			"drafter-debug-internals",
		],
	],
];

// The constructor logs setup problems via console.error and
// reportSystemError always mirrors to console.error; keep test output clean.
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});
const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});

afterEach(() => {
	// The DebugPanel constructor registers itself as the system error sink.
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	window.localStorage.clear();
	delete (window as any).DRAFTER_ENGINE;
	delete (globalThis as any).Sk;
	delete (window as any).DRAFTER_MODIFIED_CONFIGURATION;
	delete (window as any).DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION;
	delete (window as any).DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES;
	consoleErrorSpy.mockClear();
	consoleWarnSpy.mockClear();
});

afterAll(() => {
	consoleErrorSpy.mockRestore();
	consoleWarnSpy.mockRestore();
});

function mountHost(
	options: { containers?: string[]; extraHtml?: string } = {},
): void {
	const containers = options.containers ?? [CONTAINER_ID];
	document.body.innerHTML = [
		'<div class="drafter-header--"></div>',
		'<div class="drafter-footer--"></div>',
		options.extraHtml ?? "",
		...containers.map((id) => `<div id="${id}"></div>`),
	].join("");
}

function makeBridge(): ClientBridgeWrapperInterface {
	return { goto: jest.fn() } as unknown as ClientBridgeWrapperInterface;
}

/** Mount the minimal host DOM and construct a panel, as the bridge does. */
function createPanel(containerId: string = CONTAINER_ID): DebugPanel {
	mountHost({ containers: [containerId] });
	return new DebugPanel(containerId, makeBridge());
}

function container(id: string = CONTAINER_ID): HTMLElement {
	return document.getElementById(id) as HTMLElement;
}

/** The instance id suffix DebugPanel minted for the panel in `containerEl`. */
function instanceIdOf(containerEl: HTMLElement): string {
	const panelEl = containerEl.querySelector(
		"[id^='drafter-debug-panel-']",
	) as HTMLElement;
	return panelEl.id.replace("drafter-debug-panel-", "");
}

let repIdCounter = 1000;

function prim(value: string, type: Primitive["type"] = "int"): Primitive {
	return {
		kind: "primitive",
		value,
		type,
		id: repIdCounter++,
		complexity: 1,
	};
}

function stateEvent(representation: unknown): UpdatedStateEvent {
	return {
		...(UPDATED_STATE as unknown as UpdatedStateEvent),
		representation: representation as SpecificRepresentation,
	};
}

function requestEvent(overrides: Partial<RequestEvent> = {}): RequestEvent {
	return { ...(REQUEST_EVENT as RequestEvent), ...overrides };
}

describe("construction and mounting", () => {
	test("base structure: title, subtitle, tab bar, content, all sections", () => {
		createPanel();
		const root = container();

		expect(
			root.querySelector(".drafter-debug-header-title")?.textContent,
		).toBe("Debug Panel");
		expect(
			root.querySelector(".drafter-debug-header-subtitle"),
		).not.toBeNull();
		expect(root.querySelector(".drafter-debug-tabbar")).not.toBeNull();
		expect(root.querySelector(".drafter-debug-content")).not.toBeNull();

		const sections = Array.from(
			root.querySelectorAll(".drafter-debug-section"),
		) as HTMLElement[];
		expect(sections).toHaveLength(PANEL_SECTIONS.length);
		sections.forEach((section, index) => {
			const [domPrefix, title] = PANEL_SECTIONS[index];
			expect(section.id).toMatch(new RegExp(`^${domPrefix}-\\d+$`));
			expect(section.classList.contains(domPrefix)).toBe(true);
			expect(
				section.querySelector(".drafter-debug-section-header h4")
					?.textContent,
			).toBe(title);
			// Each section owns a content region with an instance-scoped id.
			expect(
				section.querySelector(
					`#${domPrefix}-content-${instanceIdOf(container())}`,
				),
			).not.toBeNull();
		});
	});

	test("tab bar renders the five tab areas holding their sections", () => {
		createPanel();
		const root = container();
		const instanceId = instanceIdOf(root);
		const tabbar = root.querySelector(
			".drafter-debug-tabbar",
		) as HTMLElement;

		const buttons = Array.from(
			tabbar.querySelectorAll("[role='tab']"),
		) as HTMLButtonElement[];
		expect(buttons).toHaveLength(TABS.length);
		buttons.forEach((button, index) => {
			const [tabId, label, sectionPrefixes] = TABS[index];
			expect(
				button.querySelector(".drafter-debug-tab-label")?.textContent,
			).toBe(label);
			// aria-controls resolves to the tab's tabpanel, which holds the
			// tab's sections in order.
			const tabpanel = root.querySelector(
				`#${button.getAttribute("aria-controls")}`,
			) as HTMLElement;
			expect(tabpanel).not.toBeNull();
			expect(tabpanel.id).toBe(
				`drafter-debug-tab-${tabId}-${instanceId}`,
			);
			const sectionIds = Array.from(
				tabpanel.querySelectorAll(".drafter-debug-section"),
			).map((section) => (section as HTMLElement).id);
			expect(sectionIds).toEqual(
				sectionPrefixes.map((prefix) => `${prefix}-${instanceId}`),
			);
		});
	});

	test("tab switching shows one tabpanel at a time and persists the choice", () => {
		createPanel();
		const root = container();
		const tabButton = (id: string) =>
			root.querySelector(
				`[id^='drafter-debug-tab-btn-${id}-']`,
			) as HTMLButtonElement;
		const tabPanel = (id: string) =>
			root.querySelector(
				`[id^='drafter-debug-tab-${id}-']:not([id*='btn'])`,
			) as HTMLElement;

		// "current" is the default active tab.
		expect(tabButton("current").getAttribute("aria-selected")).toBe("true");
		expect(tabPanel("current").hidden).toBe(false);
		expect(tabPanel("history").hidden).toBe(true);

		tabButton("history").click();

		expect(tabButton("current").getAttribute("aria-selected")).toBe(
			"false",
		);
		expect(tabButton("history").getAttribute("aria-selected")).toBe("true");
		expect(tabPanel("current").hidden).toBe(true);
		expect(tabPanel("history").hidden).toBe(false);
		// The choice persists for the next construction (page reload).
		expect(window.localStorage.getItem("drafter.debug.active-tab.v1")).toBe(
			"history",
		);
	});

	test("menu items render with i18n labels and tooltips", () => {
		createPanel();
		const menubar = document.querySelector(
			".drafter-header-menubar",
		) as HTMLElement;

		const home = menubar.querySelector(
			".drafter-menu-item-home",
		) as HTMLButtonElement;
		expect(home.textContent).toBe("🏠 Home");
		expect(home.title).toBe("Go to Home");

		const reset = menubar.querySelector(
			".drafter-menu-item-reset",
		) as HTMLButtonElement;
		expect(reset.textContent).toBe("🔄 Reset");
		expect(reset.title).toBe("Clear state, history, and return to home");

		const production = menubar.querySelector(
			".drafter-menu-item-production",
		) as HTMLButtonElement;
		expect(production.textContent).toBe("🚪 Production");
		expect(production.title).toBe(
			"Exit debug mode and switch to production view",
		);

		expect(
			menubar.querySelector(".drafter-menu-item-toggle-frame")
				?.textContent,
		).toContain("Toggle Frame");
	});

	test("header bar is decorated with the identity area and menu bar", () => {
		createPanel();
		const headerBar = document.querySelector(
			".drafter-header-- .drafter-header-bar",
		) as HTMLElement;

		expect(headerBar).not.toBeNull();
		expect(
			headerBar.querySelector(
				".drafter-header-identity .drafter-header-title",
			)?.textContent,
		).toBe("Drafter Application");
		// No favicon <link> exists in the jsdom host page, so the mirror
		// image stays hidden.
		expect(
			(
				headerBar.querySelector(
					".drafter-header-favicon",
				) as HTMLImageElement
			).hidden,
		).toBe(true);

		// The five dropdown menus replace the old hot-button row entirely.
		const menuButtons = Array.from(
			headerBar.querySelectorAll(
				".drafter-menu-button .drafter-menu-button-label",
			),
		).map((label) => label.textContent);
		expect(menuButtons).toEqual([
			"Navigate",
			"View",
			"Edit",
			"Save/Load",
			"Help",
		]);
		// Each top-level button advertises its dropdown with a caret.
		expect(
			headerBar.querySelectorAll(
				".drafter-menu-button .drafter-menu-caret",
			),
		).toHaveLength(5);
		expect(
			headerBar.querySelector(".drafter-header-hot-buttons"),
		).toBeNull();

		// Every menu item is rendered and enabled ("Load Most Recent" is the
		// exception: it stays greyed out until something has been saved,
		// covered in the header menu item events suite).
		for (const cls of [
			"drafter-menu-item-quick-save",
			"drafter-menu-item-save-slot",
			"drafter-menu-item-load-slot",
			"drafter-menu-item-download",
			"drafter-menu-item-upload",
			"drafter-menu-item-replay",
			"drafter-menu-item-bug-report",
			"drafter-menu-item-view-source",
			"drafter-menu-item-switch-theme",
			"drafter-menu-item-edit-state",
			"drafter-menu-item-edit-source",
		]) {
			const item = headerBar.querySelector(
				`.${cls}`,
			) as HTMLButtonElement;
			expect(item).not.toBeNull();
			expect(item.disabled).toBe(false);
		}
	});

	test("footer bar is decorated with the route label and persisted count", () => {
		createPanel();
		const footerBar = document.querySelector(
			".drafter-footer-- .drafter-footer-bar",
		) as HTMLElement;

		expect(footerBar).not.toBeNull();
		expect(
			footerBar.querySelector(".drafter-footer-label")?.textContent,
		).toBe("Route: ");
		expect(
			footerBar.querySelector(".drafter-footer-route")?.textContent,
		).toBe("");
		expect(
			footerBar.querySelector(".drafter-footer-persist-button")
				?.textContent,
		).toBe("📌 Persisted (0)");
		// The popup starts hidden.
		const persistPanel = document.querySelector(
			".drafter-footer-persist-panel",
		) as HTMLElement;
		expect(persistPanel.hidden).toBe(true);
	});

	test("a null scope (Python None marshalled by the bridge) falls back to document", () => {
		// Mirrors PyodideRuntimeOperations.create_debug_panel:
		// DebugPanel.new(debug_id, client_bridge, scope) with scope=None.
		mountHost();
		const panel = new DebugPanel(
			CONTAINER_ID,
			makeBridge(),
			null as unknown as ParentNode,
		);

		expect(
			container().querySelector(".drafter-debug-header-title")
				?.textContent,
		).toBe("Debug Panel");
		expect(panel.handleEvent(ROUTE_ADDED as RouteAddedEvent)).toBe(true);
	});

	test("an explicit root scopes all lookups (decoy container untouched)", () => {
		// Simulates the shadow-DOM case: the bridge passes the instance's
		// scope, and lookups must not leak to identically-id'd elements
		// elsewhere in the document.
		document.body.innerHTML = [
			`<div id="${CONTAINER_ID}"></div>`, // decoy outside the scope
			'<div id="scope-wrapper">',
			'<div class="drafter-header--"></div>',
			'<div class="drafter-footer--"></div>',
			`<div id="${CONTAINER_ID}"></div>`,
			"</div>",
		].join("");
		const scope = document.getElementById("scope-wrapper") as HTMLElement;

		const panel = new DebugPanel(CONTAINER_ID, makeBridge(), scope);
		panel.handleEvent(ROUTE_ADDED as RouteAddedEvent);

		const decoy = document.body.querySelector(
			`body > #${CONTAINER_ID}`,
		) as HTMLElement;
		expect(decoy.children).toHaveLength(0);
		expect(
			scope.querySelector(".drafter-debug-route-signature strong")
				?.textContent,
		).toBe("index");
	});

	test("missing container throws with the not-found message", () => {
		mountHost({ containers: ["some-other-container"] });

		// Note: the throw comes from the FIRST sub-panel's constructor
		// (Panel.requireElementById via new TestPanel(...)), which runs
		// before DebugPanel.getContainerElement ever does -- so it is a
		// plain Error, not the DebugPanelError that reportError would build,
		// and nothing is logged via console.error. Same message either way.
		expect(() => new DebugPanel("nonexistent", makeBridge())).toThrow(
			"DebugPanel: Container with id 'nonexistent' not found.",
		);
		expect(consoleErrorSpy).not.toHaveBeenCalled();
	});

	test("missing header decoration target throws", () => {
		document.body.innerHTML = [
			'<div class="drafter-footer--"></div>',
			`<div id="${CONTAINER_ID}"></div>`,
		].join("");

		expect(() => new DebugPanel(CONTAINER_ID, makeBridge())).toThrow(
			"Header element not found",
		);
	});
});

describe("i18n", () => {
	test("i18next is initialized at module import; language switch re-renders new panels", async () => {
		// js/src/i18n.ts calls i18next.init() at import time, so nothing had
		// to be done in test setup for translations to resolve (asserted
		// implicitly by every English-label test above). Keys missing from
		// the "es" bundle fall back to English via fallbackLng.
		await i18n.changeLanguage("es");
		try {
			createPanel();
			expect(
				document.querySelector(".drafter-header-title")?.textContent,
			).toBe("Aplicación Drafter");
			expect(
				document.querySelector(".drafter-menu-item-production")
					?.textContent,
			).toBe("🚪 Producción");
			expect(
				document.querySelector(
					".drafter-menu-button-navigate .drafter-menu-button-label",
				)?.textContent,
			).toBe("Navegar");
			// Tab labels are localized too.
			expect(
				container().querySelector(
					".drafter-debug-tab-button .drafter-debug-tab-label",
				)?.textContent,
			).toBe("Actual");
			// "button.home.tooltip" has no Spanish entry: falls back to English.
			expect(
				(
					document.querySelector(
						".drafter-menu-item-home",
					) as HTMLButtonElement
				).title,
			).toBe("Go to Home");
		} finally {
			await i18n.changeLanguage("en");
		}
	});
});

describe("header menu item events", () => {
	function captureWindowEvent(name: string): Array<CustomEvent> {
		const seen: Array<CustomEvent> = [];
		window.addEventListener(name, ((event: Event) => {
			seen.push(event as CustomEvent);
		}) as EventListener);
		return seen;
	}

	function menuItem(className: string): HTMLButtonElement {
		return document.querySelector(
			`.drafter-header-menubar .${className}`,
		) as HTMLButtonElement;
	}

	test("Navigate > Home dispatches drafter-navigate with 'index'", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-navigate");

		menuItem("drafter-menu-item-home").click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toBe("index");
	});

	test("Navigate > Reset dispatches drafter-navigate with '--reset'", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-navigate");

		menuItem("drafter-menu-item-reset").click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toBe("--reset");
	});

	test("Navigate > About dispatches drafter-navigate with '--about'", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-navigate");

		menuItem("drafter-menu-item-about").click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toBe("--about");
	});

	test("Navigate > Reload Site dispatches drafter-navigate with '--reload'", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-navigate");

		menuItem("drafter-menu-item-reload").click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toBe("--reload");
	});

	test("View > Production dispatches drafter-toggle-debug-mode", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-toggle-debug-mode");

		menuItem("drafter-menu-item-production").click();

		expect(seen).toHaveLength(1);
	});

	test("View > Toggle Frame dispatches drafter-toggle-frame", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-toggle-frame");

		menuItem("drafter-menu-item-toggle-frame").click();

		expect(seen).toHaveLength(1);
	});

	test("Navigate > Replay Route dispatches drafter-replay-route", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-replay-route");

		menuItem("drafter-menu-item-replay").click();

		expect(seen).toHaveLength(1);
	});

	test("Save/Load > Quick Save dispatches drafter-save-state", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-save-state");

		menuItem("drafter-menu-item-quick-save").click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toEqual({ reason: "save", slot: "quick" });
	});

	test("Save/Load > Download dispatches drafter-save-state with reason download", () => {
		createPanel();
		const seen = captureWindowEvent("drafter-save-state");

		menuItem("drafter-menu-item-download").click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toEqual({ reason: "download", slot: "quick" });
	});

	test("Load Most Recent is greyed out until a save exists, then shows its age", () => {
		const panel = createPanel();
		const item = menuItem("drafter-menu-item-load-recent");
		expect(item.disabled).toBe(true);

		// A completed save round-trip fills the quick slot...
		panel.handleEvent({
			kind: "StateSnapshot",
			route: "guess",
			kwargs_json: "{}",
			state_json: '{"score": 1}',
			state_type: "GameState",
			representation: null,
			reason: "save",
			slot: "quick",
			app_title: "",
			version: 1,
		} as never);
		// ...and opening the menu refreshes the dynamic item.
		(
			document.querySelector(
				".drafter-header-- .drafter-menu-button-saveload",
			) as HTMLButtonElement
		).click();

		expect(item.disabled).toBe(false);
		expect(
			item.querySelector(".drafter-menu-item-suffix")?.textContent,
		).toBe(" (just now)");
	});

	test("the debug panel has its own View menu for when the frame is hidden", () => {
		createPanel();
		// It lives in the debug container (which survives frame toggling),
		// not in the frame header.
		const panelMenu = container().querySelector(
			".drafter-menu-button-panel-view",
		) as HTMLButtonElement;
		expect(panelMenu).not.toBeNull();

		const seen = captureWindowEvent("drafter-toggle-frame");
		(
			container().querySelector(
				".drafter-menu-popup-panel-view .drafter-menu-item-toggle-frame",
			) as HTMLButtonElement
		).click();
		expect(seen).toHaveLength(1);

		// The view-settings trio is all present, including Switch Theme.
		for (const cls of [
			"drafter-menu-item-toggle-frame",
			"drafter-menu-item-production",
			"drafter-menu-item-switch-theme",
		]) {
			expect(
				container().querySelector(
					`.drafter-menu-popup-panel-view .${cls}`,
				),
			).not.toBeNull();
		}
	});

	test("Help > Documentation opens the official docs in a new tab", () => {
		createPanel();
		const openSpy = jest
			.spyOn(window, "open")
			.mockImplementation(() => null);
		try {
			menuItem("drafter-menu-item-documentation").click();
			expect(openSpy).toHaveBeenCalledWith(
				"https://drafter-edu.github.io/drafter/",
				"_blank",
			);
		} finally {
			openSpy.mockRestore();
		}
	});
});

describe("setHeaderTitle / setRoute", () => {
	test("setHeaderTitle updates the title and keeps the menu bar", () => {
		const panel = createPanel();
		const header = document.querySelector(
			".drafter-header--",
		) as HTMLElement;
		expect(header.querySelector(".drafter-header-menubar")).not.toBeNull();

		panel.setHeaderTitle("My Cool Site");

		expect(header.querySelector(".drafter-header-title")?.textContent).toBe(
			"My Cool Site",
		);
		// The menu bar rendered by the constructor survives, menus intact.
		expect(
			header.querySelectorAll(
				".drafter-header-menubar .drafter-menu-button",
			),
		).toHaveLength(5);
		expect(header.querySelector(".drafter-menu-item-home")).not.toBeNull();
	});

	test("setHeaderTitle mirrors the page favicon into the header", () => {
		// The favicon <link> lives in the document head (rendered by the
		// page template with id drafter-favicon--); the header mirrors it.
		const link = document.createElement("link");
		link.id = "drafter-favicon--";
		link.setAttribute("rel", "icon");
		link.setAttribute("href", "data:image/svg+xml;base64,abc123");
		document.head.appendChild(link);
		try {
			const panel = createPanel();
			const favicon = document.querySelector(
				".drafter-header-favicon",
			) as HTMLImageElement;
			expect(favicon.hidden).toBe(false);
			expect(favicon.src).toContain("data:image/svg+xml;base64,abc123");

			// A favicon change is picked up on the next title update.
			link.setAttribute("href", "data:image/svg+xml;base64,def456");
			panel.setHeaderTitle("Retitled");
			expect(favicon.src).toContain("data:image/svg+xml;base64,def456");
		} finally {
			link.remove();
		}
	});

	test("setRoute updates the footer route display", () => {
		const panel = createPanel();

		panel.setRoute("guessing_game");

		expect(
			document.querySelector(".drafter-footer-route")?.textContent,
		).toBe("guessing_game");
	});
});

describe("footer persisted components", () => {
	test("persist button toggles the popup and lists parked elements", () => {
		mountHost({
			extraHtml:
				'<div class="drafter-persist--" hidden>' +
				'<span data-drafter-persist-key="timer|3">03:00</span>' +
				"</div>",
		});
		new DebugPanel(CONTAINER_ID, makeBridge());

		const persistButton = document.querySelector(
			".drafter-footer-persist-button",
		) as HTMLButtonElement;
		expect(persistButton.textContent).toBe("📌 Persisted (1)");

		const persistPanel = document.querySelector(
			".drafter-footer-persist-panel",
		) as HTMLElement;
		expect(persistPanel.hidden).toBe(true);

		persistButton.click();
		expect(persistPanel.hidden).toBe(false);

		const row = persistPanel.querySelector(
			".drafter-footer-persist-item",
		) as HTMLElement;
		expect(row.querySelector("code")?.textContent).toBe("span");
		expect(
			row.querySelector(".drafter-footer-persist-key")?.textContent,
		).toBe("timer|3");
		expect(
			row.querySelector(".drafter-footer-persist-state")?.textContent,
		).toBe("03:00");

		persistButton.click();
		expect(persistPanel.hidden).toBe(true);
	});

	test("evict dispatches drafter-evict-persistent with the element's key", () => {
		mountHost({
			extraHtml:
				'<div class="drafter-persist--" hidden>' +
				'<span data-drafter-persist-key="music-player">song</span>' +
				"</div>",
		});
		new DebugPanel(CONTAINER_ID, makeBridge());
		const seen: Array<CustomEvent> = [];
		window.addEventListener("drafter-evict-persistent", ((event: Event) => {
			seen.push(event as CustomEvent);
		}) as EventListener);

		(
			document.querySelector(
				".drafter-footer-persist-button",
			) as HTMLButtonElement
		).click();
		(
			document.querySelector(
				".drafter-footer-persist-evict",
			) as HTMLButtonElement
		).click();

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toBe("music-player");
	});

	test("reveal button toggles the persist area's hidden flag", () => {
		mountHost({
			extraHtml:
				'<div class="drafter-persist--" hidden>' +
				'<span data-drafter-persist-key="k">v</span>' +
				"</div>",
		});
		new DebugPanel(CONTAINER_ID, makeBridge());
		const area = document.querySelector(
			".drafter-persist--",
		) as HTMLElement;

		(
			document.querySelector(
				".drafter-footer-persist-button",
			) as HTMLButtonElement
		).click();
		(
			document.querySelector(
				".drafter-footer-persist-reveal",
			) as HTMLButtonElement
		).click();
		expect(area.hidden).toBe(false);

		(
			document.querySelector(
				".drafter-footer-persist-reveal",
			) as HTMLButtonElement
		).click();
		expect(area.hidden).toBe(true);
	});
});

describe("history panel interactions", () => {
	function historyList(): HTMLElement {
		return container().querySelector(
			"[class*='drafter-debug-page-history-list']",
		) as HTMLElement;
	}

	test("starts empty (the empty message only appears after a re-render)", () => {
		createPanel();
		expect(historyList().children).toHaveLength(0);
	});

	test("pagination: six requests split into pages of five, newest first", () => {
		const panel = createPanel();
		for (let id = 1; id <= 6; id++) {
			panel.handleEvent(
				requestEvent({ request_id: id, url: `page${id}` }),
			);
		}

		let items = Array.from(
			historyList().querySelectorAll(".history-event"),
		) as HTMLElement[];
		expect(items).toHaveLength(5);
		expect(items.map((item) => item.dataset.requestId)).toEqual([
			"6",
			"5",
			"4",
			"3",
			"2",
		]);

		const pagination = container().querySelector(
			"[class*='drafter-debug-page-history-pagination']",
		) as HTMLElement;
		expect(
			pagination.querySelector(".drafter-debug-page-history-page-label")
				?.textContent,
		).toContain("Page 1 of 2");
		const [previous, next] = Array.from(
			pagination.querySelectorAll(".drafter-debug-pagination-btn"),
		) as HTMLButtonElement[];
		expect(previous.disabled).toBe(true);
		expect(next.disabled).toBe(false);

		next.click();

		items = Array.from(
			historyList().querySelectorAll(".history-event"),
		) as HTMLElement[];
		expect(items).toHaveLength(1);
		expect(items[0].dataset.requestId).toBe("1");
		const [previous2, next2] = Array.from(
			(
				container().querySelector(
					"[class*='drafter-debug-page-history-pagination']",
				) as HTMLElement
			).querySelectorAll(".drafter-debug-pagination-btn"),
		) as HTMLButtonElement[];
		expect(previous2.disabled).toBe(false);
		expect(next2.disabled).toBe(true);

		previous2.click();
		expect(historyList().querySelectorAll(".history-event")).toHaveLength(
			5,
		);
	});

	test("pagination is replicated below the list and both bars work", () => {
		const panel = createPanel();
		for (let id = 1; id <= 6; id++) {
			panel.handleEvent(requestEvent({ request_id: id }));
		}

		const bars = Array.from(
			container().querySelectorAll(".drafter-debug-pagination-bar"),
		) as HTMLElement[];
		expect(bars).toHaveLength(2);
		// One bar above the list, one below it.
		const list = historyList();
		expect(
			bars[0].compareDocumentPosition(list) &
				Node.DOCUMENT_POSITION_FOLLOWING,
		).toBeTruthy();
		expect(
			list.compareDocumentPosition(bars[1]) &
				Node.DOCUMENT_POSITION_FOLLOWING,
		).toBeTruthy();
		// Both bars carry the same label and their own working buttons.
		bars.forEach((bar) => {
			expect(
				bar.querySelector(".drafter-debug-page-history-page-label")
					?.textContent,
			).toContain("Page 1 of 2");
		});

		// The bottom bar's Next button paginates too.
		const bottomNext = bars[1].querySelectorAll(
			".drafter-debug-pagination-btn",
		)[1] as HTMLButtonElement;
		bottomNext.click();
		expect(
			container().querySelector(".drafter-debug-page-history-page-label")
				?.textContent,
		).toContain("Page 2 of 2");
	});

	test("a progress track shows how far through the results the page is", () => {
		const panel = createPanel();
		for (let id = 1; id <= 8; id++) {
			panel.handleEvent(requestEvent({ request_id: id }));
		}

		// Page 1 of 2 shows visits 1-5 of 8: 63% of the way through.
		let progress = container().querySelector(
			".drafter-debug-pagination-progress",
		) as HTMLElement;
		expect(progress.getAttribute("aria-valuenow")).toBe("63");
		let fill = progress.querySelector(
			".drafter-debug-pagination-progress-fill",
		) as HTMLElement;
		expect(fill.style.width).toBe("63%");

		const next = container().querySelectorAll(
			".drafter-debug-pagination-btn",
		)[1] as HTMLButtonElement;
		next.click();

		// Page 2 reaches the end of the results.
		progress = container().querySelector(
			".drafter-debug-pagination-progress",
		) as HTMLElement;
		expect(progress.getAttribute("aria-valuenow")).toBe("100");
		fill = progress.querySelector(
			".drafter-debug-pagination-progress-fill",
		) as HTMLElement;
		expect(fill.style.width).toBe("100%");
	});

	test("a new request resets pagination to page 1", () => {
		const panel = createPanel();
		for (let id = 1; id <= 6; id++) {
			panel.handleEvent(requestEvent({ request_id: id }));
		}
		const next = Array.from(
			container().querySelectorAll(".drafter-debug-pagination-btn"),
		)[1] as HTMLButtonElement;
		next.click();

		panel.handleEvent(requestEvent({ request_id: 7 }));

		expect(
			container().querySelector(".drafter-debug-page-history-page-label")
				?.textContent,
		).toContain("Page 1 of 2");
		expect(
			(historyList().querySelector(".history-event") as HTMLElement)
				.dataset.requestId,
		).toBe("7");
	});

	test("clear history asks for confirmation and clears when accepted", () => {
		const panel = createPanel();
		panel.handleEvent(requestEvent());
		const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);
		try {
			(
				container().querySelector(
					".drafter-debug-clear-history-btn",
				) as HTMLButtonElement
			).click();

			expect(confirmSpy).toHaveBeenCalledWith(
				"Are you sure you want to clear the history?",
			);
			expect(historyList().querySelector(".history-event")).toBeNull();
			expect(
				historyList().querySelector(".drafter-debug-history-empty")
					?.textContent,
			).toBe("No history available.");
		} finally {
			confirmSpy.mockRestore();
		}
	});

	test("clear history keeps entries when the confirm is declined", () => {
		const panel = createPanel();
		panel.handleEvent(requestEvent());
		const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(false);
		try {
			(
				container().querySelector(
					".drafter-debug-clear-history-btn",
				) as HTMLButtonElement
			).click();

			expect(
				historyList().querySelectorAll(".history-event"),
			).toHaveLength(1);
		} finally {
			confirmSpy.mockRestore();
		}
	});

	test("long request urls render truncated and expand/collapse on click", () => {
		const panel = createPanel();
		const longUrl =
			"index?first_name=Ada&last_name=Lovelace&role=mathematician";
		panel.handleEvent(requestEvent({ url: longUrl }));

		const urlElement = historyList().querySelector(
			".drafter-history-request-url.truncatable-url",
		) as HTMLElement;
		expect(urlElement.classList.contains("truncated")).toBe(true);
		expect(urlElement.dataset.fullValue).toBe(longUrl);
		const truncated = urlElement.textContent ?? "";
		expect(truncated).toContain("...");
		expect(truncated.length).toBeLessThan(longUrl.length);

		urlElement.click();
		expect(urlElement.textContent).toBe(longUrl);
		expect(urlElement.classList.contains("truncated")).toBe(false);

		urlElement.click();
		expect(urlElement.textContent).toBe(truncated);
		expect(urlElement.classList.contains("truncated")).toBe(true);
	});

	test("request and response details are collapsible <details> blocks", () => {
		const panel = createPanel();
		panel.handleEvent(REQUEST_EVENT as RequestEvent);
		panel.handleEvent(RESPONSE_EVENT as ResponseEvent);

		const item = historyList().querySelector(
			".history-event",
		) as HTMLElement;
		const detailBlocks = Array.from(
			item.querySelectorAll("details"),
		) as HTMLDetailsElement[];
		expect(detailBlocks).toHaveLength(2);
		// Both start collapsed; expand/collapse is native <details> behavior,
		// so the DOM contract is the open property, toggled here directly
		// (jsdom does not simulate the summary-click activation behavior
		// reliably across versions).
		detailBlocks.forEach((details) => expect(details.open).toBe(false));
		expect(detailBlocks[0].querySelector("summary")?.textContent).toBe(
			"Request",
		);
		expect(detailBlocks[1].querySelector("summary")?.textContent).toContain(
			"Response:",
		);

		detailBlocks[1].open = true;
		expect(detailBlocks[1].open).toBe(true);
		expect(detailBlocks[1].querySelector("pre")?.textContent).toContain(
			"Hello, Ada!",
		);
	});

	test("each request entry offers a Revisit button (currently unwired)", () => {
		// The button exists in the DOM but addRequest never attaches a click
		// handler to it (there is a TODO in HistoryPanel.addRequest), so
		// only its presence can be asserted.
		const panel = createPanel();
		panel.handleEvent(requestEvent());

		const revisit = historyList().querySelector(
			".request-recreate-link",
		) as HTMLButtonElement;
		expect(revisit).not.toBeNull();
		expect(revisit.textContent).toBe("Revisit");
	});
});

describe("state panel representation rendering", () => {
	function renderRep(rep: unknown): HTMLElement {
		const panel = createPanel();
		panel.handleEvent(stateEvent(rep));
		return container().querySelector(
			"[id^='drafter-debug-current-state-content-']",
		) as HTMLElement;
	}

	test("empty_linear_collection renders [] with an Empty label", () => {
		const content = renderRep({
			kind: "empty_linear_collection",
			type: "list",
			id: 1,
			complexity: 1,
		});
		const rep = content.querySelector(
			".drafter-debug-rep-empty-linear-collection",
		);
		expect(rep?.textContent).toContain("[]");
		expect(rep?.textContent).toContain("Empty list");
	});

	test("linear_collection renders the item count and each element", () => {
		const content = renderRep({
			kind: "linear_collection",
			type: "list",
			elementType: "Any",
			fullType: "list",
			elements: [prim("1"), prim("'two'", "str")],
			id: 2,
			complexity: 5,
		});
		const rep = content.querySelector(
			".drafter-debug-rep-linear-collection",
		);
		expect(rep?.textContent).toContain("list");
		expect(rep?.textContent).toContain("(2 items)");
		expect(
			rep?.querySelectorAll(".drafter-debug-rep-lc-element"),
		).toHaveLength(2);
		expect(rep?.textContent).toContain("'two'");
	});

	test("tuple renders the item count and each element", () => {
		const content = renderRep({
			kind: "tuple",
			type: "tuple",
			fullType: "tuple[int, int]",
			elements: [prim("3"), prim("4")],
			id: 3,
			complexity: 5,
		});
		const rep = content.querySelector(".drafter-debug-rep-tuple");
		expect(rep?.textContent).toContain("(2 items)");
		expect(
			rep?.querySelectorAll(".drafter-debug-rep-tuple-element"),
		).toHaveLength(2);
	});

	test("empty_tuple renders ()", () => {
		const content = renderRep({
			kind: "empty_tuple",
			type: "tuple",
			id: 4,
			complexity: 1,
		});
		const rep = content.querySelector(".drafter-debug-rep-empty-tuple");
		expect(rep?.textContent).toContain("()");
		expect(rep?.textContent).toContain("Empty tuple");
	});

	test("dict renders entry count with key/value cells", () => {
		const content = renderRep({
			kind: "dict",
			type: "dict",
			areKeysHomogenous: true,
			areValuesHomogenous: true,
			keyType: "str",
			valueType: "int",
			fullType: "dict[str, int]",
			entries: [
				{ key: prim("'lives'", "str"), value: prim("3") },
				{ key: prim("'score'", "str"), value: prim("77") },
			],
			id: 5,
			complexity: 9,
		});
		const rep = content.querySelector(".drafter-debug-rep-dict");
		expect(rep?.textContent).toContain("(2 entries)");
		const entries = rep?.querySelectorAll(".drafter-debug-rep-dict-entry");
		expect(entries).toHaveLength(2);
		expect(entries?.[0].textContent).toContain("'lives'");
		expect(entries?.[0].textContent).toContain("3");
	});

	test("empty_dict renders {}", () => {
		const content = renderRep({
			kind: "empty_dict",
			type: "dict",
			id: 6,
			complexity: 1,
		});
		const rep = content.querySelector(".drafter-debug-rep-empty-dict");
		expect(rep?.textContent).toContain("{}");
		expect(rep?.textContent).toContain("Empty dict");
	});

	test("homogenous_grid renders a row per inner collection", () => {
		const row = (values: string[]) => ({
			kind: "homogenous_linear_collection",
			type: "list",
			elementType: "int",
			fullType: "list[int]",
			elements: values.map((v) => prim(v)),
			id: repIdCounter++,
			complexity: 3,
		});
		const content = renderRep({
			kind: "homogenous_grid",
			type: "list",
			elementType: "int",
			fullType: "list[list[int]]",
			rows: [row(["1", "2"]), row(["3", "4"])],
			id: 7,
			complexity: 12,
		});
		const rep = content.querySelector(".drafter-debug-rep-homogenous-grid");
		expect(rep?.textContent).toContain("list[list[int]]");
		expect(rep?.querySelectorAll(".drafter-debug-rep-hg-row")).toHaveLength(
			2,
		);
		expect(
			rep?.querySelectorAll(".drafter-debug-rep-hg-element"),
		).toHaveLength(4);
	});

	test("cycle_reference renders the circular-reference notice", () => {
		const content = renderRep({
			kind: "cycle_reference",
			type: "State",
			targetId: 42,
			id: 8,
			complexity: 1,
		});
		expect(
			content.querySelector(".drafter-debug-rep-cycle")?.textContent,
		).toContain("Circular reference to State (ID: 42)");
	});

	test("max_depth_reached renders the depth notice", () => {
		const content = renderRep({
			kind: "max_depth_reached",
			type: "dict",
			id: 9,
			complexity: 1,
		});
		expect(
			content.querySelector(".drafter-debug-rep-max-depth")?.textContent,
		).toContain("max depth reached for dict");
	});

	test("error representation renders message, type, and value", () => {
		const content = renderRep({
			kind: "error",
			error_message: "cannot describe this",
			type: "Sprite",
			value: "<Sprite at 0x7f>",
			id: 10,
			complexity: 1,
		});
		const rep = content.querySelector(".drafter-debug-rep-error");
		expect(rep?.textContent).toContain("⚠️ Error: cannot describe this");
		expect(rep?.textContent).toContain("Type: Sprite");
		expect(rep?.textContent).toContain("Value: <Sprite at 0x7f>");
	});

	test("complete_failure renders both error messages", () => {
		const content = renderRep({
			kind: "complete_failure",
			type: "Sprite",
			error_message: "describe failed",
			new_error_message: "repr also failed",
			id: 11,
			complexity: 1,
		});
		const rep = content.querySelector(".drafter-debug-rep-failure");
		expect(rep?.textContent).toContain("❌ Complete Failure");
		expect(rep?.textContent).toContain("Original error: describe failed");
		expect(rep?.textContent).toContain("Recovery error: repr also failed");
	});

	test("image with data renders an <img> and caption", () => {
		const dataUri =
			"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAA";
		const content = renderRep({
			kind: "image",
			type: "Picture",
			value: dataUri,
			filename: "dog.png",
			width: 640,
			height: 480,
			mime: "image/png",
			id: 12,
			complexity: 5,
		});
		const img = content.querySelector(
			".drafter-debug-rep-image img",
		) as HTMLImageElement;
		expect(img).not.toBeNull();
		expect(img.getAttribute("src")).toBe(dataUri);
		expect(
			content.querySelector(".drafter-debug-rep-image-caption")
				?.textContent,
		).toBe("dog.png — 640×480 — PNG");
		expect(
			content.querySelector(".drafter-debug-rep-image")?.textContent,
		).toContain("Picture");
	});

	test("image without data renders a placeholder", () => {
		const content = renderRep({
			kind: "image",
			type: "Picture",
			value: null,
			filename: null,
			width: null,
			height: null,
			mime: null,
			id: 13,
			complexity: 5,
		});
		expect(
			content.querySelector(".drafter-debug-rep-image img"),
		).toBeNull();
		expect(
			content.querySelector(".drafter-debug-rep-image")?.textContent,
		).toContain("Image not available");
	});

	test("bytes renders length and hex preview", () => {
		const content = renderRep({
			kind: "bytes",
			type: "bytes",
			length: 11,
			preview: "68 65 6c 6c 6f 20 77 6f 72 6c 64",
			thumbnail: null,
			id: 15,
			complexity: 2,
		});
		const rep = content.querySelector(".drafter-debug-rep-bytes");
		expect(rep?.textContent).toContain("68 65 6c 6c 6f");
		expect(rep?.textContent).toContain("bytes (11 bytes)");
		expect(rep?.querySelector("img")).toBeNull();
	});

	test("image bytes render a thumbnail", () => {
		const dataUri =
			"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAA";
		const content = renderRep({
			kind: "bytes",
			type: "bytes",
			length: 2048,
			preview: "89 50 4e 47 0d 0a 1a 0a",
			thumbnail: dataUri,
			id: 16,
			complexity: 2,
		});
		const img = content.querySelector(
			".drafter-debug-rep-bytes img",
		) as HTMLImageElement;
		expect(img).not.toBeNull();
		expect(img.getAttribute("src")).toBe(dataUri);
	});

	test("unknown representation renders type and value", () => {
		const content = renderRep({
			kind: "unknown",
			type: "generator",
			value: "<generator object f>",
			id: 14,
			complexity: 1,
		});
		const rep = content.querySelector(".drafter-debug-rep-unknown");
		expect(rep?.textContent).toContain("generator");
		expect(rep?.textContent).toContain("<generator object f>");
	});

	test("declared 'class' kind falls through to the default renderer", () => {
		// SUSPECTED GAP: ClassInstanceRepresentation declares kind
		// "class" | "dataclass" (telemetry/state.ts) but renderRepresentation
		// only handles "dataclass". A plain class instance renders through
		// the default branch, silently dropping its fields. Same applies to
		// the declared "union" kind. Documented, not fixed.
		const content = renderRep({
			kind: "class",
			type: "Dog",
			fullType: "Dog",
			fields: [{ name: "name", value: prim("'Rex'", "str") }],
			id: 15,
			complexity: 3,
		});
		const fallback = content.querySelector(".drafter-debug-rep-default");
		expect(fallback?.textContent).toContain("class");
		expect(fallback?.textContent).toContain("Dog");
		expect(content.textContent).not.toContain("Rex");
	});
});

describe("config panel interactions", () => {
	function configPanelWithInitial(): DebugPanel {
		const panel = createPanel();
		panel.handleEvent(
			INITIAL_CONFIGURATION as unknown as InitialConfigurationEvent,
		);
		return panel;
	}

	function themeItem(): HTMLElement {
		return container().querySelector(
			'.drafter-debug-config-item[data-key="theme"]',
		) as HTMLElement;
	}

	test("edit + save a valid override marks the item and persists it", () => {
		configPanelWithInitial();

		(
			themeItem().querySelector(
				".drafter-debug-config-edit",
			) as HTMLButtonElement
		).click();

		// Edit mode: the item was re-rendered with an editor pre-filled with
		// the pretty-printed current value.
		const editor = themeItem().querySelector(
			".drafter-debug-config-editor",
		) as HTMLTextAreaElement;
		expect(editor).not.toBeNull();
		expect(editor.value).toBe('"default"');

		editor.value = '"midnight"';
		(
			themeItem().querySelector(
				".drafter-debug-config-save",
			) as HTMLButtonElement
		).click();

		const item = themeItem();
		expect(
			item.classList.contains("drafter-debug-config-item-overridden"),
		).toBe(true);
		expect(
			item.querySelector(".drafter-debug-config-source")?.textContent,
		).toBe("Override");
		expect(
			item.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"midnight"');
		expect(
			item.querySelector(".drafter-debug-config-base-value")?.textContent,
		).toContain('embedded: "default"');

		// Persisted to localStorage and mirrored onto the window overrides.
		expect(
			JSON.parse(
				window.localStorage.getItem(OVERRIDES_STORAGE_KEY) ?? "{}",
			),
		).toEqual({ theme: "midnight" });
		expect(
			(window as any).DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES,
		).toEqual({ theme: "midnight" });
	});

	test("saving invalid JSON shows an inline error and stays in edit mode", () => {
		configPanelWithInitial();
		(
			themeItem().querySelector(
				".drafter-debug-config-edit",
			) as HTMLButtonElement
		).click();
		const editor = themeItem().querySelector(
			".drafter-debug-config-editor",
		) as HTMLTextAreaElement;
		editor.value = "{not json";

		(
			themeItem().querySelector(
				".drafter-debug-config-save",
			) as HTMLButtonElement
		).click();

		const errorTag = themeItem().querySelector(
			".drafter-debug-config-error",
		) as HTMLElement;
		expect(errorTag.classList.contains("visible")).toBe(true);
		expect(errorTag.textContent).not.toBe("");
		// Still editing; nothing was persisted.
		expect(
			themeItem().querySelector(".drafter-debug-config-editor"),
		).not.toBeNull();
		expect(window.localStorage.getItem(OVERRIDES_STORAGE_KEY)).toBeNull();
	});

	test("cancel leaves the embedded value untouched", () => {
		configPanelWithInitial();
		(
			themeItem().querySelector(
				".drafter-debug-config-edit",
			) as HTMLButtonElement
		).click();
		const editor = themeItem().querySelector(
			".drafter-debug-config-editor",
		) as HTMLTextAreaElement;
		editor.value = '"discarded"';

		(
			themeItem().querySelector(
				".drafter-debug-config-cancel",
			) as HTMLButtonElement
		).click();

		const item = themeItem();
		expect(item.querySelector(".drafter-debug-config-editor")).toBeNull();
		expect(
			item.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"default"');
		expect(
			item.querySelector(".drafter-debug-config-source")?.textContent,
		).toBe("Embedded");
	});

	test("clearing a single override returns the item to Embedded", () => {
		configPanelWithInitial();
		(
			themeItem().querySelector(
				".drafter-debug-config-edit",
			) as HTMLButtonElement
		).click();
		(
			themeItem().querySelector(
				".drafter-debug-config-editor",
			) as HTMLTextAreaElement
		).value = '"midnight"';
		(
			themeItem().querySelector(
				".drafter-debug-config-save",
			) as HTMLButtonElement
		).click();

		(
			themeItem().querySelector(
				".drafter-debug-config-clear",
			) as HTMLButtonElement
		).click();

		const item = themeItem();
		expect(
			item.classList.contains("drafter-debug-config-item-overridden"),
		).toBe(false);
		expect(
			item.querySelector(".drafter-debug-config-source")?.textContent,
		).toBe("Embedded");
		expect(
			item.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"default"');
		expect(
			JSON.parse(
				window.localStorage.getItem(OVERRIDES_STORAGE_KEY) ?? "null",
			),
		).toEqual({});
	});

	test("clear-all removes every override and the storage key", () => {
		configPanelWithInitial();
		(
			themeItem().querySelector(
				".drafter-debug-config-edit",
			) as HTMLButtonElement
		).click();
		(
			themeItem().querySelector(
				".drafter-debug-config-editor",
			) as HTMLTextAreaElement
		).value = '"midnight"';
		(
			themeItem().querySelector(
				".drafter-debug-config-save",
			) as HTMLButtonElement
		).click();

		(
			container().querySelector(
				"[class*='drafter-debug-config-clear-all']",
			) as HTMLButtonElement
		).click();

		expect(window.localStorage.getItem(OVERRIDES_STORAGE_KEY)).toBeNull();
		expect(
			themeItem().querySelector(".drafter-debug-config-source")
				?.textContent,
		).toBe("Embedded");
		expect(
			container().querySelector(".drafter-debug-config-item-overridden"),
		).toBeNull();
	});

	test("overrides persisted in localStorage apply on construction", () => {
		window.localStorage.setItem(
			OVERRIDES_STORAGE_KEY,
			JSON.stringify({ theme: "ocean" }),
		);

		configPanelWithInitial();

		const item = themeItem();
		expect(
			item.classList.contains("drafter-debug-config-item-overridden"),
		).toBe(true);
		expect(
			item.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"ocean"');
		expect(
			item.querySelector(".drafter-debug-config-source")?.textContent,
		).toBe("Override");
	});

	test("an UpdatedConfiguration on an overridden key keeps the override visible", () => {
		// The override wins over the new embedded value in the inline
		// display; the new base value is shown as "embedded:".
		const panel = configPanelWithInitial();
		(
			themeItem().querySelector(
				".drafter-debug-config-edit",
			) as HTMLButtonElement
		).click();
		(
			themeItem().querySelector(
				".drafter-debug-config-editor",
			) as HTMLTextAreaElement
		).value = '"midnight"';
		(
			themeItem().querySelector(
				".drafter-debug-config-save",
			) as HTMLButtonElement
		).click();

		panel.handleEvent(UPDATED_CONFIGURATION as UpdatedConfigurationEvent);

		const item = themeItem();
		expect(
			item.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"midnight"');
		expect(
			item.querySelector(".drafter-debug-config-base-value")?.textContent,
		).toContain('embedded: "dark"');
		expect(
			item.classList.contains("drafter-debug-config-item-updated"),
		).toBe(true);
	});

	// NOT TESTED: the "Reload page" button calls window.location.reload(),
	// which jsdom does not implement and whose location object cannot be
	// spied on (non-configurable). Presence is implied by the initialize()
	// wiring not throwing during construction.
});

describe("event log", () => {
	function logContent(): HTMLElement {
		return container().querySelector(
			"[id^='drafter-debug-log-content-']",
		) as HTMLElement;
	}

	test("handled events are also mirrored into the event log", () => {
		const panel = createPanel();

		expect(panel.handleEvent(ROUTE_ADDED as RouteAddedEvent)).toBe(true);

		// The routes panel rendered it AND the log recorded it at its
		// metadata level ("info"), bullet-prefixed.
		const entry = logContent().querySelector(".drafter-log-info-item");
		expect(entry?.textContent).toBe("• RouteAdded");
	});

	test("metadata level 'error' without an envelope uses the error renderer", () => {
		const panel = createPanel();
		const fixture = {
			kind: "SomethingBad",
			metadata: {
				source: "client_server.test",
				level: "error",
				id: 60,
				version: "2.0.0b10",
				timestamp: "2026-07-23T10:15:36.000000",
			},
			correlation: {},
		} as TelemetryRecord;

		expect(panel.handleEvent(fixture)).toBe(false);

		const entry = logContent().querySelector(".drafter-log-error-item");
		expect(entry?.textContent).toBe("❌ SomethingBad");
	});

	test("metadata level 'warning' without an envelope uses the warning renderer", () => {
		const panel = createPanel();
		const fixture = {
			kind: "SomethingIffy",
			metadata: {
				source: "client_server.test",
				level: "warning",
				id: 61,
				version: "2.0.0b10",
				timestamp: "2026-07-23T10:15:36.500000",
			},
			correlation: {},
		} as TelemetryRecord;

		panel.handleEvent(fixture);

		const entry = logContent().querySelector(".drafter-log-warning-item");
		expect(entry?.textContent).toBe("⚠ SomethingIffy");
	});

	test("log entries accumulate in arrival order", () => {
		const panel = createPanel();
		panel.handleEvent(ROUTE_ADDED as RouteAddedEvent);
		panel.handleEvent(REQUEST_EVENT as RequestEvent);

		// The log's initial content is an empty <div>; entries append after
		// it, so filter to the log-item elements.
		const entries = Array.from(
			logContent().querySelectorAll("[class*='drafter-log-']"),
		).map((entry) => entry.textContent);
		expect(entries).toEqual(["• RouteAdded", "• RequestEvent"]);
	});

	test("TS-side system errors reach the log through the engine sink", () => {
		// The DebugPanel constructor registers itself via setSystemErrorSink;
		// a warning-severity report has "log" presentation, so the panel's
		// event log is the only place it surfaces.
		createPanel();

		reportSystemError({
			id: "runtime.debug_panel_test_warning",
			category: "runtime",
			message: "Engine hiccup, carrying on",
			severity: "warning",
		});

		const entry = logContent().querySelector(".drafter-log-warning-item");
		expect(entry?.textContent).toContain("Engine hiccup, carrying on");
		// No dialog for warning severity (dialogs render a close button).
		expect(document.querySelector(".drafter-dialog-close")).toBeNull();
	});
});

describe("files panel", () => {
	test("refresh with an unknown engine logs an error and lists nothing", () => {
		createPanel();

		(
			container().querySelector(
				".drafter-debug-refresh-client-btn",
			) as HTMLButtonElement
		).click();

		expect(consoleErrorSpy).toHaveBeenCalledWith(
			"Unknown DRAFTER_ENGINE:",
			undefined,
		);
		expect(
			container().querySelector(
				".drafter-debug-files-local .drafter-debug-files-list-items",
			)?.children,
		).toHaveLength(0);
	});

	test("skulpt engine lists files and previews one on click", () => {
		(window as any).DRAFTER_ENGINE = "skulpt";
		(globalThis as any).Sk = {
			builtinFiles: {
				files: {
					"main.py": "print('hello from drafter')",
					"helpers.py": "x = 1",
				},
			},
		};
		createPanel();

		(
			container().querySelector(
				".drafter-debug-refresh-client-btn",
			) as HTMLButtonElement
		).click();

		const items = container().querySelector(
			".drafter-debug-files-local .drafter-debug-files-list-items",
		) as HTMLElement;
		const names = Array.from(items.querySelectorAll("code")).map(
			(code) => code.textContent,
		);
		expect(names).toEqual(["main.py", "helpers.py"]);

		(items.querySelector("code") as HTMLElement).click();

		// previewFile appends a dialog directly to document.body.
		const title = Array.from(document.body.querySelectorAll("h2")).find(
			(h2) => h2.textContent === "Preview: main.py",
		);
		expect(title).not.toBeUndefined();
		expect(
			title?.parentElement?.querySelector("pre")?.textContent,
		).toContain("print('hello from drafter')");
	});

	// NOT TESTED: the pyodide branch of getAllClientFiles/getFileContents
	// needs a real pyodide.FS; that path is exercised by the integration
	// suite under __tests__/pyodide/. The Host File System list has no
	// implementation at all yet (the Refresh button is rendered but
	// FilesPanel.initialize only wires the client refresh button).
});

describe("multiple instances", () => {
	test("two panels mount independently and events stay scoped", () => {
		mountHost({ containers: ["debug-a", "debug-b"] });
		const bridgeA = makeBridge();
		const bridgeB = makeBridge();
		const panelA = new DebugPanel("debug-a", bridgeA);
		const panelB = new DebugPanel("debug-b", bridgeB);

		expect(instanceIdOf(container("debug-a"))).not.toBe(
			instanceIdOf(container("debug-b")),
		);

		panelA.handleEvent(ROUTE_ADDED as RouteAddedEvent);
		panelB.handleEvent(requestEvent({ request_id: 1, url: "only-in-b" }));

		// Panel A got the route; panel B did not.
		expect(
			container("debug-a").querySelector(
				".drafter-debug-route-signature",
			),
		).not.toBeNull();
		expect(
			container("debug-b").querySelector(
				".drafter-debug-route-signature",
			),
		).toBeNull();

		// Panel B got the history entry; panel A did not.
		expect(
			container("debug-b").querySelector(".history-event"),
		).not.toBeNull();
		expect(container("debug-a").querySelector(".history-event")).toBeNull();

		// Each panel logged only its own events.
		expect(
			container("debug-a").querySelector(
				"[id^='drafter-debug-log-content-']",
			)?.textContent,
		).toContain("RouteAdded");
		expect(
			container("debug-a").querySelector(
				"[id^='drafter-debug-log-content-']",
			)?.textContent,
		).not.toContain("RequestEvent");
		expect(
			container("debug-b").querySelector(
				"[id^='drafter-debug-log-content-']",
			)?.textContent,
		).toContain("RequestEvent");
	});
});
