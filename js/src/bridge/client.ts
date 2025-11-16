import type { Suspension } from "../types/skulpt";
import type { DebugPanel } from "../debug";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { TelemetryEvent } from "../debug/telemetry";

type NavEvent =
    | { kind: "link"; url: string; data: FormData; submitter?: HTMLElement }
    | { kind: "form"; url: string; data: FormData; submitter?: HTMLElement };

/**
 * This module gets included in the Skulpt build as a built-in module,
 * using a completely separate mechanism. Basically, it is compiled by
 * scripts/precompile-typescript.mjs (as part of precompile-python.mjs) and
 * injected into the Skulpt build as a built-in file.
 */
function $builtinmodule(name: string) {
    const drafter_client_mod: Record<string, any> = {};

    return Sk.misceval.chain(
        Sk.importModule("drafter.data.request", false, true),
        (request_mod) => {
            drafter_client_mod.Request =
                request_mod.$d.data.$d.request.$d.Request;
            return Sk.importModule("drafter.site.site", false, true);
        },
        (site_mod) => {
            drafter_client_mod.DRAFTER_TAG_IDS = Sk.ffi.remapToJs(
                site_mod.$d.site.$d.site.$d.DRAFTER_TAG_IDS
            );
            return Sk.importModule("drafter.monitor.telemetry", false, true);
        },
        (telemetry_mod) => {
            drafter_client_mod.TelemetryEvent =
                telemetry_mod.$d.monitor.$d.telemetry.$d.TelemetryEvent;
            drafter_client_mod.TelemetryCorrelation =
                telemetry_mod.$d.monitor.$d.telemetry.$d.TelemetryCorrelation;
            return Sk.importModule("drafter.monitor.bus", false, true);
        },
        (event_bus_mod) => {
            drafter_client_mod.get_main_event_bus =
                event_bus_mod.$d.monitor.$d.bus.$d.get_main_event_bus;
            return drafter_client_mod;
        },
        () => drafter_bridge_client_module(drafter_client_mod)
    );
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

function drafter_bridge_client_module(drafter_client_mod: Record<string, any>) {
    const {
        builtin: {
            str: pyStr,
            tuple: pyTuple,
            list: pyList,
            int_: pyInt,
            bool: pyBool,
            func: pyFunc,
            dict: pyDict,
            TypeError: pyTypeError,
            ValueError,
            none: { none$: pyNone },
            NotImplemented: { NotImplemented$: pyNotImplemented },
            abs: pyAbs,
            len: pyLen,
            checkString,
            checkInt,
        },

        abstr: {
            buildNativeClass,
            checkNoKwargs,
            checkArgsLen,
            checkOneArg,
            numberUnaryOp,
            numberBinOp,
            numberInplaceBinOp,
            objectGetItem,
            objectDelItem,
            objectSetItem,
            sequenceConcat,
            sequenceContains,
            sequenceGetCountOf,
            sequenceGetIndexOf,
            sequenceInPlaceConcat,
            typeName,
            lookupSpecial,
            gattr: getAttr,
            setUpModuleMethods,
        },
        misceval: {
            richCompareBool,
            asIndexOrThrow,
            chain: chainOrSuspend,
            callsimArray: pyCall,
            callsimOrSuspendArray: pyCallOrSuspend,
            objectRepr,
        },
        generic: { getAttr: genericGetAttr },
    } = Sk;

    drafter_client_mod.__name__ = new pyStr("drafter.bridge.client");

    const Request = drafter_client_mod.Request;

    const str_payload = new Sk.builtin.str("payload");
    const str_url = new Sk.builtin.str("url");
    const str_body = new Sk.builtin.str("body");
    const str_request_id = new Sk.builtin.str("request_id");
    const str_response_id = new Sk.builtin.str("response_id");
    const str_id = new Sk.builtin.str("id");

    const debug_log = function (event_name: string, ...args: any[]) {
        let eventBus;
        try {
            eventBus = Sk.misceval.callsimArray(
                drafter_client_mod.get_main_event_bus,
                []
            );
        } catch (e) {
            console.error(
                "[Drafter Bridge Client] Failed to get event bus:",
                e
            );
            throw e;
        }
        // TODO: Finish populating the event data
        const event = Sk.misceval.callsimArray(
            drafter_client_mod.TelemetryEvent,
            [
                new pyStr(event_name),
                Sk.misceval.callsimArray(
                    drafter_client_mod.TelemetryCorrelation,
                    []
                ),
                new pyStr("bridge.client"),
            ]
        );
        try {
            Sk.misceval.callsimArray(eventBus.publish, [eventBus, event]);
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

    let requestCount = 0;

    let siteTitle = "";
    drafter_client_mod.set_site_title = new Sk.builtin.func(
        function set_site_title_func(title: pyStr): pyNone {
            const titleStr = Sk.ffi.remapToJs(title);
            siteTitle = titleStr;
            document.title = siteTitle;
            debug_log("site.set_title", siteTitle);
            // const headerTag = document.getElementById(
            //     drafter_client_mod.DRAFTER_TAG_IDS["HEADER"]
            // );
            // if (!headerTag) {
            //     throw new Error(
            //         `Header tag ${drafter_client_mod.DRAFTER_TAG_IDS["HEADER"]} not found`
            //     );
            // }
            // headerTag.innerHTML = siteTitle;
            debugPanel?.setHeaderTitle(siteTitle);
            return pyNone;
        }
    );

    let navigationFunc: pyFunc | null = null;

    class ClientBridgeWrapper implements ClientBridgeWrapperInterface {
        constructor(private clientBridge: pyObject) {}

        public goto(url: string, formData?: FormData) {
            if (!navigationFunc) {
                throw new Error("navigationFunc not set");
            }
            return initiateRequest(url, formData);
        }
    }

    function wrapClientBridge(clientBridge: pyObject): ClientBridgeWrapper {
        const wrapped = new ClientBridgeWrapper(clientBridge);
        console.log("Wrapped client bridge:", wrapped);
        return wrapped;
    }

    let debugPanel: DebugPanel | null = null;
    drafter_client_mod.setup_debug_menu = new Sk.builtin.func(
        function setup_debug_menu_func(clientBridge: pyObject): pyNone {
            debug_log("site.setup_debug_menu");
            debugPanel = new Sk.DebugPanel(
                drafter_client_mod.DRAFTER_TAG_IDS["DEBUG"],
                wrapClientBridge(clientBridge)
            );
            console.log("**", clientBridge);
            return pyNone;
        }
    );

    drafter_client_mod.handle_event = new Sk.builtin.func(
        function handle_event_func(event: pyDict): pyNone {
            try {
                const unpackedEvent = Sk.ffi.remapToJs(event) as TelemetryEvent;
                debugPanel?.handleEvent(unpackedEvent);
                return pyNone;
            } catch (e) {
                console.error(
                    "[Drafter Bridge Client] Failed to handle event:",
                    e,
                    event
                );
                throw e;
            }
        }
    );

    const getFile = function (
        file: File,
        data: any,
        key: string
    ): Promise<void> {
        return file.arrayBuffer().then((buffer) => {
            const bytes = new Uint8Array(buffer);
            const content = new Sk.builtin.bytes(bytes);
            const fileData = {
                filename: file.name,
                content,
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

    const makeRequest = function (url: string, formData?: FormData) {
        const data: Record<string, FormDataEntryValue | FormDataEntryValue[]> =
            {};
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
            const dataDict: pyDict = new pyDict();
            for (const [k, v] of Object.entries(data)) {
                dataDict.mp$ass_subscript(
                    new pyStr(k),
                    new pyList([Sk.ffi.remapToPy(v)])
                );
            }
            const args = [
                new pyInt(requestCount),
                new pyStr("submit"),
                new pyStr(url),
                new pyList([]),
                dataDict,
                new pyDict(),
            ];
            const request = Sk.misceval.callsimArray(Request, args);
            requestCount += 1;
            return request;
        });
    };

    const addToHistory = function (request: pyObject) {
        const urlObj = request.tp$getattr(str_url);
        const url = Sk.ffi.remapToJs(urlObj) as string;
        const requestIdObj = request.tp$getattr(str_id);
        const requestId = Sk.ffi.remapToJs(requestIdObj);
        const state = {
            request_id: requestId,
            url: url,
            // TODO: Track parameters as well
        };
        const fullUrl = new URL(window.location.href);
        document.title = `${siteTitle} - ${url}`;
        fullUrl.searchParams.set("route", url);
        window.history.pushState(state, "", fullUrl.toString());
        debug_log("history.push_state", state, request);
    };

    const {
        DRAFTER_TAG_IDS: {
            ROOT: ROOT_ELEMENT_ID,
            FORM: FORM_ELEMENT_ID,
            BODY: BODY_ELEMENT_ID,
        },
    } = drafter_client_mod;

    function initiateRequest(url: string, data?: FormData, remember = true) {
        if (!navigationFunc) {
            throw new Error("navigationFunc not set");
        }
        debug_log("request.initiated", url, data, navigationFunc);
        return Sk.misceval.promiseToSuspension(
            makeRequest(url, data).then((newRequest) => {
                if (remember) {
                    addToHistory(newRequest);
                }
                const nextVisit = navigationFunc?.tp$call([newRequest]);
                return Sk.misceval.asyncToPromise(() => nextVisit);
            })
        );
    }

    const update_site = new pyFunc(function update_site_func(
        response: pyObject,
        callback: pyFunc
    ): Suspension {
        navigationFunc = callback;
        // Implementation for loading a page
        const element = document.getElementById(BODY_ELEMENT_ID);
        if (!element) {
            // TODO: Handle this absolutely crisis of an error properly
            throw new ValueError(`Target element ${BODY_ELEMENT_ID} not found`);
        }
        const startBodyUpdate = () => {
            const body: string = Sk.ffi.remapToJs(
                response.tp$getattr(str_body)
            );
            const originalRequestId: pyInt =
                response.tp$getattr(str_request_id);
            const responseId: pyInt = response.tp$getattr(str_id);
            replaceHTML(element, body);
            debugPanel?.setRoute(
                Sk.ffi.remapToJs(response.tp$getattr(str_url))
            );
            debug_log(
                "dom.updated_body",
                "update_site called with",
                response,
                navigationFunc
            );
            const mounted = mountNavigation(element, (navEvent: NavEvent) => {
                return initiateRequest(navEvent.url, navEvent.data);
            });
            debug_log(
                "dom.mount_navigation",
                "Mounted navigation handlers:",
                mounted
            );
            return Sk.builtin.bool.true$;
        };
        return Sk.misceval.chain<any, any>([], startBodyUpdate);
    });

    drafter_client_mod.update_site = update_site;

    // Track handlers for cleanup
    let clickHandler: ((event: MouseEvent) => void) | null = null;
    let submitHandler: ((event: SubmitEvent) => void) | null = null;

    function mountNavigation(
        root: HTMLElement,
        onNavigation: (e: NavEvent) => Suspension | void
    ) {
        // Clean up old handlers
        if (clickHandler) {
            root.removeEventListener("click", clickHandler);
        }
        clickHandler = function (event: MouseEvent) {
            // debug_log("dom.click", event);
            const target = event.target as Element | null;
            if (!target) return;

            // First, try to find the closest element with data-nav or data-call
            const nearestNavLink = target.closest?.("[data-nav], [data-call]");
            if (nearestNavLink && root.contains(nearestNavLink)) {
                event.preventDefault();
                const name =
                    nearestNavLink.getAttribute("data-nav") ||
                    nearestNavLink.getAttribute("data-call");
                if (!name) return; // TODO: Handle error

                // Old approach: Find nearest form submission
                // const form = nearestNavLink.closest("form");
                // New approach: Use fixed form ID
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
                } else {
                    // TODO: Handle error
                }
            }
        };
        root.addEventListener("click", clickHandler);

        const formRoot = document.getElementById(
            FORM_ELEMENT_ID
        ) as HTMLFormElement;
        if (!formRoot) {
            // TODO: Also handle this crisis properly
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
    drafter_client_mod.setup_navigation = new pyFunc(
        function setup_navigation_func(callback: pyFunc) {
            navigationFunc = callback;
            // TODO: Handle navigation on page load by inspecting the query string
            if (window.location.search) {
                const params = new URLSearchParams(window.location.search);
                const route = params.get("route");
                if (route) {
                    initiateRequest(route, undefined, navigationFunc, false);
                }
            }
            if (popstateListener) {
                window.removeEventListener("popstate", popstateListener);
            }
            // TODO: Handle scroll restoration
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
                    initiateRequest(url, undefined, false);
                } else {
                    debug_log("history.popstate_no_state", event);
                    document.title = siteTitle;
                    const fullUrl = new URL(window.location.href);
                    fullUrl.searchParams.delete("route");
                    window.history.replaceState({}, "", fullUrl.toString());
                    initiateRequest("index", undefined, false);
                }
            };
            window.addEventListener("popstate", popstateListener);
            return pyNone;
        }
    );

    drafter_client_mod.console_log = new Sk.builtin.func(
        function console_log_func(event: pyObject) {
            try {
                let repr = event.$r().v;
                console.log("[Drafter]", repr);
            } catch (e) {
                console.log("[Drafter] (unrepresentable event)", e, event);
            }
            return pyNone;
        }
    );

    window.stopHotkeyListener = () => {
        throw new Error("hotkeyListener not set");
    };
    window.hotkeyListenerReady = window.hotkeyListenerReady || false;
    const hotkeyEvents: Record<string, pyFunc> = {};
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
                Sk.misceval.callsimArray(hotkeyEvents[key], []);
            }
            lastPressTime = now;
        }
        window.stopHotkeyListener = () => {
            document.removeEventListener("keydown", hotkeyHandler);
            window.hotkeyListenerReady = false;
            debug_log("hotkey.listener_stopped");
        };
    }
    drafter_client_mod.register_hotkey = new Sk.builtin.func(
        function register_hotkey_func(
            keyCombo: pyStr,
            callback: pyFunc
        ): pyNone {
            if (!window.hotkeyListenerReady) {
                document.addEventListener("keydown", hotkeyHandler);
                window.hotkeyListenerReady = true;
            }
            const comboStr = Sk.ffi.remapToJs(keyCombo) as string;
            debug_log("hotkey.register", comboStr);
            hotkeyEvents[comboStr.toLowerCase()] = callback;
            return pyNone;
        }
    );

    return drafter_client_mod;
}
