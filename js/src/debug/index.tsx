import type { TelemetryEvent } from "./telemetry";
import { t } from "../i18n";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";
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

export class DebugPanel {
    private static instanceCounter = 0;
    private instanceId: number;

    private panelElement: HTMLElement | null = null;
    private contentElement: HTMLElement | null = null;
    private events: TelemetryEvent[] = [];
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
    private logPanel: LogPanel;
    private panels: Panel[];

    constructor(
        private containerId: string,
        private clientBridge: ClientBridgeWrapperInterface
    ) {
        this.instanceId = DebugPanel.instanceCounter++;

        this.headerBar = new DebugHeaderBar("");
        this.footerBar = new DebugFooterBar();
        this.testingPanel = new TestPanel(this.containerId, this.instanceId);
        this.statePanel = new StatePanel(this.containerId, this.instanceId);
        this.routesPanel = new RoutesPanel(this.containerId, this.instanceId);
        this.historyPanel = new HistoryPanel(this.containerId, this.instanceId);
        this.logPanel = new LogPanel(this.containerId, this.instanceId);
        this.panels = [
            this.statePanel,
            this.routesPanel,
            this.historyPanel,
            this.testingPanel,
            this.logPanel,
        ];

        const container = this.getContainerElement();
        this.panelElement = this.createPanelStructure();
        container.appendChild(this.panelElement);
        this.contentElement = this.panelElement.querySelector(
            ".drafter-debug-content"
        );

        this.panels.forEach((p) => p.initialize());
        this.attachEventHandlers();
    }

    private reportError(message: string) {
        console.error("[DebugPanel] Error:", message);
        this.errors.push(message);
        return new DebugPanelError(message);
    }

    private getContainerElement(): HTMLElement {
        const container = document.getElementById(this.containerId);
        if (!container) {
            throw this.reportError(
                `DebugPanel: Container with id '${this.containerId}' not found.`
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
            "|"
        );
        const panelComponents = this.panels.map((panel) =>
            panel?.createStructure()
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
                {toggleFrame}
            </div>
        );
    }

    private toggleFrame(): void {
        const frames = document.querySelectorAll(
            ".drafter-padding-h--,.drafter-padding-v--,.drafter-header--,.drafter-footer--"
        );
        if (frames) {
            frames.forEach((frame) =>
                frame.classList.toggle("drafter-hidden--")
            );
        }
        const body = document.querySelector(".drafter-body--");
        if (body) {
            body.classList.toggle("drafter-body-frame-hidden--");
        }
    }

    private attachEventHandlers(): void {
        const NAVIGATION_BUTTONS = [
            [".drafter-home-button", "index"],
            [".drafter-reset-button", "--reset"],
            [".drafter-about-button", "--about"],
        ];
        NAVIGATION_BUTTONS.forEach(([selector, detail]) => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach((button) => {
                button.addEventListener("click", (event) => {
                    event.preventDefault();
                    window.dispatchEvent(
                        new CustomEvent("drafter-navigate", { detail })
                    );
                });
            });
        });
    }

    public handleEvent(event: TelemetryEvent): void {
        this.events.push(event);
        switch (event.data?.event_type) {
            case "RouteAdded":
                this.routesPanel?.renderRoute(
                    event.data.url,
                    event.data.signature
                );
                break;
            case "RequestEvent":
                this.historyPanel?.addRequest(event.data);
                break;
            case "RequestParseEvent":
                this.historyPanel?.addRequestParse(event.data);
                break;
            case "ResponseEvent":
                this.historyPanel?.addResponse(event.data);
                break;
            case "UpdatedState":
                this.statePanel?.renderState(event.data.representation);
                break;
            case "TestCaseEvent":
                this.testingPanel?.renderTest(event.data);
                this.testingPanel?.updateTestSummary();
                break;
        }
        this.logPanel?.renderEvent(event);
    }
}
