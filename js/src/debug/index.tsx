import type { TelemetryRecord, TypedRecord } from "./telemetry";
import { t } from "../i18n";
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
import { DebugPanelError } from "./utils/errors";
import type { ReactElement } from "jsx-dom";
import type { Panel } from "./panels/panel";
import { intersperse } from "./utils/lists";
import { ConfigPanel } from "./panels/config";
import { FilesPanel } from "./panels/files";

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
	private panels: Panel[];

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

		this.headerBar = new DebugHeaderBar("", this.root);
		this.footerBar = new DebugFooterBar(this.root);
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
		this.panels = [
			this.statePanel,
			this.routesPanel,
			this.historyPanel,
			this.testingPanel,
			this.logPanel,
			this.configPanel,
			this.filesPanel,
		];

		const container = this.getContainerElement();
		this.panelElement = this.createPanelStructure();
		container.appendChild(this.panelElement);
		this.contentElement = this.panelElement.querySelector(
			".drafter-debug-content",
		);

		this.panels.forEach((p) => p.initialize());
		this.attachEventHandlers();

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
		if (this.footerBar) {
			this.footerBar.setRoute(route);
		}
	}

	private createPanelStructure(): HTMLElement {
		const panel = document.createElement("div");
		panel.className = "drafter-debug-panel";
		panel.id = `drafter-debug-panel-${this.instanceId}`;

		const links = intersperse<ReactElement | string>(
			this.panels.map((panel) => panel?.getAnchor()),
			"|",
		);
		const panelComponents = this.panels.map((panel) =>
			panel?.createStructure(),
		);

		const ui = (
			<div class="drafter-debug-panel">
				<div class="drafter-debug-header-left">
					<div>
						<div class="drafter-debug-header-title">
							Debug Panel
						</div>
						<div class="drafter-debug-header-subtitle"></div>
					</div>
					<div class="drafter-debug-header-buttons">{links}</div>
				</div>
				{this.createActionButtons()}
				<div class="drafter-debug-content">{panelComponents}</div>
			</div>
		);
		panel.appendChild(ui);

		return panel;
	}

	private createActionButtons() {
		const toggleFrame = (
			<button title="Show/Hide Frame" class="drafter-toggle-frame-button">
				👁️ Toggle Frame
			</button>
		);
		toggleFrame.addEventListener("click", () => {
			this.toggleFrame();
		});
		const exitDebug = (
			<button
				title={t("button.exit_debug.tooltip")}
				class="drafter-exit-debug-button"
			>
				{t("icon.exit_debug")} {t("button.exit_debug")}
			</button>
		);
		exitDebug.addEventListener("click", () => {
			window.dispatchEvent(new CustomEvent("drafter-toggle-debug-mode"));
		});
		return (
			<div class="drafter-debug-actions">
				<button
					title={t("button.home.tooltip")}
					class="drafter-home-button"
				>
					{t("icon.home")} {t("button.home")}
				</button>
				<button
					title={t("button.reset.tooltip")}
					class="drafter-reset-button"
				>
					{t("icon.reset")} {t("button.reset")}
				</button>
				{exitDebug}
				{toggleFrame}
			</div>
		);
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

	private attachEventHandlers(): void {
		const NAVIGATION_BUTTONS = [
			[".drafter-home-button", "index"],
			[".drafter-reset-button", "--reset"],
			[".drafter-about-button", "--about"],
		];
		NAVIGATION_BUTTONS.forEach(([selector, detail]) => {
			const buttons = this.root.querySelectorAll(selector);
			buttons.forEach((button) => {
				button.addEventListener("click", (event) => {
					event.preventDefault();
					window.dispatchEvent(
						new CustomEvent("drafter-navigate", { detail }),
					);
				});
			});
		});
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
				);
				break;
			case "RequestEvent":
				this.historyPanel?.addRequest(typed);
				break;
			case "RequestParseEvent":
				handled = this.historyPanel?.addRequestParse(typed) ?? false;
				break;
			case "ResponseEvent":
				handled = this.historyPanel?.addResponse(typed) ?? false;
				break;
			case "UpdatedState":
				this.statePanel?.renderState(typed.representation);
				break;
			case "TestCaseEvent":
				this.testingPanel?.renderTest(typed);
				this.testingPanel?.updateTestSummary();
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
		this.logPanel?.renderEvent(event);
		return handled;
	}
}
