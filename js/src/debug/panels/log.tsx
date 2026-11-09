import { Panel } from "./panel";
import type { TelemetryRecord } from "../telemetry";
import { extractErrorDetails } from "../utils/errors";

interface LogEntry {
	message: string;
}

export class LogPanel extends Panel {
	/** The most recent line, so an identical next line raises its count. */
	private lastLine: { key: string; element: HTMLElement; count: number } | null =
		null;

	/**
	 * Append a line, or when it repeats the previous line exactly, bump
	 * that line's "×N" counter instead (a failing timer route would
	 * otherwise fill the log with one line per tick).
	 */
	private appendLine(key: string, build: () => HTMLElement): void {
		if (this.lastLine && this.lastLine.key === key) {
			this.lastLine.count += 1;
			let badge = this.lastLine.element.querySelector(
				".drafter-debug-problem-count",
			) as HTMLElement | null;
			if (!badge) {
				badge = (
					<span class="drafter-debug-problem-count"></span>
				) as HTMLElement;
				this.lastLine.element.appendChild(badge);
			}
			badge.textContent = ` ×${this.lastLine.count}`;
			return;
		}
		const element = build();
		this.getContentElement().appendChild(element);
		this.lastLine = { key, element, count: 1 };
	}

	constructor(containerId: string, instanceId: number, root: ParentNode = document) {
		super(containerId, instanceId, "drafter-debug-log", "Event Log", root);
	}

	protected get initialContent() {
		return <div></div>;
	}

	public renderEvent(event: TelemetryRecord): void {
		const envelope = extractErrorDetails(event);
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

	public renderLogWarning(warning: LogEntry): void {
		const warningBullet = "\u26A0 "; // Unicode for warning sign
		this.appendLine(
			`warning:${warning.message}`,
			() =>
				(
					<div class="drafter-log-warning-item">
						{warningBullet}
						{warning.message}
					</div>
				) as HTMLElement,
		);
	}

	public renderLogError(error: LogEntry): void {
		const errorBullet = "\u274C "; // Unicode for error
		this.appendLine(
			`error:${error.message}`,
			() =>
				(
					<div class="drafter-log-error-item">
						{errorBullet}
						{error.message}
					</div>
				) as HTMLElement,
		);
	}

	public renderLogInfo(info: LogEntry): void {
		const bullet = "\u2022 "; // Unicode for bullet point
		this.appendLine(
			`info:${info.message}`,
			() =>
				(
					<div class="drafter-log-info-item">
						{bullet}
						{info.message}
					</div>
				) as HTMLElement,
		);
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
