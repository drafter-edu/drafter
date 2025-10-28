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
            return Sk.importModule("drafter.data.outcome", false, true);
        },
        (outcome_mod) => {
            drafter_client_mod.Outcome =
                outcome_mod.$d.data.$d.outcome.$d.Outcome;
            //     return Sk.importModule("operator", false, true);
        },
        // (operator) => {
        //     drafter_client_mod._itemgetter = operator.$d.itemgetter;
        // },
        () => drafter_bridge_client_module(drafter_client_mod)
    );
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
    const Outcome = drafter_client_mod.Outcome;

    const str_payload = new Sk.builtin.str("payload");
    const str_body = new Sk.builtin.str("body");
    const str_request_id = new Sk.builtin.str("request_id");
    const str_response_id = new Sk.builtin.str("response_id");
    const str_id = new Sk.builtin.str("id");

    const debug_log = function (...args: any[]) {
        console.log("[Drafter Bridge Client]", ...args);
    };

    let requestCount = 0;
    let outcomeCount = 0;

    const ROOT_ELEMENT_ID =
        window.DRAFTER_SITE_ROOT_ELEMENT_ID || "drafter-site--";
    const FORM_ELEMENT_ID = "drafter-form--";

    const makeOutcome = function (originalRequestId: pyInt, responseId: pyInt) {
        const args = [new pyInt(outcomeCount), originalRequestId, responseId];
        console.log(Outcome, args);
        const outcome = Sk.misceval.callsimArray(Outcome, args);
        outcomeCount += 1;
        return outcome;
    };

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

    const update_site = new pyFunc(function update_site_func(
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
        debug_log("update_site called with", response, callback);
        const element = document.getElementById(ROOT_ELEMENT_ID);
        if (!element) {
            // TODO: Handle this absolutely crisis of an error properly
            throw new ValueError(`Target element ${ROOT_ELEMENT_ID} not found`);
        }
        const startSiteUpdate = () => {
            debug_log("Starting site update...");
            const body: string = Sk.ffi.remapToJs(
                response.tp$getattr(str_body)
            );
            const originalRequestId: pyInt =
                response.tp$getattr(str_request_id);
            const responseId: pyInt = response.tp$getattr(str_id);
            debug_log("Updating site body to:", body);
            element.innerHTML = body;
            const mounted = mountNavigation(element, (navEvent: NavEvent) => {
                debug_log(
                    "Navigating to:",
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
            debug_log("Mounted navigation handlers:", mounted);
            return makeOutcome(originalRequestId, responseId);
        };
        return Sk.misceval.chain<any, any>([], startSiteUpdate);
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
            debug_log("Clicked", event);
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
            throw new Error(`Form element ${FORM_ELEMENT_ID} not found`);
        }
        // TODO: Check if still needed; the old handler was probably already removed
        // if (submitHandler) {
        //     formRoot.removeEventListener("submit", submitHandler);
        // }
        submitHandler = function (event: SubmitEvent) {
            debug_log("Form submitted", event);

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

    drafter_client_mod.update_site = update_site;

    return drafter_client_mod;
}
