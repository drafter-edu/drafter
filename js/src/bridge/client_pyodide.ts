import type { DebugPanel } from "../debug";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { TelemetryEvent } from "../debug/telemetry";

type NavEvent =
    | { kind: "link"; url: string; data: FormData; submitter?: HTMLElement }
    | { kind: "form"; url: string; data: FormData; submitter?: HTMLElement };

/**
 * This module provides the Pyodide-compatible bridge for Drafter.
 * It replaces the Skulpt-specific bridge with Pyodide FFI mechanisms.
 */

declare global {
    interface Window {
        pyodide: any;
        stopHotkeyListener: () => void;
        hotkeyListenerReady: boolean;
    }
}

function replaceHTML(tag: HTMLElement, html: string) {
    // Save current scroll position
    const scrollTop = window.scrollY;
    const scrollLeft = window.scrollX;

    // Replace content
    const r = document.createRange();
    r.selectNode(tag);
    const fragment = r.createContextualFragment(html);
    tag.replaceChildren(fragment);

    // Restore scroll position
    window.scrollTo(scrollLeft, scrollTop);
}

export function createPyodideBridge() {
    const pyodide = window.pyodide;
    if (!pyodide) {
        throw new Error("Pyodide not found. Please ensure Pyodide is loaded before initializing Drafter.");
    }

    // Import Python modules we need
    const drafter_data_request = pyodide.pyimport("drafter.data.request");
    const drafter_site_site = pyodide.pyimport("drafter.site.site");
    const drafter_monitor_telemetry = pyodide.pyimport("drafter.monitor.telemetry");
    const drafter_monitor_bus = pyodide.pyimport("drafter.monitor.bus");

    const Request = drafter_data_request.Request;
    const DRAFTER_TAG_IDS = drafter_site_site.DRAFTER_TAG_IDS.toJs();
    const TelemetryEvent = drafter_monitor_telemetry.TelemetryEvent;
    const TelemetryCorrelation = drafter_monitor_telemetry.TelemetryCorrelation;
    const get_main_event_bus = drafter_monitor_bus.get_main_event_bus;

    const debug_log = function (event_name: string, ...args: any[]) {
        let eventBus;
        try {
            eventBus = get_main_event_bus();
        } catch (e) {
            console.error(
                "[Drafter Bridge Client] Failed to get event bus:",
                e
            );
            throw e;
        }
        
        const event = TelemetryEvent(event_name, TelemetryCorrelation(), "bridge.client");
        try {
            eventBus.publish(event);
        } catch (e) {
            console.error(
                "[Drafter Bridge Client] Failed to publish event:",
                e,
                event
            );
            throw e;
        }

        console.log("[Drafter Bridge Client]", event_name, ...args);
    };

    // Starts at 1 because ClientBridge.make_initial_request uses 0
    let requestCount = 1;

    let siteTitle = "";
    function set_site_title(title: string): void {
        siteTitle = title;
        document.title = siteTitle;
        debug_log("site.set_title", siteTitle);
        debugPanel?.setHeaderTitle(siteTitle);
    }

    let navigationFunc: any = null;

    class ClientBridgeWrapper implements ClientBridgeWrapperInterface {
        constructor(private clientBridge: any) {}

        public goto(url: string, formData?: FormData, action = "system") {
            if (!navigationFunc) {
                throw new Error("navigationFunc not set");
            }
            return initiateRequest(url, formData, true, action);
        }
    }

    function wrapClientBridge(clientBridge: any): ClientBridgeWrapper {
        const wrapped = new ClientBridgeWrapper(clientBridge);
        console.log("Wrapped client bridge:", wrapped);
        return wrapped;
    }

    let debugPanel: DebugPanel | null = null;
    function setup_debug_menu(clientBridge: any): void {
        debug_log("site.setup_debug_menu");
        debugPanel = new (window as any).Sk.DebugPanel(
            DRAFTER_TAG_IDS["DEBUG"],
            wrapClientBridge(clientBridge)
        );
        console.log("**", clientBridge);
    }

    function handle_event(event: any): void {
        try {
            const unpackedEvent = event.toJs() as TelemetryEvent;
            debugPanel?.handleEvent(unpackedEvent);
        } catch (e) {
            console.error(
                "[Drafter Bridge Client] Failed to handle event:",
                e,
                event
            );
            throw e;
        }
    }

    const getFile = function (
        file: File,
        data: any,
        key: string
    ): Promise<void> {
        return file.arrayBuffer().then((buffer) => {
            const bytes = new Uint8Array(buffer);
            const fileData = {
                filename: file.name,
                content: bytes,
                type: file.type,
                size: file.size,
                __file_upload__: true,
            };
            data[key] =
                key in data
                    ? ([] as any[]).concat(data[key] as any, fileData)
                    : fileData;
        });
    };

    const makeRequest = function (
        url: string,
        formData?: FormData,
        action = "submit"
    ): Promise<any> {
        const data: Record<string, FormDataEntryValue | FormDataEntryValue[]> = {};
        const filePromises: Promise<void>[] = [];
        if (formData) {
            for (const [k, v] of formData.entries()) {
                if (v instanceof File) {
                    const promise = getFile(v, data, k);
                    filePromises.push(promise);
                } else {
                    data[k] =
                        k in data ? ([] as any[]).concat(data[k] as any, v) : v;
                }
            }
        }
        return Promise.all(filePromises).then(() => {
            const dataDict: Record<string, any[]> = {};
            for (const [k, v] of Object.entries(data)) {
                dataDict[k] = [v];
            }
            const request = Request(
                requestCount,
                action,
                url,
                [],
                dataDict,
                {}
            );
            requestCount += 1;
            return request;
        });
    };

    const addToHistory = function (request: any) {
        const url = request.url;
        const requestId = request.id;
        const state = {
            request_id: requestId,
            url: url,
        };
        const fullUrl = new URL(window.location.href);
        document.title = `${siteTitle} - ${url}`;
        fullUrl.searchParams.set("route", url);
        window.history.pushState(state, "", fullUrl.toString());
        debug_log("history.push_state", state, request);
    };

    const {
        ROOT: ROOT_ELEMENT_ID,
        FORM: FORM_ELEMENT_ID,
        BODY: BODY_ELEMENT_ID,
    } = DRAFTER_TAG_IDS;

    async function initiateRequest(
        url: string,
        data?: FormData,
        remember = true,
        action = "submit"
    ): Promise<any> {
        if (!navigationFunc) {
            throw new Error("navigationFunc not set");
        }
        debug_log("request.initiated", url, data, navigationFunc);
        const newRequest = await makeRequest(url, data, action);
        if (remember) {
            addToHistory(newRequest);
        }
        const nextVisit = await navigationFunc(newRequest);
        return nextVisit;
    }

    function update_site(response: any, callback: any): boolean {
        navigationFunc = callback;
        // Implementation for loading a page
        const element = document.getElementById(BODY_ELEMENT_ID);
        if (!element) {
            throw new Error(`Target element ${BODY_ELEMENT_ID} not found`);
        }
        
        const body: string = response.body;
        const originalRequestId = response.request_id;
        const responseId = response.id;
        
        replaceHTML(element, body);
        debugPanel?.setRoute(response.url);
        debug_log(
            "dom.updated_body",
            "update_site called with",
            response,
            navigationFunc
        );
        
        const mounted = mountNavigation(element, (navEvent: NavEvent) => {
            return initiateRequest(
                navEvent.url,
                navEvent.data,
                true,
                navEvent.kind
            );
        });
        debug_log(
            "dom.mount_navigation",
            "Mounted navigation handlers:",
            mounted
        );
        return true;
    }

    // Track handlers for cleanup
    let clickHandler: ((event: MouseEvent) => void) | null = null;
    let submitHandler: ((event: SubmitEvent) => void) | null = null;

    function mountNavigation(
        root: HTMLElement,
        onNavigation: (e: NavEvent) => Promise<any>
    ) {
        // Clean up old handlers
        if (clickHandler) {
            root.removeEventListener("click", clickHandler);
        }
        clickHandler = function (event: MouseEvent) {
            const target = event.target as Element | null;
            if (!target) return;

            // First, try to find the closest element with data-nav or data-call
            const nearestNavLink = target.closest?.("[data-nav], [data-call]");
            if (nearestNavLink && root.contains(nearestNavLink)) {
                event.preventDefault();
                const name =
                    nearestNavLink.getAttribute("data-nav") ||
                    nearestNavLink.getAttribute("data-call");
                if (!name) return;

                const form = document.getElementById(
                    FORM_ELEMENT_ID
                ) as HTMLFormElement | null;
                if (form) {
                    const isAnchor =
                        nearestNavLink.tagName.toLowerCase() === "a";
                    const formData = new FormData(
                        form,
                        isAnchor ? undefined : (nearestNavLink as HTMLElement)
                    );
                    return onNavigation({
                        kind: "link",
                        url: name,
                        data: formData,
                        submitter: nearestNavLink as HTMLElement,
                    });
                }
            }
        };
        root.addEventListener("click", clickHandler);

        const formRoot = document.getElementById(
            FORM_ELEMENT_ID
        ) as HTMLFormElement;
        if (!formRoot) {
            throw new Error(`Form element ${FORM_ELEMENT_ID} not found`);
        }
        submitHandler = function (event: SubmitEvent) {
            debug_log("dom.form_submit", event);

            event.preventDefault();
            const submitter = (event as any).submitter as HTMLElement | null;
            const formData = new FormData(
                formRoot,
                submitter as HTMLElement | undefined
            );

            const url =
                submitter?.getAttribute("formaction") ||
                formRoot.action ||
                window.location.href;
            return onNavigation({
                kind: "form",
                url,
                data: formData,
                submitter: submitter || undefined,
            });
        };
        formRoot.addEventListener("submit", submitHandler);
    }

    let popstateListener: ((event: PopStateEvent) => void) | null = null;
    function setup_navigation(callback: any): void {
        navigationFunc = callback;
        // Handle navigation on page load by inspecting the query string
        if (window.location.search) {
            const params = new URLSearchParams(window.location.search);
            const route = params.get("route");
            if (route) {
                initiateRequest(route, undefined, false, "query_string");
            }
        }
        if (popstateListener) {
            window.removeEventListener("popstate", popstateListener);
        }
        popstateListener = function (event: PopStateEvent) {
            debug_log("history.popstate", event);
            if (event.state && event.state.request_id !== undefined) {
                const request_id = event.state.request_id;
                const url = event.state.url;
                debug_log("request.back", url, event.state);
                document.title = `${siteTitle} - ${url}`;
                const fullUrl = new URL(window.location.href);
                fullUrl.searchParams.set("route", url);
                window.history.replaceState(
                    event.state,
                    "",
                    fullUrl.toString()
                );
                initiateRequest(url, undefined, false, "back");
            } else {
                debug_log("history.popstate_no_state", event);
                document.title = siteTitle;
                const fullUrl = new URL(window.location.href);
                fullUrl.searchParams.delete("route");
                window.history.replaceState({}, "", fullUrl.toString());
                initiateRequest("index", undefined, false, "back");
            }
        };
        window.addEventListener("popstate", popstateListener);
    }

    function console_log(event: any): void {
        try {
            let repr = String(event);
            console.log("[Drafter]", repr);
        } catch (e) {
            console.log("[Drafter] (unrepresentable event)", e, event);
        }
    }

    window.stopHotkeyListener = () => {
        throw new Error("hotkeyListener not set");
    };
    window.hotkeyListenerReady = window.hotkeyListenerReady || false;
    const hotkeyEvents: Record<string, any> = {};
    let lastPressTime = 0;
    const DOUBLE_PRESS_THRESHOLD = 600; // milliseconds
    
    function hotkeyHandler(event: KeyboardEvent) {
        const key = event.key.toLowerCase();
        const ctrl = event.ctrlKey || event.metaKey;

        if (ctrl && hotkeyEvents[key]) {
            const now = Date.now();
            const timeSinceLastPress = now - lastPressTime;
            if (timeSinceLastPress < DOUBLE_PRESS_THRESHOLD) {
                debug_log("hotkey.triggered", key);
                event.preventDefault();
                hotkeyEvents[key]();
            }
            lastPressTime = now;
        }
        window.stopHotkeyListener = () => {
            document.removeEventListener("keydown", hotkeyHandler);
            window.hotkeyListenerReady = false;
            debug_log("hotkey.listener_stopped");
        };
    }
    
    function register_hotkey(keyCombo: string, callback: any): void {
        if (!window.hotkeyListenerReady) {
            document.addEventListener("keydown", hotkeyHandler);
            window.hotkeyListenerReady = true;
        }
        debug_log("hotkey.register", keyCombo);
        hotkeyEvents[keyCombo.toLowerCase()] = callback;
    }

    // Return the bridge module with all functions
    return {
        update_site,
        console_log,
        setup_navigation,
        set_site_title,
        register_hotkey,
        setup_debug_menu,
        handle_event,
    };
}
