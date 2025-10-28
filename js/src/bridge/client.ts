import type { Suspension } from "../types/skulpt";

/**
 * This module gets included in the Skulpt build as a built-in module,
 * using a completely separate mechanism. Basically, it is compiled by
 * scripts/precompile-typescript.mjs (as part of precompile-python.mjs) and
 * injected into the Skulpt build as a built-in file.
 */
function $builtinmodule(name: string) {
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

    const load_page = new pyFunc(function (
        url: pyStr,
        parameters: typeof pyList,
        target: pyStr,
        navigate: pyFunc
    ): Suspension {
        // Implementation for loading a page
        console.log("Loading page:", url.v, parameters, target.v);
        const element = document.getElementById(target.v);
        if (!element) {
            throw new ValueError(`Target element ${target.v} not found`);
        }
        const loadPage = (page: any) => {
            console.log("Setting up navigation:", page);
            return modifyLinks(element, (url: string, data?: any) => {
                console.log("Navigating to:", url, data, navigate);
                const urlObj = new URL(url, window.location.href);
                // Remove leading slash
                const pathPart = urlObj.pathname.replace(/^\/+/, "");
                const args = [new pyStr(pathPart), new pyStr("TEST")];
                const kwargs = new pyDict();
                const nextPage = navigate.tp$call(args, kwargs);
                return Sk.misceval.promiseToSuspension(
                    Sk.misceval.asyncToPromise(() => nextPage)
                );
            });
        };
        return Sk.misceval.chain<any, any>([], loadPage);
    });

    let oldNavigationHandler: null | ((event: MouseEvent) => void) = null;
    function modifyLinks(target: HTMLElement, callback: (url: string) => void) {
        if (oldNavigationHandler) {
            target.removeEventListener("click", oldNavigationHandler);
        }
        oldNavigationHandler = function (event: MouseEvent) {
            console.log("CLICKED", event);
            const el = event.target as Element | null;
            if (!el) {
                return;
            }
            if (el.matches("a[download]")) {
                return;
            }
            if (el.matches("a")) {
                event.preventDefault();
                return callback((el as HTMLAnchorElement).href);
            }
            if (
                el.matches('input[type="submit"]') ||
                el.matches('button[type="submit"]')
            ) {
                console.log("OH");
                event.preventDefault();
                const closestForm = el.closest(
                    "form"
                ) as HTMLFormElement | null;
                const formAction =
                    (el as HTMLElement).getAttribute("formaction") || "";
                if (closestForm) {
                    const data = Object.fromEntries(
                        new FormData(closestForm, el as any).entries()
                    );
                    console.log(
                        "Clicked!",
                        closestForm,
                        data,
                        formAction,
                        event,
                        (event as any).submitter
                    );
                    return callback(formAction, data);
                }
            }
        };
        target.addEventListener("click", oldNavigationHandler);
    }

    return {
        __name__: new pyStr("drafter.bridge.client"),
        load_page,
    };
}
