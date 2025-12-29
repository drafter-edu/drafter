import type { TelemetryEvent } from "../telemetry";
import type { DrafterWarning } from "../telemetry/errors";

export class LogPanel {
    private getContentElement(): HTMLElement {
        const content = document.getElementsByClassName(
            "drafter-debug-log-content"
        )[0];
        if (!content) {
            throw new Error("DebugPanel: Log section not found.");
        }
        return content as HTMLElement;
    }

    public renderEvent(event: TelemetryEvent): void {
        switch (event.data?.event_type) {
            case "DrafterError":
                this.renderLogError(event.data);
                break;
            case "DrafterWarning":
                this.renderLogWarning(event.data);
                break;
            case "DrafterInfo":
                this.renderLogInfo(event.data);
                break;
            default:
                this.renderLogDefault(event.event_type);
                break;
        }
    }

    public renderLogWarning(warning: DrafterWarning): void {
        const section = this.getContentElement();
        const warningBullet = "\u26A0 "; // Unicode for warning sign

        const newWarning = (
            <div class="drafter-log-warning-item">
                {warningBullet}
                {warning.message}
            </div>
        );

        section.appendChild(newWarning);
    }

    public renderLogError(error: any): void {
        const section = this.getContentElement();

        const errorBullet = "\u274C "; // Unicode for error

        const newError = (
            <div class="drafter-log-error-item">
                {errorBullet}
                {error.message}
            </div>
        );

        section.appendChild(newError);
    }

    public renderLogInfo(info: any): void {
        const section = this.getContentElement();

        const bullet = "\u2022 "; // Unicode for bullet point

        const newInfo = (
            <div class="drafter-log-info-item">
                {bullet}
                {info.message}
            </div>
        );

        section.appendChild(newInfo);
    }

    public renderLogDefault(message: string): void {
        const section = this.getContentElement();

        const bullet = "\u2022 "; // Unicode for bullet point

        const newMessage = (
            <div class="drafter-log-default-item">
                {bullet}
                {message}
            </div>
        );

        section.appendChild(newMessage);
    }
}
