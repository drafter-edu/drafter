import type { DrafterError, DrafterWarning, DrafterInfo } from "../telemetry/errors";

export class ErrorsPanel {
    private contentElement: HTMLElement;
    private listElement: HTMLElement;
    private errors: DrafterError[] = [];
    private warnings: DrafterWarning[] = [];
    private infos: DrafterInfo[] = [];

    constructor() {
        const content = document.getElementById("drafter-debug-errors-content");

        if (!content) {
            throw new Error("DebugPanel: Errors section not found.");
        }

        this.contentElement = content;

        const initialContent = (
            <div>
                <div id="drafter-debug-errors-list"></div>
            </div>
        );
        content.appendChild(initialContent);
        this.listElement = document.getElementById("drafter-debug-errors-list")!;
    }

    public addError(error: DrafterError): void {
        this.errors.push(error);
        this.renderError(error);
    }

    public addWarning(warning: DrafterWarning): void {
        this.warnings.push(warning);
        this.renderWarning(warning);
    }

    public addInfo(info: DrafterInfo): void {
        this.infos.push(info);
        this.renderInfo(info);
    }

    private renderError(error: DrafterError): void {
        const errorElement = (
            <div class="error-item">
                <div class="error-header">
                    <span class="error-icon">❌</span>
                    <strong class="error-message">{error.message}</strong>
                </div>
                <div class="error-details">
                    <div class="error-where">
                        <strong>Where:</strong> {error.where}
                    </div>
                    <div class="error-description">{error.details}</div>
                    {error.traceback && (
                        <details class="error-traceback">
                            <summary>Traceback</summary>
                            <pre>{error.traceback}</pre>
                        </details>
                    )}
                </div>
            </div>
        );
        this.listElement.appendChild(errorElement);
    }

    private renderWarning(warning: DrafterWarning): void {
        const warningElement = (
            <div class="warning-item">
                <div class="warning-header">
                    <span class="warning-icon">⚠️</span>
                    <strong class="warning-message">{warning.message}</strong>
                </div>
                <div class="warning-details">
                    <div class="warning-where">
                        <strong>Where:</strong> {warning.where}
                    </div>
                    <div class="warning-description">{warning.details}</div>
                    {warning.traceback && (
                        <details class="warning-traceback">
                            <summary>Traceback</summary>
                            <pre>{warning.traceback}</pre>
                        </details>
                    )}
                </div>
            </div>
        );
        this.listElement.appendChild(warningElement);
    }

    private renderInfo(info: DrafterInfo): void {
        const infoElement = (
            <div class="info-item">
                <div class="info-header">
                    <span class="info-icon">ℹ️</span>
                    <strong class="info-message">{info.message}</strong>
                </div>
                <div class="info-details">
                    <div class="info-where">
                        <strong>Where:</strong> {info.where}
                    </div>
                    <div class="info-description">{info.details}</div>
                </div>
            </div>
        );
        this.listElement.appendChild(infoElement);
    }

    public clear(): void {
        this.errors = [];
        this.warnings = [];
        this.infos = [];
        this.listElement.replaceChildren();
    }
}
