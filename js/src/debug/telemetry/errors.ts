/**
 * Error/Warning/Info event types.
 */

import type { BaseEvent } from "./base";

export interface DrafterLog extends BaseEvent {
    event_type: "DrafterLog" | "DrafterError" | "DrafterWarning" | "DrafterInfo";
    message: string;
    where: string;
    details: string;
}

export interface DrafterError extends DrafterLog {
    event_type: "DrafterError";
    traceback?: string;
}

export interface DrafterWarning extends DrafterLog {
    event_type: "DrafterWarning";
    traceback?: string;
}

export interface DrafterInfo extends DrafterLog {
    event_type: "DrafterInfo";
}
