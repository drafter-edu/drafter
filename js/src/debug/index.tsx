import type { TelemetryEvent } from "./telemetry";
import { t } from "../i18n";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";

export class DebugPanel {
    private panelElement: HTMLElement | null = null;
    private contentElement: HTMLElement | null = null;
    private events: TelemetryEvent[] = [];
    private pageHistory: any[] = [];
    private currentState: any = null;
    private currentRoute: string = "";
    private errors: any[] = [];
    private warnings: any[] = [];
    private isVisible: boolean = true;
    private headerBar: DebugHeaderBar | null = null;
    private footerBar: DebugFooterBar | null = null;
    private historyIndex: number = -1;
    private isPlayingHistory: boolean = false;
    private playbackInterval: number | null = null;

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
                        id="drafter-debug-errors"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>❌ Errors</h4>
                        </div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-warnings"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>⚠️ Warnings</h4>
                        </div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-history"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>📜 Page Visit History</h4>
                        </div>
                        <div class="vcr-controls">
                            <button
                                id="vcr-first"
                                class="vcr-button"
                                title="Go to first visit"
                            >
                                ⏮
                            </button>
                            <button
                                id="vcr-prev"
                                class="vcr-button"
                                title="Previous visit"
                            >
                                ⏪
                            </button>
                            <button
                                id="vcr-play"
                                class="vcr-button"
                                title="Play/Pause"
                            >
                                ▶️
                            </button>
                            <button
                                id="vcr-next"
                                class="vcr-button"
                                title="Next visit"
                            >
                                ⏩
                            </button>
                            <button
                                id="vcr-last"
                                class="vcr-button"
                                title="Go to last visit"
                            >
                                ⏭
                            </button>
                            <span id="vcr-position" class="vcr-position">
                                0 / 0
                            </span>
                        </div>
                        <div id="drafter-history-list"></div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-current-route"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>🔗 Current Route</h4>
                        </div>
                    </div>
                    <div class="drafter-debug-section" id="drafter-debug-state">
                        <div class="drafter-debug-section-header">
                            <h4>📊 Current State</h4>
                        </div>
                        <div id="drafter-debug-current-state-content"></div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-routes"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>🗺️ Registered Routes</h4>
                        </div>
                        <div id="drafter-routes-list"></div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-tests"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>🧪 Test Status</h4>
                        </div>
                        <div id="drafter-test-summary"></div>
                        <div id="drafter-test-cases"></div>
                    </div>
                    <div
                        class="drafter-debug-section"
                        id="drafter-debug-events"
                    >
                        <div class="drafter-debug-section-header">
                            <h4>ℹ️ Info Messages</h4>
                        </div>
                    </div>
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
        
        const resetButtons = document.querySelectorAll(".drafter-reset-button");
        resetButtons.forEach((button) => {
            button.addEventListener("click", (event) => {
                event.preventDefault();
                // Reset state by reloading the page
                window.location.reload();
            });
        });
        
        // VCR control event handlers
        const vcrFirst = document.getElementById("vcr-first");
        const vcrPrev = document.getElementById("vcr-prev");
        const vcrPlay = document.getElementById("vcr-play");
        const vcrNext = document.getElementById("vcr-next");
        const vcrLast = document.getElementById("vcr-last");
        
        if (vcrFirst) {
            vcrFirst.addEventListener("click", () => this.vcrGoToFirst());
        }
        if (vcrPrev) {
            vcrPrev.addEventListener("click", () => this.vcrStepBackward());
        }
        if (vcrPlay) {
            vcrPlay.addEventListener("click", () => this.vcrTogglePlayback());
        }
        if (vcrNext) {
            vcrNext.addEventListener("click", () => this.vcrStepForward());
        }
        if (vcrLast) {
            vcrLast.addEventListener("click", () => this.vcrGoToLast());
        }
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
                <div class="state-actions">
                    <button
                        class="state-action-btn"
                        onClick={() => this.saveStateToLocalStorage()}
                    >
                        💾 Save to LocalStorage
                    </button>
                    <button
                        class="state-action-btn"
                        onClick={() => this.loadStateFromLocalStorage()}
                    >
                        📂 Load from LocalStorage
                    </button>
                    <button
                        class="state-action-btn"
                        onClick={() => this.downloadState()}
                    >
                        ⬇️ Download JSON
                    </button>
                </div>
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

    public handleEvent(event: TelemetryEvent): void {
        this.events.push(event);
        
        if (!event.data) {
            console.warn(
                `DebugPanel: Event without data: '${event.event_type}'`
            );
            return;
        }
        
        switch (event.data.event_type) {
            case "RouteAdded":
                this.renderRoute(event.data.url, event.data.signature);
                break;
            case "UpdatedState":
                this.currentState = event.data.html;
                this.renderState(this.currentState);
                break;
            case "DrafterError":
                this.renderError(event.data);
                break;
            case "DrafterWarning":
                this.renderWarning(event.data);
                break;
            case "DrafterInfo":
                this.renderInfo(event.data);
                break;
            case "PageVisitEvent":
                this.currentRoute = event.data.url;
                this.renderCurrentRoute(this.currentRoute);
                this.renderPageVisit(event.data);
                break;
            case "RequestEvent":
                // Handled as part of PageVisitEvent
                this.currentRoute = event.data.url;
                this.renderCurrentRoute(this.currentRoute);
                break;
            case "ResponseEvent":
                // Handled as part of PageVisitEvent
                break;
            case "TestCaseEvent":
                this.renderTestCase(event.data);
                break;
            case "TestSummaryEvent":
                this.renderTestSummary(event.data);
                break;
            default:
                console.warn(
                    `DebugPanel: Unhandled event type '${event.data.event_type}'`
                );
                break;
        }
    }


    private renderError(error: any): void {
        const section = document.getElementById("drafter-debug-errors");
        if (!section) {
            return;
        }
        
        const errorElement = (
            <div class="debug-message error-message">
                <div class="message-header">{error.message}</div>
                <div class="message-where">at {error.where}</div>
                <div class="message-details">{error.details}</div>
                {error.traceback && (
                    <details>
                        <summary>Traceback</summary>
                        <pre>{error.traceback}</pre>
                    </details>
                )}
            </div>
        );
        
        section.appendChild(errorElement);
    }

    private renderWarning(warning: any): void {
        const section = document.getElementById("drafter-debug-warnings");
        if (!section) {
            return;
        }
        
        const warningElement = (
            <div class="debug-message warning-message">
                <div class="message-header">{warning.message}</div>
                <div class="message-where">at {warning.where}</div>
                <div class="message-details">{warning.details}</div>
            </div>
        );
        
        section.appendChild(warningElement);
    }

    private renderInfo(info: any): void {
        const section = document.getElementById("drafter-debug-events");
        if (!section) {
            return;
        }
        
        const infoElement = (
            <div class="debug-message info-message">
                <div class="message-header">{info.message}</div>
                <div class="message-where">at {info.where}</div>
            </div>
        );
        
        section.appendChild(infoElement);
    }

    private renderPageVisit(visit: any): void {
        // Store the visit in history
        this.pageHistory.push(visit);
        
        // If not in playback mode, show the latest visit
        if (!this.isPlayingHistory && this.historyIndex === -1) {
            this.historyIndex = this.pageHistory.length - 1;
        }
        
        // Re-render the history list
        this.renderHistoryList();
        this.updateVcrControls();
    }
    
    private renderHistoryList(): void {
        const section = document.getElementById("drafter-history-list");
        if (!section) {
            return;
        }
        
        // Clear existing content
        section.innerHTML = "";
        
        // Render all visits with highlighting for current position
        this.pageHistory.forEach((visit, index) => {
            const isCurrentVisit = index === this.historyIndex;
            const visitElement = (
                <div class={`visit-item ${isCurrentVisit ? "visit-current" : ""}`}>
                    <div class="visit-header">
                        <span class="visit-number">#{index + 1}</span>
                        <span class="visit-url">{visit.url}</span>
                        <span class="visit-function">{visit.function_name}</span>
                        <span class="visit-duration">{visit.duration_ms.toFixed(1)}ms</span>
                        <span class={`visit-status ${visit.status_code < 400 ? "status-ok" : "status-error"}`}>
                            {visit.status_code}
                        </span>
                    </div>
                    <details>
                        <summary>Details</summary>
                        <div class="visit-details">
                            <p><strong>Arguments:</strong> {visit.arguments}</p>
                            <p><strong>Timestamp:</strong> {visit.timestamp}</p>
                            {visit.button_pressed && (
                                <p><strong>Button:</strong> {visit.button_pressed}</p>
                            )}
                        </div>
                    </details>
                </div>
            );
            
            section.appendChild(visitElement);
        });
        
        // Scroll current visit into view
        if (this.historyIndex >= 0 && this.historyIndex < this.pageHistory.length) {
            const currentVisit = section.children[this.historyIndex] as HTMLElement;
            if (currentVisit) {
                currentVisit.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
        }
    }

    private renderCurrentRoute(route: string): void {
        const section = document.getElementById("drafter-debug-current-route");
        if (!section) {
            return;
        }
        
        // Find the section header or create one
        let content = section.querySelector(".current-route-content");
        if (!content) {
            content = document.createElement("div");
            content.className = "current-route-content";
            section.appendChild(content);
        }
        
        content.textContent = route ? `Currently viewing: ${route}` : "No route visited yet";
    }

    private saveStateToLocalStorage(): void {
        if (this.currentState) {
            try {
                localStorage.setItem("drafter-debug-state", this.currentState);
                alert("State saved to LocalStorage");
            } catch (e) {
                console.error("Failed to save state to LocalStorage:", e);
                alert("Failed to save state: " + e);
            }
        }
    }

    private loadStateFromLocalStorage(): void {
        try {
            const savedState = localStorage.getItem("drafter-debug-state");
            if (savedState) {
                this.currentState = savedState;
                this.renderState(this.currentState);
                alert("State loaded from LocalStorage");
            } else {
                alert("No saved state found in LocalStorage");
            }
        } catch (e) {
            console.error("Failed to load state from LocalStorage:", e);
            alert("Failed to load state: " + e);
        }
    }

    private downloadState(): void {
        if (this.currentState) {
            try {
                const blob = new Blob([this.currentState], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `drafter-state-${new Date().toISOString()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (e) {
                console.error("Failed to download state:", e);
                alert("Failed to download state: " + e);
            }
        }
    }

    private renderTestSummary(summary: any): void {
        const section = document.getElementById("drafter-test-summary");
        if (!section) {
            return;
        }

        const summaryElement = (
            <div class="test-summary">
                <div class="test-summary-stats">
                    <span class="test-total">Total: {summary.total}</span>
                    <span class="test-passed">✅ Passed: {summary.passed}</span>
                    <span class="test-failed">❌ Failed: {summary.failed}</span>
                </div>
            </div>
        );

        section.replaceChildren(summaryElement);
    }

    private renderTestCase(testCase: any): void {
        const section = document.getElementById("drafter-test-cases");
        if (!section) {
            return;
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
                        <div dangerouslySetInnerHTML={{ __html: testCase.diff_html }}></div>
                    </details>
                )}
            </div>
        );

        section.appendChild(testElement);
    }
    
    // VCR Playback Control Methods
    
    private updateVcrControls(): void {
        const position = document.getElementById("vcr-position");
        if (position) {
            const current = this.historyIndex + 1;
            const total = this.pageHistory.length;
            position.textContent = `${current} / ${total}`;
        }
        
        // Update play button icon
        const playButton = document.getElementById("vcr-play");
        if (playButton) {
            playButton.textContent = this.isPlayingHistory ? "⏸️" : "▶️";
            playButton.title = this.isPlayingHistory ? "Pause" : "Play";
        }
        
        // Enable/disable buttons based on position
        const firstButton = document.getElementById("vcr-first") as HTMLButtonElement;
        const prevButton = document.getElementById("vcr-prev") as HTMLButtonElement;
        const nextButton = document.getElementById("vcr-next") as HTMLButtonElement;
        const lastButton = document.getElementById("vcr-last") as HTMLButtonElement;
        
        if (firstButton) firstButton.disabled = this.historyIndex <= 0;
        if (prevButton) prevButton.disabled = this.historyIndex <= 0;
        if (nextButton) nextButton.disabled = this.historyIndex >= this.pageHistory.length - 1;
        if (lastButton) lastButton.disabled = this.historyIndex >= this.pageHistory.length - 1;
    }
    
    private vcrGoToFirst(): void {
        if (this.pageHistory.length > 0) {
            this.historyIndex = 0;
            this.renderHistoryList();
            this.updateVcrControls();
        }
    }
    
    private vcrStepBackward(): void {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.renderHistoryList();
            this.updateVcrControls();
        }
    }
    
    private vcrStepForward(): void {
        if (this.historyIndex < this.pageHistory.length - 1) {
            this.historyIndex++;
            this.renderHistoryList();
            this.updateVcrControls();
        }
    }
    
    private vcrGoToLast(): void {
        if (this.pageHistory.length > 0) {
            this.historyIndex = this.pageHistory.length - 1;
            this.renderHistoryList();
            this.updateVcrControls();
        }
    }
    
    private vcrTogglePlayback(): void {
        this.isPlayingHistory = !this.isPlayingHistory;
        
        if (this.isPlayingHistory) {
            // Start playback
            this.playbackInterval = window.setInterval(() => {
                if (this.historyIndex < this.pageHistory.length - 1) {
                    this.vcrStepForward();
                } else {
                    // Reached the end, stop playback
                    this.vcrStopPlayback();
                }
            }, 2000); // Play one step every 2 seconds
        } else {
            // Stop playback
            this.vcrStopPlayback();
        }
        
        this.updateVcrControls();
    }
    
    private vcrStopPlayback(): void {
        if (this.playbackInterval !== null) {
            window.clearInterval(this.playbackInterval);
            this.playbackInterval = null;
        }
        this.isPlayingHistory = false;
        this.updateVcrControls();
    }
}
