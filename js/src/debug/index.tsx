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
    private errors: any[] = [];
    private warnings: any[] = [];
    private isVisible: boolean = true;
    private headerBar: DebugHeaderBar | null = null;
    private footerBar: DebugFooterBar | null = null;

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
                this.renderPageVisit(event.data);
                break;
            case "RequestEvent":
                // Handled as part of PageVisitEvent
                break;
            case "ResponseEvent":
                // Handled as part of PageVisitEvent
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
        const section = document.getElementById("drafter-debug-history");
        if (!section) {
            return;
        }
        
        const visitElement = (
            <div class="visit-item">
                <div class="visit-header">
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
        
        // Insert at the beginning so newest is on top
        if (section.firstChild) {
            section.insertBefore(visitElement, section.firstChild);
        } else {
            section.appendChild(visitElement);
        }
    }
}
