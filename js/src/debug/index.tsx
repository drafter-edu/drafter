import type { TelemetryRecord, TypedRecord } from "./telemetry";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";
import { setSystemErrorSink } from "../bridge/engine";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { TestCaseEvent } from "./telemetry/tests";
import { TestPanel } from "./panels/testing";
import { StatePanel } from "./panels/state";
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
import { openHtmlConverter } from "./htmlconvert";
import { openStateEditor } from "./state_edit";
import { openThemeSwitcher } from "./theme_switch";
import { downloadBugReport, SaveLoadManager } from "./saveload";
import { DevServerErrorReporter } from "./error_reporter";
import {
	isDevServerDocument,
	ownerDocumentOf,
	requestDevServerStop,
} from "./dev_server";
import { alertDialog, confirmDialog } from "../dialogs";
import { t } from "../i18n";

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
	// Problems with no request correlation (startup/setup issues). They are
	// not tied to the page being shown, so they survive navigations.
	private globalErrorCount = 0;
	private globalWarningCount = 0;
	// Forwards error envelopes to the local dev server's debug log while the
	// site is not in production mode.
	private errorReporter = new DevServerErrorReporter();
	// Whether this instance's page was served by the local development
	// server, which is the only place the "Stop Server" control makes sense.
	private devServer = false;

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
		this.devServer = isDevServerDocument(ownerDocumentOf(this.root));
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
		this.routesPanel = new RoutesPanel(
			this.containerId,
			this.instanceId,
			this.root,
		);
		this.historyPanel = new HistoryPanel(
			this.containerId,
			this.instanceId,
			this.root,
			() => this.testingPanel.clearRegressionTests(),
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
				content: [this.historyPanel.createStructure()],
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

	/**
	 * Download the bug-report bundle (telemetry events, system status, page
	 * context). Used by the Help menu and, via the client bridge, by the
	 * download button on the `--bug-report` system route's page.
	 */
	public downloadBugReport(): void {
		downloadBugReport(this.events, {
			route: this.lastRoute,
			pageHtml: this.getPageHtml(),
			sourceCode: getCurrentSourceCode(),
		});
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
						separatorAfter: this.devServer,
						action: () => this.navigate("--about"),
					},
					...this.createStopServerItems(),
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
					{
						labelKey: "menu.convert_html",
						iconKey: "icon.convert_html",
						tooltipKey: "menu.convert_html.tooltip",
						className: "drafter-menu-item-convert-html",
						action: () => openHtmlConverter(),
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
						action: () => this.downloadBugReport(),
					},
				],
			},
		];
	}

	/**
	 * The Navigate menu's "Stop Server" item, present only when the page is
	 * served by the local development server (deployed sites have no server
	 * to stop).
	 */
	private createStopServerItems(): MenuItemDefinition[] {
		if (!this.devServer) {
			return [];
		}
		return [
			{
				labelKey: "menu.stop_server",
				iconKey: "icon.stop_server",
				tooltipKey: "menu.stop_server.tooltip",
				className: "drafter-menu-item-stop-server",
				action: () => {
					void this.stopServer();
				},
			},
		];
	}

	/**
	 * Stop the local development server. Used by the Navigate menu, which
	 * asks for confirmation first, and, via the client bridge, by the button
	 * on the `--stop-server` system route's page, where the page itself is
	 * the confirmation (`askFirst` false). Outside the development server
	 * it only explains that there is nothing to stop. The outcome is shown
	 * in a dialog; resolves to whether the server acknowledged the stop.
	 */
	public async stopServer(askFirst: boolean = true): Promise<boolean> {
		const title = t("menu.stop_server.title");
		if (!this.devServer) {
			await alertDialog(t("menu.stop_server.not_dev_server"), { title });
			return false;
		}
		if (askFirst) {
			const accepted = await confirmDialog(t("menu.stop_server.confirm"), {
				title,
				confirmLabel: t("menu.stop_server.confirm_button"),
				confirmVariant: "danger",
			});
			if (!accepted) {
				return false;
			}
		}
		const stopped = await requestDevServerStop();
		await alertDialog(
			t(stopped ? "menu.stop_server.stopped" : "menu.stop_server.failed"),
			{ title },
		);
		return stopped;
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
				this.testingPanel?.recordVisit(typed);
				break;
			case "UpdatedState":
				this.statePanel?.renderState(typed.representation);
				// The history panel shows the snapshot with the visit's
				// response details (below the generated unit test).
				this.historyPanel?.addStateSnapshot(
					typed.representation,
					typed.correlation?.request_id,
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
				this.errorReporter.setDebugMode(
					(typed.config as { in_debug_mode?: boolean } | undefined)
						?.in_debug_mode !== false,
				);
				break;
			case "UpdatedConfiguration":
				this.configPanel?.renderConfigUpdate(typed.key, typed.value);
				if (typed.key === "in_debug_mode") {
					this.errorReporter.setDebugMode(Boolean(typed.value));
				}
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
		const isError =
			envelope.severity === "error" || envelope.severity === "critical";
		if (!isError && envelope.severity !== "warning") {
			return;
		}
		// Problems without a request correlation are not tied to the page
		// being shown (startup/setup issues, often replayed into the panel
		// before the first navigation): keep them visible across navigations
		// instead of wiping them on the next RequestEvent.
		const isGlobal = envelope.context?.request_id == null;
		this.historyPanel?.noteProblem(envelope);
		// A repeat of a problem already on the slate raises that problem's
		// counter (in the Current tab) rather than the number of problems.
		const isNew = this.currentPanel?.addProblem(envelope, isGlobal) ?? true;
		if (isError) {
			// The log sender does its own counting of repeats.
			this.errorReporter.report(envelope);
		}
		if (!isNew) {
			return;
		}
		if (isError) {
			if (isGlobal) {
				this.globalErrorCount++;
			} else {
				this.currentErrorCount++;
			}
		} else if (isGlobal) {
			this.globalWarningCount++;
		} else {
			this.currentWarningCount++;
		}
		this.updateProblemIndicators();
	}

	private updateProblemIndicators(): void {
		const errors = this.currentErrorCount + this.globalErrorCount;
		const warnings = this.currentWarningCount + this.globalWarningCount;
		this.tabBar?.setBadge(
			"current",
			errors + warnings,
			errors > 0 ? "error" : "warn",
		);
		this.footerBar?.setProblemCounts(errors, warnings);
		this.updateDocumentTitle(errors, warnings);
	}

	/** The site title the browser tab showed before any problem prefix. */
	private plainDocumentTitle: string | null = null;

	/**
	 * Put the problem counts in front of the browser tab's title, so a
	 * student who switched tabs (or scrolled the panel away) can see that
	 * something went wrong. Only this instance's own document is touched.
	 */
	private updateDocumentTitle(errors: number, warnings: number): void {
		const doc = ownerDocumentOf(this.root);
		if (!doc) {
			return;
		}
		const current = doc.title;
		if (this.plainDocumentTitle === null) {
			this.plainDocumentTitle = current;
		} else if (!current.startsWith("(")) {
			// Something else (set_website_title) changed the title.
			this.plainDocumentTitle = current;
		}
		const parts: string[] = [];
		if (errors > 0) {
			parts.push(`${errors} ${errors === 1 ? "error" : "errors"}`);
		}
		if (warnings > 0) {
			parts.push(`${warnings} ${warnings === 1 ? "warning" : "warnings"}`);
		}
		const plain = this.plainDocumentTitle;
		doc.title = parts.length > 0 ? `(${parts.join(", ")}) ${plain}` : plain;
	}
}
