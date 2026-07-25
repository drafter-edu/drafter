import type { TelemetryRecord } from "../telemetry";
import type { ErrorDetailsJson } from "../telemetry/errors";

export class DebugPanelError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "DebugPanelError";
    }
}

/**
 * Extract the canonical error envelope from a telemetry record, when it
 * carries one (Python ErrorRecord.to_json() / TS ErrorTelemetryRecord).
 * Shared by the event log, the Current tab's problems list, and the tab
 * badge counters so they all agree on what counts as an error/warning.
 */
export function extractErrorDetails(
    record: TelemetryRecord
): ErrorDetailsJson | null {
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
