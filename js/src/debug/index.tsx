import type { TelemetryEvent } from "./telemetry";
import { t } from "../i18n";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { TestCaseEvent } from "./telemetry/tests";

export class DebugPanel {
    private panelElement: HTMLElement | null = null;
    private contentElement: HTMLElement | null = null;
    private events: TelemetryEvent[] = [];
    private pageHistory: any[] = [];
    private currentState: any = null;
    private errors: any[] = [];
    private warnings: any[] = [];
    private isVisible: boolean = true;
    private headerBar: DebugHeaderBar | null = null;
    private footerBar: DebugFooterBar | null = null;
    private tests: TestCaseEvent[] = [];

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
                        <a href="#drafter-debug-warnings">Warnings</a> |
                        <a href="#drafter-debug-errors">Errors</a> |
                        <a href="#drafter-debug-current-route">Current Route</a>{" "}
                        |<a href="#drafter-debug-state">State</a> |
                        <a href="#drafter-debug-history">History</a> |
                        <a href="#drafter-debug-routes">Routes</a> |
                        <a href="#drafter-debug-events">Events</a>
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
                    ></div>
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

    private renderState(newState: any): void {
        const section = document.getElementById(
            "drafter-debug-current-state-content"
        );
        if (!section) {
            throw new Error("DebugPanel: State section not found.");
        }

        const stateContent = (
            <div class="state-content">
                <div dangerouslySetInnerHTML={{ __html: newState }}></div>
            </div>
        );

        section.replaceChildren(stateContent);
    }

    private renderRoute(route: string, signature: string): void {
        const section = document.getElementById("drafter-routes-list");
        if (!section) {
            throw new Error("DebugPanel: Routes section not found.");
        }

        const newRouteItem = (
            <div class="route-signature">
                <strong>{route}</strong>:<pre>{signature}</pre>
            </div>
        );

        section.appendChild(newRouteItem);
    }

    private renderTest(testCase: TestCaseEvent): void {
        const testList = document.getElementById(
            "drafter-debug-current-tests-content-list"
        );
        if (!testList) {
            throw new Error("DebugPanel: Tests section not found.");
        }

        const statusIcon = testCase.passed ? "✅" : "❌";
        const statusClass = testCase.passed ? "test-passed" : "test-failed";

        const testElement = (
            <div class={`test-case ${statusClass}`}>
                <div class="test-case-header">
                    <span class="test-status">{statusIcon}</span>
                    <span class="test-line">Line {testCase.line}</span>
                    <code class="test-caller">{testCase.caller}</code>
                </div>
                {!testCase.passed && testCase.diff_html && (
                    <details class="test-diff">
                        <summary>Show Difference</summary>
                        <div
                            dangerouslySetInnerHTML={{
                                __html: testCase.diff_html,
                            }}
                        ></div>
                    </details>
                )}
            </div>
        );

        testList.appendChild(testElement);
    }

    private updateTestSummary(): void {
        const summaryElement = document.getElementById(
            "drafter-debug-current-tests-summary"
        );
        if (!summaryElement) {
            throw new Error("DebugPanel: Test summary section not found.");
        }

        const totalTests = this.tests.length;
        const passedTests = this.tests.filter((t) => t.passed).length;
        const failedTests = totalTests - passedTests;

        summaryElement.replaceChildren(
            <div class="test-summary">
                <strong>Summary:</strong>
                <div>Total Tests: {totalTests}</div>
                <div>✅ Passed: {passedTests}</div>
                <div>❌ Failed: {failedTests}</div>
            </div>
        );
    }

    public handleEvent(event: TelemetryEvent): void {
        this.events.push(event);
        switch (event.data?.event_type) {
            case "RouteAdded":
                this.renderRoute(event.data.url, event.data.signature);
                break;
            case "UpdatedState":
                this.currentState = event.data.html;
                this.renderState(this.currentState);
                break;
            case "TestCaseEvent":
                this.tests.push(event.data);
                this.renderTest(event.data);
                this.updateTestSummary();
                break;
            default:
                // console.warn(
                //     `DebugPanel: Unhandled event type '${event.event_type}'`
                // );
                break;
        }
    }
}
