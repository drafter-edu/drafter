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

/**
 * The last "File ..., line N" of a Python traceback, or the first "at"
 * frame of a JavaScript stack: where the error was raised, as text.
 */
function topFrame(traceback: string | null | undefined): string {
    if (!traceback) {
        return "";
    }
    const lines = traceback.split("\n").map((line) => line.trim());
    const pythonFrames = lines.filter((line) => line.startsWith("File "));
    if (pythonFrames.length > 0) {
        return pythonFrames[pythonFrames.length - 1];
    }
    return lines.find((line) => line.startsWith("at ")) ?? "";
}

/**
 * A key under which repeats of the same problem agree: the error's id and
 * severity, the first line of its message, where it was raised, and the
 * route it belongs to. The request id is deliberately left out so that
 * the same failure on consecutive visits (a timer route that breaks every
 * tick) counts as one problem repeating, not many problems.
 */
export function errorFingerprint(envelope: ErrorDetailsJson): string {
    const firstLine = (envelope.message ?? "").split("\n")[0].trim();
    return [
        envelope.id,
        envelope.severity,
        firstLine,
        topFrame(envelope.traceback),
        envelope.context?.route ?? "",
    ].join("\u0000");
}
