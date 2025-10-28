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
            return mountNav(element, (navEvent: NavEvent) => {
                console.log("Navigation event:", navEvent);
                
                let routeName: string;
                let formData: pyDict | undefined;
                
                if (navEvent.kind === 'form') {
                    // Extract route name from data-nav attribute
                    routeName = navEvent.name;
                    
                    // Convert FormData to Python dict
                    formData = new pyDict();
                    for (const [key, value] of navEvent.data.entries()) {
                        formData.mp$ass_subscript(
                            new pyStr(key),
                            new pyStr(String(value))
                        );
                    }
                } else {
                    // For links and buttons, just use the name
                    routeName = navEvent.name;
                }
                
                const args = [new pyStr(routeName)];
                const kwargs = formData || new pyDict();
                const nextPage = navigate.tp$call(args, kwargs);
                return Sk.misceval.promiseToSuspension(
                    Sk.misceval.asyncToPromise(() => nextPage)
                );
            });
        };
        return Sk.misceval.chain<any, any>([], loadPage);
    });

    // Navigation event types
    type NavEvent =
        | { kind: 'link' | 'button'; name: string; el: Element }
        | { kind: 'form'; name: string; el: HTMLFormElement; data: FormData };

    // Track handlers for cleanup
    let clickHandler: ((event: MouseEvent) => void) | null = null;
    let submitHandler: ((event: SubmitEvent) => void) | null = null;

    /**
     * Mount declarative navigation handlers on a root element.
     * Uses data-nav and data-call attributes for opt-in navigation,
     * with fallback support for formaction attributes for backward compatibility.
     */
    function mountNav(
        root: HTMLElement,
        onNav: (e: NavEvent) => Suspension | void
    ): void {
        // Clean up old handlers if they exist
        if (clickHandler) {
            root.removeEventListener("click", clickHandler);
        }
        if (submitHandler) {
            root.removeEventListener("submit", submitHandler);
        }

        // Click handler for links and buttons
        clickHandler = function (event: MouseEvent) {
            const target = event.target as Element | null;
            if (!target) return;

            // First, try to find closest element with data-nav or data-call (opt-in declarative)
            const optInEl = target.closest?.('[data-nav], [data-call]');
            if (optInEl && root.contains(optInEl)) {
                event.preventDefault();
                const name = (optInEl.getAttribute('data-nav') || optInEl.getAttribute('data-call'))!;
                const kind = optInEl.hasAttribute('data-call') ? 'button' : 'link';
                onNav({ kind, name, el: optInEl });
                return;
            }

            // Fallback: handle links with href (legacy behavior, but simplified)
            if (target instanceof HTMLAnchorElement && target.href) {
                // Skip download links
                if (target.hasAttribute('download')) return;
                
                event.preventDefault();
                // Extract path from href, removing leading slashes
                const url = new URL(target.href, window.location.href);
                const name = url.pathname.replace(/^\/+/, '') || 'index';
                onNav({ kind: 'link', name, el: target });
                return;
            }

            // Fallback: handle buttons with formaction (legacy behavior, but simplified)
            const button = target.closest?.('button[type="submit"], input[type="submit"]');
            if (button && root.contains(button)) {
                const form = button.closest('form') as HTMLFormElement | null;
                if (!form) return;

                const formAction = (button as HTMLElement).getAttribute('formaction');
                // Only proceed if we have a formaction to handle
                if (!formAction) return;
                
                event.preventDefault();
                
                // Create URL from formaction, with fallback to form action or current location
                const url = new URL(formAction || form.action || window.location.href, window.location.href);
                const name = url.pathname.replace(/^\/+/, '') || 'index';
                const formData = new FormData(form, button as HTMLButtonElement | HTMLInputElement);
                
                onNav({ kind: 'form', name, el: form, data: formData });
            }
        };

        // Submit handler for forms
        submitHandler = function (event: SubmitEvent) {
            const form = event.target as HTMLFormElement;
            
            // Opt-in declarative forms with data-nav
            if (form.hasAttribute('data-nav')) {
                event.preventDefault();
                const name = form.getAttribute('data-nav')!;
                const formData = new FormData(form, (event as any).submitter ?? undefined);
                onNav({ kind: 'form', name, el: form, data: formData });
            }
        };

        root.addEventListener("click", clickHandler);
        root.addEventListener("submit", submitHandler);
    }

    return {
        __name__: new pyStr("drafter.bridge.client"),
        load_page,
    };
}
