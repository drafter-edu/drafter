import type { ReactElement } from "jsx-dom";

/**
 * Base class for all debug panels. Provides common structure and utilities.
 */
export abstract class Panel {
    protected static DEBUG_PANEL_CLASS = "drafter-debug-section";
    protected static DEBUG_PANEL_HEADER_CLASS = "drafter-debug-section-header";

    protected readonly container: HTMLElement;

    protected constructor(
        protected readonly containerId: string,
        protected readonly instanceId: number,
        protected readonly panelName: string,
        protected readonly panelTitle: string
    ) {
        this.container = this.requireElementById(
            containerId,
            `DebugPanel: Container with id '${containerId}' not found.`
        );
    }

    /**
     * Get the initial content for this panel
     */
    protected abstract get initialContent(): ReactElement;

    protected getPanelElement(): HTMLElement {
        return this.requireElementById(
            this.getPanelDomId(),
            `DebugPanel: Panel '${this.panelName}' not found.`
        );
    }

    public initialize(): void {}

    protected getContentElement(): HTMLElement {
        return this.requireElementById(
            this.getContentDomId(),
            `DebugPanel: ${this.panelName} content not found.`
        );
    }

    protected scopedSelector(baseClass: string): string {
        return `.${baseClass}-${this.instanceId}`;
    }

    protected queryWithin(selector: string, errorMessage: string): HTMLElement {
        const element = this.container.querySelector(
            selector
        ) as HTMLElement | null;
        if (!element) {
            throw new Error(errorMessage);
        }
        return element;
    }

    protected getPanelDomId(): string {
        return `${this.panelName}-${this.instanceId}`;
    }

    protected getContentDomId(): string {
        return `${this.panelName}-content-${this.instanceId}`;
    }

    protected getContentClass(): string {
        return `${this.panelName}-content`;
    }

    protected getContentInstanceClass(): string {
        return `${this.panelName}-content-${this.instanceId}`;
    }

    private requireElementById(id: string, errorMessage: string): HTMLElement {
        const element = document.getElementById(id);
        if (!element) {
            throw new Error(errorMessage);
        }
        return element;
    }

    /**
     * Create the panel structure with header and content area
     */
    public createStructure(): ReactElement {
        return (
            <div
                class={`${Panel.DEBUG_PANEL_CLASS} ${this.panelName}`}
                id={this.getPanelDomId()}
            >
                <div class={Panel.DEBUG_PANEL_HEADER_CLASS}>
                    <h4>{this.panelTitle}</h4>
                </div>
                <div
                    class={`${this.getContentClass()} ${this.getContentInstanceClass()}`}
                    id={this.getContentDomId()}
                >
                    {this.initialContent}
                </div>
            </div>
        );
    }

    public getAnchor(): ReactElement {
        return <a href={`#${this.getPanelDomId()}`}>{this.panelTitle}</a>;
    }
}
