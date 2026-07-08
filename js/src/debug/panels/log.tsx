import { Panel } from "./panel";
import type { TelemetryRecord } from "../telemetry";
import type { ErrorDetailsJson } from "../telemetry/errors";

interface LogEntry {
	message: string;
}

export class LogPanel extends Panel {
	constructor(containerId: string, instanceId: number, root: ParentNode = document) {
		super(containerId, instanceId, "drafter-debug-log", "Event Log", root);
	}

	protected get initialContent() {
		return <div></div>;
	}

	public renderEvent(event: TelemetryRecord): void {
		const envelope = this.asErrorDetails(event);
		if (envelope) {
			switch (envelope.severity) {
				case "critical":
				case "error":
					this.renderLogError({ message: envelope.message });
					break;
				case "warning":
					this.renderLogWarning({ message: envelope.message });
					break;
				case "info":
					this.renderLogInfo({ message: envelope.message });
					break;
				default:
					this.renderLogDefault(envelope.message);
					break;
			}
			return;
		}

		switch (event.metadata?.level) {
			case "error":
				this.renderLogError({ message: event.kind });
				break;
			case "warning":
				this.renderLogWarning({ message: event.kind });
				break;
			case "info":
				this.renderLogInfo({ message: event.kind });
				break;
			default:
				this.renderLogDefault(event.kind);
				break;
		}
	}

	private asErrorDetails(record: TelemetryRecord): ErrorDetailsJson | null {
		const error = (record as { error?: unknown }).error;
		if (!error || typeof error !== "object") {
			return null;
		}
		if (
			"id" in error &&
			"category" in error &&
			"severity" in error &&
			"message" in error
		) {
			return error as ErrorDetailsJson;
		}
		return null;
	}

	public renderLogWarning(warning: LogEntry): void {
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

	public renderLogError(error: LogEntry): void {
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

	public renderLogInfo(info: LogEntry): void {
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
