import type { Suspension } from "../types/skulpt";

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
            return Sk.importModule("drafter.site", false, true);
        },
        (site_mod) => {
            drafter_client_mod.DRAFTER_TAG_IDS = Sk.ffi.remapToJs(
                site_mod.$d.site.$d.DRAFTER_TAG_IDS
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
    const r = document.createRange();
    r.selectNode(tag);
    const fragment = r.createContextualFragment(html);
    tag.replaceChildren(fragment);
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

    const makeRequest = function (url: string, formData: FormData) {
        const data: Record<string, FormDataEntryValue | FormDataEntryValue[]> =
            {};
        for (const [k, v] of formData.entries()) {
            data[k] = k in data ? ([] as any[]).concat(data[k] as any, v) : v;
        }
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
    };

    const {
        DRAFTER_TAG_IDS: {
            ROOT: ROOT_ELEMENT_ID,
            FORM: FORM_ELEMENT_ID,
            BODY: BODY_ELEMENT_ID,
        },
    } = drafter_client_mod;

    const update_body = new pyFunc(function update_body_func(
        response: pyObject,
        callback: pyFunc
    ): Suspension {
        /*
        url: pyStr,
        parameters: typeof pyList,
        target: pyStr,
        navigate: pyFunc
        */
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
            debug_log(
                "dom.updated_body",
                "update_body called with",
                response,
                callback
            );
            const mounted = mountNavigation(element, (navEvent: NavEvent) => {
                debug_log(
                    "request.initiated",
                    navEvent.url,
                    navEvent.data,
                    callback
                );
                // TODO: Process data into something Skulpt can understand
                // const args = [new pyStr(pathPart), new pyStr("TEST")];
                // const kwargs = new pyDict();
                const newRequest = makeRequest(navEvent.url, navEvent.data);
                const nextVisit = callback.tp$call([newRequest]);
                return Sk.misceval.promiseToSuspension(
                    Sk.misceval.asyncToPromise(() => nextVisit)
                );
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
            debug_log("dom.click", event);
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
                    const formData = new FormData(
                        form,
                        nearestNavLink as HTMLElement
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

    drafter_client_mod.update_site = update_body;

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

    return drafter_client_mod;
}
