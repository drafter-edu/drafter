import type { TelemetryEvent } from "./telemetry";
import { t } from "../i18n";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { TestCaseEvent } from "./telemetry/tests";
import { decodeHtmlEntities } from "./utils";
import { TestPanel } from "./panels/testing";
import { StatePanel } from "./panels/state";
import { RoutesPanel } from "./panels/routes";
import { HistoryPanel } from "./panels/history";

export class DebugPanel {
    private panelElement: HTMLElement | null = null;
    private contentElement: HTMLElement | null = null;
    private events: TelemetryEvent[] = [];
    private pageHistory: any[] = [];
    private errors: any[] = [];
    private warnings: any[] = [];
    private isVisible: boolean = true;
    private headerBar: DebugHeaderBar | null = null;
    private footerBar: DebugFooterBar | null = null;
    private testingPanel: TestPanel | null = null;
    private statePanel: StatePanel | null = null;
    private routesPanel: RoutesPanel | null = null;
    private historyPanel: HistoryPanel | null = null;

    constructor(
        private containerId: string,
        private clientBridge: ClientBridgeWrapperInterface
    ) {
        this.initialize();
    }

    private initialize() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(
                `DebugPanel: Container with id '${this.containerId}' not found.`
            );
            return;
        }

        this.panelElement = this.createPanelStructure();
        container.appendChild(this.panelElement);
        this.contentElement = this.panelElement.querySelector(
            ".drafter-debug-content"
        );
        this.headerBar = new DebugHeaderBar("");
        this.footerBar = new DebugFooterBar();
        this.testingPanel = new TestPanel();
        this.statePanel = new StatePanel();
        this.routesPanel = new RoutesPanel();
        this.historyPanel = new HistoryPanel();
        this.attachEventHandlers();
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
        panel.id = "drafter-debug-panel";

        const ui = (
            <div class="drafter-debug-panel">
                <div class="drafter-debug-header-left">
                    <div>
                        <div class="drafter-debug-header-title">
                            Debug Panel
                        </div>
                        <div class="drafter-debug-header-subtitle"></div>
                    </div>
                    <div class="drafter-debug-header-buttons">
                        <a href="#drafter-debug-console">Console</a> |
                        <a href="#drafter-debug-current-route">Routes</a> |
                        <a href="#drafter-debug-state">State</a> |
                        <a href="#drafter-debug-history">History</a> |
                        <a href="#drafter-debug-routes">Routes</a>
                    </div>
                </div>
                {this.createActionButtons()}
                <div class="drafter-debug-content">
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-routes"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>Registered Routes</h4>
                        </div>
                        <div id="drafter-routes-list"></div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-current-route"
                    ></div>
                    <div class="drafter-debug-section" id="drafter-debug-state">
                        <div class="drafter-debug-section-header">
                            <h4>Current State</h4>
                        </div>
                        <div id="drafter-debug-current-state-content"></div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-history"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>Page History</h4>
                        </div>
                        <div id="drafter-debug-page-history-content"></div>
                    </div>
                    <div class="drafter-debug-section" id="drafter-debug-tests">
                        <div class="drafter-debug-section-header">
                            <h4>Your Tests</h4>
                        </div>
                        <div id="drafter-debug-current-tests-content">
                            <div id="drafter-debug-current-tests-summary"></div>
                            <br></br>
                            <strong>Details: </strong>
                            <div id="drafter-debug-current-tests-content-list"></div>
                        </div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-errors"
                    ></div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-events"
                    ></div>
                </div>
            </div>
        );
        panel.appendChild(ui);

        return panel;
    }

    private createActionButtons() {
        return (
            <div class="drafter-debug-actions">
                <button
                    id="drafter-home-btn"
                    title={t("button.home.tooltip")}
                    class="drafter-home-button"
                >
                    {t("icon.home")} {t("button.home")}
                </button>
                <button
                    id="debug-reset-btn"
                    title={t("button.reset.tooltip")}
                    class="drafter-reset-button"
                >
                    {t("icon.reset")} {t("button.reset")}
                </button>
            </div>
        );
    }

    private attachEventHandlers(): void {
        const homeButtons = document.querySelectorAll(".drafter-home-button");
        homeButtons.forEach((button) => {
            button.addEventListener("click", (event) => {
                event.preventDefault();
                this.clientBridge.goto("index");
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
                this.statePanel?.renderState(event.data.html);
                break;
            case "TestCaseEvent":
                this.testingPanel?.renderTest(event.data);
                this.testingPanel?.updateTestSummary();
                break;
            default:
                // console.warn(
                //     `DebugPanel: Unhandled event type '${event.event_type}'`
                // );
                break;
        }
    }
}
