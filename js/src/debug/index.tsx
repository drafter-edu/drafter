import type { TelemetryRecord, TypedRecord } from "./telemetry";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";
import { setSystemErrorSink } from "../bridge/engine";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { TestCaseEvent } from "./telemetry/tests";
import { TestPanel } from "./panels/testing";
import { StatePanel } from "./panels/state";
import { StateHistoryPanel } from "./panels/state_history";
import { RoutesPanel } from "./panels/routes";
import { HistoryPanel } from "./panels/history";
import { LogPanel } from "./panels/log";
import { DebugPanelError, extractErrorDetails } from "./utils/errors";
import type { Panel } from "./panels/panel";
import { ConfigPanel } from "./panels/config";
import { FilesPanel } from "./panels/files";
import { CurrentPanel } from "./panels/current";
import { RouteGraphPanel } from "./panels/route_graph";
import { CoveragePanel } from "./panels/coverage";
import { TestWizardPanel } from "./panels/test_wizard";
import { PackagesPanel } from "./panels/packages";
import { RuntimeInfoPanel } from "./panels/runtime_info";
import { StoragePanel } from "./panels/storage";
import { InternalsPanel } from "./panels/internals";
import { attachPrinterConsole } from "../console/printer";
import { TabBar } from "./tabs";
import {
	HeaderMenuBar,
	type MenuDefinition,
	type MenuItemDefinition,
} from "./menubar";
import { getCurrentSourceCode, openCodeEditor } from "./editor";
import { openSourceViewer } from "./viewsource";
import { openStateEditor } from "./state_edit";
import { openThemeSwitcher } from "./theme_switch";
import { downloadBugReport, SaveLoadManager } from "./saveload";

const DOCUMENTATION_URL = "https://drafter-edu.github.io/drafter/";

export class DebugPanel {
	private static instanceCounter = 0;
	private instanceId: number;

	private panelElement: HTMLElement | null = null;
	private contentElement: HTMLElement | null = null;
	private events: TelemetryRecord[] = [];
	private pageHistory: any[] = [];
	private errors: any[] = [];
	private warnings: any[] = [];
	private isVisible: boolean = true;
	private headerBar: DebugHeaderBar;
	private footerBar: DebugFooterBar;
	private testingPanel: TestPanel;
	private statePanel: StatePanel;
	private stateHistoryPanel: StateHistoryPanel;
	private routesPanel: RoutesPanel;
	private historyPanel: HistoryPanel;
	private configPanel: ConfigPanel;
	private logPanel: LogPanel;
	private filesPanel: FilesPanel;
	private currentPanel: CurrentPanel;
	private routeGraphPanel: RouteGraphPanel;
	private coveragePanel: CoveragePanel;
	private testWizardPanel: TestWizardPanel;
	private packagesPanel: PackagesPanel;
	private runtimeInfoPanel: RuntimeInfoPanel;
	private storagePanel: StoragePanel;
	private internalsPanel: InternalsPanel;
	private panels: Panel[];
	private tabBar!: TabBar;
	private panelMenuBar!: HeaderMenuBar;
	private saveLoad: SaveLoadManager = new SaveLoadManager();
	private lastRoute: string | null = null;
	// Problems on the CURRENT page (reset on each navigation); the Log tab
	// keeps the cumulative record.
	private currentErrorCount = 0;
	private currentWarningCount = 0;

	// The node to scope all debug DOM lookups to: the instance's shadow root
	// when shadow DOM is on, else document. Lets concurrent instances each
	// mount their own debug panel without colliding on shared ids/classes.
	private root: ParentNode;

	constructor(
		private containerId: string,
		private clientBridge: ClientBridgeWrapperInterface,
		// May arrive as null when marshalled from Python (None -> null), which
		// bypasses default params, so normalize explicitly.
		root: ParentNode | null = document,
	) {
		this.root = root ?? document;
		this.instanceId = DebugPanel.instanceCounter++;

		this.headerBar = new DebugHeaderBar(
			"",
			this.root,
			this.createMenuDefinitions(),
		);
		this.footerBar = new DebugFooterBar(this.root, () =>
			this.activateTab("current"),
		);
		this.testingPanel = new TestPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.statePanel = new StatePanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.stateHistoryPanel = new StateHistoryPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.routesPanel = new RoutesPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.historyPanel = new HistoryPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.logPanel = new LogPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.configPanel = new ConfigPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.filesPanel = new FilesPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.currentPanel = new CurrentPanel(
			this.containerId,
			this.instanceId,
			this.root,
			() => this.statePanel.getDiffTexts(),
		);
		this.routeGraphPanel = new RouteGraphPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.coveragePanel = new CoveragePanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.testWizardPanel = new TestWizardPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.packagesPanel = new PackagesPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.runtimeInfoPanel = new RuntimeInfoPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.storagePanel = new StoragePanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.internalsPanel = new InternalsPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.panels = [
			this.currentPanel,
			this.statePanel,
			this.historyPanel,
			this.stateHistoryPanel,
			this.routesPanel,
			this.routeGraphPanel,
			this.testingPanel,
			this.coveragePanel,
			this.testWizardPanel,
			this.filesPanel,
			this.packagesPanel,
			this.configPanel,
			this.runtimeInfoPanel,
			this.logPanel,
			this.storagePanel,
			this.internalsPanel,
		];

		const container = this.getContainerElement();
		this.panelElement = this.createPanelStructure();
		container.appendChild(this.panelElement);
		this.contentElement = this.panelElement.querySelector(
			".drafter-debug-content",
		);

		// Panels resolve their DOM by id under this.root, so initialize()
		// must run only after the tab structure is appended above. Hidden
		// tabpanels are still in the DOM (hidden, not detached), so panels
		// in inactive tabs initialize and update normally.
		this.panels.forEach((p) => p.initialize());

		// Mount the printer console (captured print output + Python REPL)
		// into this instance's footer. The debug panel is constructed exactly
		// once per instance run — including in production mode, where the
		// hover/toast console modes still need a mount point.
		attachPrinterConsole(this.root);

		// Receive TypeScript-side system errors (boot/runtime failures) so
		// they appear in the event log alongside Python telemetry.
		setSystemErrorSink((event) => {
			this.handleEvent(event as unknown as TelemetryRecord);
		});
	}

	private reportError(message: string) {
		console.error("[DebugPanel] Error:", message);
		this.errors.push(message);
		return new DebugPanelError(message);
	}

	private getContainerElement(): HTMLElement {
		const container = this.root.querySelector(
			`#${this.containerId}`,
		) as HTMLElement | null;
		if (!container) {
			throw this.reportError(
				`DebugPanel: Container with id '${this.containerId}' not found.`,
			);
		}
		return container;
	}

	public setHeaderTitle(title: string) {
		if (this.headerBar) {
			this.headerBar.setTitle(title);
		}
	}
	public setRoute(route: string) {
		this.lastRoute = route;
		if (this.footerBar) {
			this.footerBar.setRoute(route);
		}
		this.currentPanel?.setRoute(route);
	}

	/** The generated HTML currently rendered into the site body. */
	private getPageHtml(): string | null {
		const body = this.root.querySelector(
			".drafter-body--",
		) as HTMLElement | null;
		return body ? body.innerHTML : null;
	}

	private createPanelStructure(): HTMLElement {
		const panel = document.createElement("div");
		panel.className = "drafter-debug-panel";
		panel.id = `drafter-debug-panel-${this.instanceId}`;

		// Five student-facing tab areas. Several tabs will gain additional
		// panels (route graph, coverage, packages, ...) as they are built;
		// each tab's content is just the member panels' structures in order.
		this.tabBar = new TabBar(this.instanceId, [
			{
				id: "current",
				labelKey: "debug.tab.current",
				content: [
					this.currentPanel.createStructure(),
					this.statePanel.createStructure(),
				],
			},
			{
				id: "history",
				labelKey: "debug.tab.history",
				content: [
					this.historyPanel.createStructure(),
					this.stateHistoryPanel.createStructure(),
				],
			},
			{
				id: "overview",
				labelKey: "debug.tab.overview",
				content: [
					this.routesPanel.createStructure(),
					this.routeGraphPanel.createStructure(),
				],
			},
			{
				id: "tests",
				labelKey: "debug.tab.tests",
				content: [
					this.testingPanel.createStructure(),
					// TODO: Finish these panels
					// this.coveragePanel.createStructure(),
					// this.testWizardPanel.createStructure(),
				],
			},
			{
				id: "environment",
				labelKey: "debug.tab.environment",
				content: [
					this.filesPanel.createStructure(),
					this.packagesPanel.createStructure(),
					this.configPanel.createStructure(),
					this.runtimeInfoPanel.createStructure(),
					this.logPanel.createStructure(),
					this.storagePanel.createStructure(),
					this.internalsPanel.createStructure(),
				],
			},
		]);

		// The panel's own top-right menu duplicates the view-settings
		// toggles: with the frame (and its header menus) hidden, this is
		// the only way to bring the frame back.
		this.panelMenuBar = new HeaderMenuBar([
			{
				id: "panel-view",
				labelKey: "menu.view",
				items: this.createViewSettingsItems(),
			},
		]);

		const ui = (
			<div class="drafter-debug-panel">
				<div class="drafter-debug-header-left">
					<div class="drafter-debug-header-top">
						<div>
							<div class="drafter-debug-header-title">
								Debug Panel
							</div>
							<div class="drafter-debug-header-subtitle"></div>
						</div>
						{this.panelMenuBar.element}
					</div>
					{this.tabBar.createTabList()}
				</div>
				<div class="drafter-debug-content">
					{this.tabBar.createTabPanels()}
				</div>
			</div>
		);
		panel.appendChild(ui);

		return panel;
	}

	/** Bring the given tab (e.g. "current") to the front. */
	public activateTab(tabId: string): void {
		this.tabBar?.activate(tabId);
	}

	private navigate(target: string): void {
		window.dispatchEvent(
			new CustomEvent("drafter-navigate", { detail: target }),
		);
	}

	/**
	 * The view-settings items (frame / production / theme). Shared between
	 * the header's View menu and the debug panel's own top-right menu — the
	 * latter matters because hiding the frame hides the header, and without
	 * a second home for these toggles there would be no way back.
	 */
	private createViewSettingsItems(): MenuItemDefinition[] {
		return [
			{
				labelKey: "menu.toggle_frame",
				iconKey: "icon.toggle_frame",
				tooltipKey: "menu.toggle_frame.tooltip",
				className: "drafter-menu-item-toggle-frame",
				action: () => this.toggleFrame(),
			},
			{
				labelKey: "button.exit_debug",
				iconKey: "icon.exit_debug",
				tooltipKey: "button.exit_debug.tooltip",
				className: "drafter-menu-item-production",
				action: () =>
					window.dispatchEvent(
						new CustomEvent("drafter-toggle-debug-mode"),
					),
			},
			{
				labelKey: "menu.switch_theme",
				iconKey: "icon.switch_theme",
				tooltipKey: "menu.switch_theme.tooltip",
				className: "drafter-menu-item-switch-theme",
				action: () => openThemeSwitcher(),
			},
		];
	}

	/**
	 * The header dropdown menus. Actions close over `this`, so panels
	 * referenced here (constructed after the header bar) resolve lazily at
	 * click time.
	 */
	private createMenuDefinitions(): MenuDefinition[] {
		return [
			{
				id: "navigate",
				labelKey: "menu.navigate",
				items: [
					{
						labelKey: "button.home",
						iconKey: "icon.home",
						tooltipKey: "button.home.tooltip",
						className: "drafter-menu-item-home",
						action: () => this.navigate("index"),
					},
					{
						labelKey: "button.reset",
						iconKey: "icon.reset",
						tooltipKey: "button.reset.tooltip",
						className: "drafter-menu-item-reset",
						action: () => this.navigate("--reset"),
					},
					{
						labelKey: "menu.reload",
						iconKey: "icon.reload",
						tooltipKey: "menu.reload.tooltip",
						className: "drafter-menu-item-reload",
						action: () => this.navigate("--reload"),
					},
					{
						labelKey: "menu.replay",
						iconKey: "icon.replay",
						tooltipKey: "menu.replay.tooltip",
						className: "drafter-menu-item-replay",
						separatorAfter: true,
						action: () =>
							window.dispatchEvent(
								new CustomEvent("drafter-replay-route"),
							),
					},
					{
						labelKey: "button.about",
						iconKey: "icon.about",
						tooltipKey: "button.about.tooltip",
						className: "drafter-menu-item-about",
						action: () => this.navigate("--about"),
					},
				],
			},
			{
				id: "view",
				labelKey: "menu.view",
				items: [
					...this.createViewSettingsItems(),
					{
						labelKey: "menu.view_source",
						iconKey: "icon.view_source",
						tooltipKey: "menu.view_source.tooltip",
						className: "drafter-menu-item-view-source",
						action: () =>
							openSourceViewer(() => this.getPageHtml()),
					},
				],
			},
			{
				id: "edit",
				labelKey: "menu.edit",
				items: [
					{
						labelKey: "menu.edit_state",
						iconKey: "icon.edit_state",
						tooltipKey: "menu.edit_state.tooltip",
						className: "drafter-menu-item-edit-state",
						action: () =>
							openStateEditor(
								() => this.statePanel?.getPlainText() ?? "",
							),
					},
					{
						labelKey: "button.edit",
						iconKey: "icon.edit",
						tooltipKey: "button.edit.tooltip",
						className: "drafter-menu-item-edit-source",
						action: () => openCodeEditor(),
					},
				],
			},
			{
				id: "saveload",
				labelKey: "menu.saveload",
				items: [
					{
						labelKey: "menu.quick_save",
						iconKey: "icon.save",
						tooltipKey: "button.save.tooltip",
						className: "drafter-menu-item-quick-save",
						action: () =>
							this.saveLoad.requestSave("save", "quick"),
					},
					{
						labelKey: "menu.save_slot",
						iconKey: "icon.save",
						className: "drafter-menu-item-save-slot",
						separatorAfter: true,
						action: () => this.saveLoad.openSaveDialog(),
					},
					{
						labelKey: "menu.load_recent",
						iconKey: "icon.load",
						tooltipKey: "button.load.tooltip",
						className: "drafter-menu-item-load-recent",
						action: () => this.saveLoad.loadMostRecent(),
						// Show how long ago the last save happened; grey out
						// when nothing has been saved yet.
						dynamic: () => {
							const age = this.saveLoad.describeMostRecentAge();
							return {
								suffix: age ? ` (${age})` : "",
								disabled: age === null,
							};
						},
					},
					{
						labelKey: "menu.load_slot",
						iconKey: "icon.load",
						className: "drafter-menu-item-load-slot",
						separatorAfter: true,
						action: () => this.saveLoad.openLoadDialog(),
					},
					{
						labelKey: "menu.download_snapshot",
						iconKey: "icon.download",
						tooltipKey: "button.download.tooltip",
						className: "drafter-menu-item-download",
						action: () =>
							this.saveLoad.requestSave("download", "quick"),
					},
					{
						labelKey: "menu.upload_snapshot",
						iconKey: "icon.upload",
						tooltipKey: "button.upload.tooltip",
						className: "drafter-menu-item-upload",
						action: () => this.saveLoad.openUploadDialog(),
					},
				],
			},
			{
				id: "help",
				labelKey: "menu.help",
				items: [
					{
						labelKey: "menu.documentation",
						iconKey: "icon.documentation",
						tooltipKey: "menu.documentation.tooltip",
						className: "drafter-menu-item-documentation",
						action: () => window.open(DOCUMENTATION_URL, "_blank"),
					},
					{
						labelKey: "menu.bug_report",
						iconKey: "icon.bug_report",
						tooltipKey: "menu.bug_report.tooltip",
						className: "drafter-menu-item-bug-report",
						action: () =>
							downloadBugReport(this.events, {
								route: this.lastRoute,
								pageHtml: this.getPageHtml(),
								sourceCode: getCurrentSourceCode(),
							}),
					},
				],
			},
		];
	}

	private toggleFrame(): void {
		window.dispatchEvent(new CustomEvent("drafter-toggle-frame"));
		// const frames = document.querySelectorAll(
		//     ".drafter-padding-h--,.drafter-padding-v--,.drafter-header--,.drafter-footer--",
		// );
		// if (frames) {
		//     frames.forEach((frame) =>
		//         frame.classList.toggle("drafter-hidden--"),
		//     );
		// }
		// const body = document.querySelector(".drafter-body--");
		// if (body) {
		//     body.classList.toggle("drafter-body-frame-hidden--");
		// }
	}

	public handleEvent(event: TelemetryRecord): boolean {
		this.events.push(event);
		let handled = true;
		const typed = event as TypedRecord;
		switch (typed.kind) {
			case "RouteAdded":
				this.routesPanel?.renderRoute(
					typed.url,
					typed.signature,
					typed.is_system_route,
					typed.parameters ?? [],
				);
				break;
			case "RequestEvent":
				this.historyPanel?.addRequest(typed);
				// A new page visit starts a fresh problems slate for the
				// Current tab (the Log tab keeps the cumulative record).
				this.currentErrorCount = 0;
				this.currentWarningCount = 0;
				this.currentPanel?.startNavigation(typed.url);
				this.updateProblemIndicators();
				break;
			case "RequestParseEvent":
				handled = this.historyPanel?.addRequestParse(typed) ?? false;
				break;
			case "ResponseEvent":
				handled = this.historyPanel?.addResponse(typed) ?? false;
				this.currentPanel?.setPageContent(typed.formatted_page_content);
				break;
			case "UpdatedState":
				this.statePanel?.renderState(typed.representation);
				this.stateHistoryPanel?.addSnapshot(
					typed.representation,
					typed.correlation?.route ?? "",
				);
				break;
			case "StateSnapshot":
				this.saveLoad.handleSnapshot(typed);
				break;
			case "TestCaseEvent":
				this.testingPanel?.renderTest(typed);
				this.testingPanel?.updateTestSummary();
				this.tabBar?.setBadge(
					"tests",
					this.testingPanel?.getFailCount() ?? 0,
					"fail",
				);
				break;
			case "InitialConfiguration":
				this.configPanel?.renderInitialConfig(typed.config);
				break;
			case "UpdatedConfiguration":
				this.configPanel?.renderConfigUpdate(typed.key, typed.value);
				break;
			default:
				handled = false;
				break;
		}
		this.trackProblem(event);
		this.logPanel?.renderEvent(event);
		return handled;
	}

	/** Count error/warning envelopes for the Current tab and footer. */
	private trackProblem(event: TelemetryRecord): void {
		const envelope = extractErrorDetails(event);
		if (!envelope) {
			return;
		}
		if (envelope.severity === "error" || envelope.severity === "critical") {
			this.currentErrorCount++;
		} else if (envelope.severity === "warning") {
			this.currentWarningCount++;
		} else {
			return;
		}
		this.currentPanel?.addProblem(envelope);
		this.updateProblemIndicators();
	}

	private updateProblemIndicators(): void {
		this.tabBar?.setBadge(
			"current",
			this.currentErrorCount + this.currentWarningCount,
			this.currentErrorCount > 0 ? "error" : "warn",
		);
		this.footerBar?.setProblemCounts(
			this.currentErrorCount,
			this.currentWarningCount,
		);
	}
}
