export interface DrafterInitOptions {
    code?: string;
    url?: string;
    presentErrors?: boolean;
}

export function clearDrafterSiteRoot() {
    const rootElement = document.getElementById(
        "drafter-root--"
    ) as HTMLElement;
    if (rootElement) {
        rootElement.innerHTML = "";
    } else {
        throw new Error(`Element with ID drafter-root-- not found`);
    }
}

export function handleSystemError(
    message: string,
    error: any,
    suggestion: string = "Please show this to your instructor for more help."
) {
    console.error("[Drafter System Error]", message, error);
    alert(`Drafter System Error: ${message}\n${suggestion}\n${error}`);
    return error;
}
