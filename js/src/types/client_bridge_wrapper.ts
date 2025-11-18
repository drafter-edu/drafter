import type { Suspension } from "./skulpt";

export interface ClientBridgeWrapperInterface {
    goto(url: string, formData?: FormData): Suspension;
}
