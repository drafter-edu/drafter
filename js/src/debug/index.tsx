import type { TelemetryEvent } from "./telemetry";
import { t } from "../i18n";
import { DebugHeaderBar } from "./header";
import { DebugFooterBar } from "./footer";

export class DebugPanel {
    private panelElement: HTMLElement | null = null;
    private contentElement: HTMLElement | null = null;
    private events: TelemetryEvent[] = [];
    private routes: Map<string, any> = new Map();
    private pageHistory: any[] = [];
    private currentState: any = null;
    private errors: any[] = [];
    private warnings: any[] = [];
    private isVisible: boolean = true;
    private headerBar: DebugHeaderBar | null = null;
    private footerBar: DebugFooterBar | null = null;

    constructor(private containerId: string) {
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
        this.attachEventHandlers();
        this.headerBar = new DebugHeaderBar("");
        this.footerBar = new DebugFooterBar();
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

        const ui = <div></div>;

        panel.innerHTML = `
            <div class="drafter-debug-header">
                <h3>🔍 Debug Monitor</h3>
                <div class="drafter-debug-actions">
                    <button id="debug-reset-btn" title="Reset state and return to index">🔄 Reset</button>
                    <button id="debug-about-btn" title="Go to About page">ℹ️ About</button>
                    <button id="debug-save-state-btn" title="Save state to localStorage">💾 Save State</button>
                    <button id="debug-load-state-btn" title="Load state from localStorage">📂 Load State</button>
                    <button id="debug-download-state-btn" title="Download state as JSON">⬇️ Download</button>
                    <button id="debug-upload-state-btn" title="Upload state from JSON">⬆️ Upload</button>
                    <button id="debug-toggle-btn" title="Toggle debug panel">👁️</button>
                </div>
            </div>
            <div class="drafter-debug-content">
                <div class="debug-section" id="debug-errors"></div>
                <div class="debug-section" id="debug-warnings"></div>
                <div class="debug-section" id="debug-current-route"></div>
                <div class="debug-section" id="debug-state"></div>
                <div class="debug-section" id="debug-history"></div>
                <div class="debug-section" id="debug-routes"></div>
                <div class="debug-section" id="debug-events"></div>
            </div>
        `;

        return panel;
    }

    private attachEventHandlers(): void {
        // const toggleBtn = document.getElementById("debug-toggle-btn");
        // if (toggleBtn) {
        //     toggleBtn.addEventListener("click", () => this.toggleVisibility());
        // }
        // const resetBtn = document.getElementById("debug-reset-btn");
        // if (resetBtn) {
        //     resetBtn.addEventListener("click", () => this.resetState());
        // }
        // const aboutBtn = document.getElementById("debug-about-btn");
        // if (aboutBtn) {
        //     aboutBtn.addEventListener("click", () => this.navigateToAbout());
        // }
        // const saveBtn = document.getElementById("debug-save-state-btn");
        // if (saveBtn) {
        //     saveBtn.addEventListener("click", () =>
        //         this.saveStateToLocalStorage()
        //     );
        // }
        // const loadBtn = document.getElementById("debug-load-state-btn");
        // if (loadBtn) {
        //     loadBtn.addEventListener("click", () =>
        //         this.loadStateFromLocalStorage()
        //     );
        // }
        // const downloadBtn = document.getElementById("debug-download-state-btn");
        // if (downloadBtn) {
        //     downloadBtn.addEventListener("click", () => this.downloadState());
        // }
        // const uploadBtn = document.getElementById("debug-upload-state-btn");
        // if (uploadBtn) {
        //     uploadBtn.addEventListener("click", () => this.uploadState());
        // }
    }
}
