import type { Suspension } from "./skulpt";

export interface ClientBridgeWrapperInterface {
    goto(url: string, formData?: FormData): Suspension;
    reset(): Suspension;
    saveState(): void;
    loadState(): void;
    downloadState(): void;
    uploadState(): void;
}
