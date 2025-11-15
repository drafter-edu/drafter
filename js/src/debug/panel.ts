/**
 * Debug Panel for displaying telemetry events from the Monitor.
 * 
 * This module handles rendering debug information dynamically based on
 * telemetry events emitted from the backend Monitor system.
 */

export interface TelemetryEvent {
    event_type: string;
    correlation: {
        causation_id?: number;
        route?: string;
        request_id?: number;
        response_id?: number;
        outcome_id?: number;
        dom_id?: string;
    };
    source: string;
    id: number;
    version: string;
    level?: string;
    timestamp: string;
    data?: any;
}

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

    constructor(private containerId: string) {
        this.initialize();
    }

    private initialize(): void {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.warn(`Debug panel container ${this.containerId} not found`);
            return;
        }

        this.panelElement = this.createPanelStructure();
        container.appendChild(this.panelElement);
        this.contentElement = this.panelElement.querySelector('.drafter-debug-content');
        this.attachEventHandlers();
    }

    private createPanelStructure(): HTMLElement {
        const panel = document.createElement('div');
        panel.className = 'drafter-debug-panel';
        panel.id = 'drafter-debug-panel';
        
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
        const toggleBtn = document.getElementById('debug-toggle-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleVisibility());
        }

        const resetBtn = document.getElementById('debug-reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetState());
        }

        const aboutBtn = document.getElementById('debug-about-btn');
        if (aboutBtn) {
            aboutBtn.addEventListener('click', () => this.navigateToAbout());
        }

        const saveBtn = document.getElementById('debug-save-state-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveStateToLocalStorage());
        }

        const loadBtn = document.getElementById('debug-load-state-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadStateFromLocalStorage());
        }

        const downloadBtn = document.getElementById('debug-download-state-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadState());
        }

        const uploadBtn = document.getElementById('debug-upload-state-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.uploadState());
        }
    }

    public handleTelemetryEvent(event: TelemetryEvent): void {
        this.events.push(event);

        // Route different event types to appropriate handlers
        switch (true) {
            case event.event_type.startsWith('route.'):
                this.handleRouteEvent(event);
                break;
            case event.event_type.startsWith('request.'):
                this.handleRequestEvent(event);
                break;
            case event.event_type.startsWith('response.'):
                this.handleResponseEvent(event);
                break;
            case event.event_type.startsWith('outcome.'):
                this.handleOutcomeEvent(event);
                break;
            case event.event_type.startsWith('state.'):
                this.handleStateEvent(event);
                break;
            case event.event_type.startsWith('logger.error'):
                this.handleErrorEvent(event);
                break;
            case event.event_type.startsWith('logger.warning'):
                this.handleWarningEvent(event);
                break;
            default:
                // Generic event handling
                this.updateEventsSection();
        }

        this.render();
    }

    private handleRouteEvent(event: TelemetryEvent): void {
        if (event.event_type === 'route.added') {
            this.routes.set(event.data?.path || 'unknown', event.data);
        }
    }

    private handleRequestEvent(event: TelemetryEvent): void {
        if (event.event_type === 'request.visit') {
            // Update current route information
            this.updateCurrentRouteSection(event.data);
        }
    }

    private handleResponseEvent(event: TelemetryEvent): void {
        // Track response data for history
        if (event.data) {
            this.pageHistory.push({
                type: 'response',
                timestamp: event.timestamp,
                data: event.data
            });
        }
    }

    private handleOutcomeEvent(event: TelemetryEvent): void {
        // Track outcome data
        if (event.data) {
            this.pageHistory.push({
                type: 'outcome',
                timestamp: event.timestamp,
                data: event.data
            });
        }
    }

    private handleStateEvent(event: TelemetryEvent): void {
        if (event.event_type === 'state.updated') {
            this.currentState = event.data;
        }
    }

    private handleErrorEvent(event: TelemetryEvent): void {
        this.errors.push(event);
    }

    private handleWarningEvent(event: TelemetryEvent): void {
        this.warnings.push(event);
    }

    private render(): void {
        if (!this.contentElement) return;

        this.renderErrors();
        this.renderWarnings();
        this.renderCurrentRoute();
        this.renderState();
        this.renderHistory();
        this.renderRoutes();
        this.renderEvents();
    }

    private renderErrors(): void {
        const section = document.getElementById('debug-errors');
        if (!section) return;

        if (this.errors.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        section.innerHTML = `
            <h4>❌ Errors (${this.errors.length})</h4>
            <div class="debug-messages">
                ${this.errors.slice(-10).map(err => `
                    <div class="debug-message error-message">
                        <div class="message-header">${this.escapeHtml(err.data?.message || 'Unknown error')}</div>
                        <div class="message-meta">
                            <span class="message-source">${this.escapeHtml(err.source)}</span>
                            <span class="message-time">${new Date(err.timestamp).toLocaleTimeString()}</span>
                        </div>
                        ${err.data?.details ? `
                            <details>
                                <summary>Details</summary>
                                <pre>${this.escapeHtml(err.data.details)}</pre>
                            </details>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    private renderWarnings(): void {
        const section = document.getElementById('debug-warnings');
        if (!section) return;

        if (this.warnings.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        section.innerHTML = `
            <h4>⚠️ Warnings (${this.warnings.length})</h4>
            <div class="debug-messages">
                ${this.warnings.slice(-10).map(warn => `
                    <div class="debug-message warning-message">
                        <div class="message-header">${this.escapeHtml(warn.data?.message || 'Unknown warning')}</div>
                        <div class="message-meta">
                            <span class="message-source">${this.escapeHtml(warn.source)}</span>
                            <span class="message-time">${new Date(warn.timestamp).toLocaleTimeString()}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    private renderCurrentRoute(): void {
        const section = document.getElementById('debug-current-route');
        if (!section) return;

        section.innerHTML = `
            <details open>
                <summary><h4>🗺️ Current Route</h4></summary>
                <div class="route-info">
                    <p><strong>Route:</strong> ${this.escapeHtml(String(this.events.find(e => e.event_type === 'request.visit')?.correlation.route || 'None'))}</p>
                </div>
            </details>
        `;
    }

    private renderState(): void {
        const section = document.getElementById('debug-state');
        if (!section) return;

        section.innerHTML = `
            <details open>
                <summary><h4>📊 Current State</h4></summary>
                <div class="state-content">
                    <pre>${this.escapeHtml(JSON.stringify(this.currentState, null, 2) || 'null')}</pre>
                </div>
            </details>
        `;
    }

    private renderHistory(): void {
        const section = document.getElementById('debug-history');
        if (!section) return;

        section.innerHTML = `
            <details open>
                <summary><h4>📜 Page History (${this.pageHistory.length})</h4></summary>
                <div class="history-content">
                    ${this.pageHistory.length === 0 ? '<p>No history yet</p>' : `
                        <ul class="history-list">
                            ${this.pageHistory.slice(-20).reverse().map((item, idx) => `
                                <li class="history-item">
                                    <span class="history-index">#${this.pageHistory.length - idx}</span>
                                    <span class="history-type">${item.type}</span>
                                    <span class="history-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
                                </li>
                            `).join('')}
                        </ul>
                    `}
                </div>
            </details>
        `;
    }

    private renderRoutes(): void {
        const section = document.getElementById('debug-routes');
        if (!section) return;

        const routesList = Array.from(this.routes.entries());
        section.innerHTML = `
            <details>
                <summary><h4>🛣️ Available Routes (${routesList.length})</h4></summary>
                <div class="routes-content">
                    ${routesList.length === 0 ? '<p>No routes registered</p>' : `
                        <ul class="routes-list">
                            ${routesList.map(([path, data]) => `
                                <li class="route-item">
                                    <code>${this.escapeHtml(path)}</code>
                                    ${data?.function_name ? ` → <code>${this.escapeHtml(data.function_name)}</code>` : ''}
                                </li>
                            `).join('')}
                        </ul>
                    `}
                </div>
            </details>
        `;
    }

    private renderEvents(): void {
        const section = document.getElementById('debug-events');
        if (!section) return;

        section.innerHTML = `
            <details>
                <summary><h4>📋 Recent Events (${this.events.length})</h4></summary>
                <div class="events-content">
                    <ul class="events-list">
                        ${this.events.slice(-50).reverse().map((event, idx) => `
                            <li class="event-item">
                                <span class="event-index">#${this.events.length - idx}</span>
                                <span class="event-type">${this.escapeHtml(event.event_type)}</span>
                                <span class="event-source">${this.escapeHtml(event.source)}</span>
                                <span class="event-time">${new Date(event.timestamp).toLocaleTimeString()}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </details>
        `;
    }

    private updateEventsSection(): void {
        // Called for generic events
    }

    private updateCurrentRouteSection(data: any): void {
        // Called when route changes
    }

    private toggleVisibility(): void {
        this.isVisible = !this.isVisible;
        if (this.contentElement) {
            this.contentElement.style.display = this.isVisible ? 'block' : 'none';
        }
    }

    private resetState(): void {
        console.log('[Debug Panel] Reset state requested');
        // Trigger navigation to index with reset
        window.location.href = window.location.pathname;
    }

    private navigateToAbout(): void {
        console.log('[Debug Panel] Navigate to About');
        // Navigate to about page - would need to trigger route change
    }

    private saveStateToLocalStorage(): void {
        try {
            localStorage.setItem('drafter-debug-state', JSON.stringify(this.currentState));
            console.log('[Debug Panel] State saved to localStorage');
        } catch (e) {
            console.error('[Debug Panel] Failed to save state:', e);
        }
    }

    private loadStateFromLocalStorage(): void {
        try {
            const saved = localStorage.getItem('drafter-debug-state');
            if (saved) {
                this.currentState = JSON.parse(saved);
                this.render();
                console.log('[Debug Panel] State loaded from localStorage');
            }
        } catch (e) {
            console.error('[Debug Panel] Failed to load state:', e);
        }
    }

    private downloadState(): void {
        try {
            const dataStr = JSON.stringify(this.currentState, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
            const exportFileDefaultName = `drafter-state-${Date.now()}.json`;

            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
        } catch (e) {
            console.error('[Debug Panel] Failed to download state:', e);
        }
    }

    private uploadState(): void {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e: Event) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        const content = event.target?.result as string;
                        this.currentState = JSON.parse(content);
                        this.render();
                        console.log('[Debug Panel] State loaded from file');
                    } catch (err) {
                        console.error('[Debug Panel] Failed to parse state file:', err);
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }

    private escapeHtml(text: string): string {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export a factory function to create and initialize the debug panel
export function initializeDebugPanel(containerId: string = 'drafter-debug--'): DebugPanel {
    return new DebugPanel(containerId);
}
