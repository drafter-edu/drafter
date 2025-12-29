/**
 * Skulpt module that provides a Python-accessible interface to JavaScript's
 * window and document objects. This module mimics Pyodide's js package to
 * enable cross-runtime compatibility.
 *
 * This module provides access to:
 * - js.window: Window object with methods like scrollTo()
 * - js.document: Document object with DOM manipulation methods
 * - js.scrollX, js.scrollY: Scroll position properties
 * - js.FormData: FormData class wrapper
 */

function $builtinmodule(name: string) {
    const js_mod: Record<string, any> = {};

    return Sk.misceval.chain(
        Sk.importModule("document", false, true),
        (document_mod) => {
            // Import the document module for reuse
            js_mod._document_mod = document_mod;
            return js_mod;
        },
        () => js_module(js_mod)
    );
}

function js_module(js_mod: Record<string, any>) {
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
        },

        abstr: {
            buildNativeClass,
            checkNoKwargs,
            checkArgsLen,
            checkOneArg,
            setUpModuleMethods,
        },
        misceval: {
            richCompareBool,
            chain: chainOrSuspend,
            callsimArray: pyCall,
            callsimOrSuspendArray: pyCallOrSuspend,
        },
    } = Sk;

    js_mod.__name__ = new pyStr("js");

    // FormData class wrapper
    const FormDataClass = function FormDataClass($gbl: any, $loc: any) {
        $loc.__init__ = new pyFunc(function (self: any) {
            self._formData = new FormData();
            return pyNone;
        });

        $loc.__getitem__ = new pyFunc(function (self: any, key: any) {
            const keyStr = Sk.ffi.remapToJs(key);
            const value = self._formData.get(keyStr);
            return value ? Sk.ffi.remapToPy(value) : pyNone;
        });

        $loc.__setitem__ = new pyFunc(function (self: any, key: any, value: any) {
            const keyStr = Sk.ffi.remapToJs(key);
            const valueJs = Sk.ffi.remapToJs(value);
            self._formData.set(keyStr, valueJs);
            return pyNone;
        });

        $loc.append = new pyFunc(function (self: any, key: any, value: any) {
            const keyStr = Sk.ffi.remapToJs(key);
            const valueJs = Sk.ffi.remapToJs(value);
            self._formData.append(keyStr, valueJs);
            return pyNone;
        });

        $loc.delete = new pyFunc(function (self: any, key: any) {
            const keyStr = Sk.ffi.remapToJs(key);
            self._formData.delete(keyStr);
            return pyNone;
        });

        $loc.get = new pyFunc(function (self: any, key: any) {
            const keyStr = Sk.ffi.remapToJs(key);
            const value = self._formData.get(keyStr);
            return value ? Sk.ffi.remapToPy(value) : pyNone;
        });

        $loc.has = new pyFunc(function (self: any, key: any) {
            const keyStr = Sk.ffi.remapToJs(key);
            return self._formData.has(keyStr) ? Sk.builtin.bool.true$ : Sk.builtin.bool.false$;
        });
    };

    js_mod.FormData = Sk.misceval.buildClass(js_mod, FormDataClass, "FormData", []);

    // Create a proxy wrapper that allows Python code to access JS object properties
    // This wrapper converts between Python and JavaScript types automatically
    function createJSObjectProxy(jsObject: any, proxyName: string): any {
        const ProxyClass = function ($gbl: any, $loc: any) {
            $loc.__init__ = new pyFunc(function (self: any) {
                self._jsObject = jsObject;
                return pyNone;
            });

            $loc.__getattr__ = new pyFunc(function (self: any, name: any) {
                const nameStr = Sk.ffi.remapToJs(name);
                const value = self._jsObject[nameStr];

                if (value === undefined) {
                    throw new Sk.builtin.AttributeError(
                        `'${proxyName}' object has no attribute '${nameStr}'`
                    );
                }

                // If it's a function, wrap it
                if (typeof value === "function") {
                    return new pyFunc(function (...args: any[]) {
                        const jsArgs = args.map((arg) => {
                            // Keep 'self' out of args when calling
                            if (arg === self) return undefined;
                            return Sk.ffi.remapToJs(arg);
                        }).filter(arg => arg !== undefined);

                        const result = value.apply(self._jsObject, jsArgs);

                        // Convert result back to Python
                        if (result === undefined || result === null) {
                            return pyNone;
                        }
                        
                        // Handle DOM elements - wrap them in a proxy too
                        if (result instanceof HTMLElement || result instanceof Element) {
                            return createDOMElementProxy(result);
                        }
                        
                        // Handle NodeList and HTMLCollection
                        if (result instanceof NodeList || result instanceof HTMLCollection) {
                            const pyList_result = new pyList([]);
                            for (let i = 0; i < result.length; i++) {
                                pyList_result.v.push(createDOMElementProxy(result[i]));
                            }
                            return pyList_result;
                        }
                        
                        // Handle Range objects
                        if (result instanceof Range) {
                            return createRangeProxy(result);
                        }

                        return Sk.ffi.remapToPy(result);
                    });
                }

                // If it's a primitive, convert it
                return Sk.ffi.remapToPy(value);
            });

            $loc.__setattr__ = new pyFunc(function (self: any, name: any, value: any) {
                const nameStr = Sk.ffi.remapToJs(name);
                if (nameStr.startsWith('_')) {
                    // Allow setting internal attributes
                    self[nameStr] = value;
                } else {
                    self._jsObject[nameStr] = Sk.ffi.remapToJs(value);
                }
                return pyNone;
            });
        };

        const proxyInstance = Sk.misceval.buildClass(js_mod, ProxyClass, proxyName, []);
        return Sk.misceval.callsimArray(proxyInstance, []);
    }

    // Create a proxy for DOM elements
    function createDOMElementProxy(element: Element | HTMLElement | null): any {
        if (!element) return pyNone;

        const ElementProxyClass = function ($gbl: any, $loc: any) {
            $loc.__init__ = new pyFunc(function (self: any) {
                self._element = element;
                return pyNone;
            });

            $loc.__getattr__ = new pyFunc(function (self: any, name: any) {
                const nameStr = Sk.ffi.remapToJs(name);
                const value = (self._element as any)[nameStr];

                if (value === undefined) {
                    throw new Sk.builtin.AttributeError(
                        `'Element' object has no attribute '${nameStr}'`
                    );
                }

                // If it's a function, wrap it
                if (typeof value === "function") {
                    return new pyFunc(function (...args: any[]) {
                        const jsArgs = args.map((arg) => {
                            if (arg === self) return undefined;
                            
                            // Handle DocumentFragment and other special types
                            if (arg._fragment !== undefined) {
                                return arg._fragment;
                            }
                            if (arg._element !== undefined) {
                                return arg._element;
                            }
                            
                            return Sk.ffi.remapToJs(arg);
                        }).filter(arg => arg !== undefined);

                        const result = value.apply(self._element, jsArgs);

                        if (result === undefined || result === null) {
                            return pyNone;
                        }
                        
                        if (result instanceof HTMLElement || result instanceof Element) {
                            return createDOMElementProxy(result);
                        }
                        
                        if (result instanceof NodeList || result instanceof HTMLCollection) {
                            const pyList_result = new pyList([]);
                            for (let i = 0; i < result.length; i++) {
                                pyList_result.v.push(createDOMElementProxy(result[i]));
                            }
                            return pyList_result;
                        }

                        return Sk.ffi.remapToPy(result);
                    });
                }

                return Sk.ffi.remapToPy(value);
            });

            $loc.__setattr__ = new pyFunc(function (self: any, name: any, value: any) {
                const nameStr = Sk.ffi.remapToJs(name);
                if (nameStr.startsWith('_')) {
                    self[nameStr] = value;
                } else {
                    (self._element as any)[nameStr] = Sk.ffi.remapToJs(value);
                }
                return pyNone;
            });
        };

        const proxyInstance = Sk.misceval.buildClass(js_mod, ElementProxyClass, "Element", []);
        return Sk.misceval.callsimArray(proxyInstance, []);
    }

    // Create a proxy for Range objects
    function createRangeProxy(range: Range): any {
        const RangeProxyClass = function ($gbl: any, $loc: any) {
            $loc.__init__ = new pyFunc(function (self: any) {
                self._range = range;
                return pyNone;
            });

            $loc.selectNode = new pyFunc(function (self: any, node: any) {
                const nodeElement = node._element;
                self._range.selectNode(nodeElement);
                return pyNone;
            });

            $loc.createContextualFragment = new pyFunc(function (self: any, htmlString: any) {
                const htmlStr = Sk.ffi.remapToJs(htmlString);
                const fragment = self._range.createContextualFragment(htmlStr);
                
                // Return a proxy for the fragment
                const FragmentProxyClass = function ($gbl: any, $loc: any) {
                    $loc.__init__ = new pyFunc(function (fragmentSelf: any) {
                        fragmentSelf._fragment = fragment;
                        return pyNone;
                    });
                };
                
                const fragmentProxy = Sk.misceval.buildClass(js_mod, FragmentProxyClass, "DocumentFragment", []);
                return Sk.misceval.callsimArray(fragmentProxy, []);
            });
        };

        const proxyInstance = Sk.misceval.buildClass(js_mod, RangeProxyClass, "Range", []);
        return Sk.misceval.callsimArray(proxyInstance, []);
    }

    // Create enhanced document proxy with special methods
    const DocumentProxyClass = function ($gbl: any, $loc: any) {
        $loc.__init__ = new pyFunc(function (self: any) {
            self._jsObject = document;
            return pyNone;
        });

        $loc.__getattr__ = new pyFunc(function (self: any, name: any) {
            const nameStr = Sk.ffi.remapToJs(name);
            const value = document[nameStr as keyof Document];

            if (value === undefined) {
                throw new Sk.builtin.AttributeError(
                    `'document' object has no attribute '${nameStr}'`
                );
            }

            // If it's a function, wrap it
            if (typeof value === "function") {
                return new pyFunc(function (...args: any[]) {
                    const jsArgs = args.map((arg) => {
                        if (arg === self) return undefined;
                        return Sk.ffi.remapToJs(arg);
                    }).filter(arg => arg !== undefined);

                    const result = (value as Function).apply(document, jsArgs);

                    if (result === undefined || result === null) {
                        return pyNone;
                    }
                    
                    if (result instanceof HTMLElement || result instanceof Element) {
                        return createDOMElementProxy(result);
                    }
                    
                    if (result instanceof NodeList || result instanceof HTMLCollection) {
                        const pyList_result = new pyList([]);
                        for (let i = 0; i < result.length; i++) {
                            pyList_result.v.push(createDOMElementProxy(result[i]));
                        }
                        return pyList_result;
                    }
                    
                    if (result instanceof Range) {
                        return createRangeProxy(result);
                    }

                    return Sk.ffi.remapToPy(result);
                });
            }

            return Sk.ffi.remapToPy(value);
        });

        $loc.__setattr__ = new pyFunc(function (self: any, name: any, value: any) {
            const nameStr = Sk.ffi.remapToJs(name);
            if (nameStr.startsWith('_')) {
                self[nameStr] = value;
            } else {
                (document as any)[nameStr] = Sk.ffi.remapToJs(value);
            }
            return pyNone;
        });
    };

    const documentProxy = Sk.misceval.buildClass(js_mod, DocumentProxyClass, "document", []);
    js_mod.document = Sk.misceval.callsimArray(documentProxy, []);

    // window proxy with scrollTo and other methods
    const WindowProxyClass = function ($gbl: any, $loc: any) {
        $loc.__init__ = new pyFunc(function (self: any) {
            self._jsObject = window;
            return pyNone;
        });

        $loc.scrollTo = new pyFunc(function (self: any, x: any, y: any) {
            const xVal = Sk.ffi.remapToJs(x);
            const yVal = Sk.ffi.remapToJs(y);
            window.scrollTo(xVal, yVal);
            return pyNone;
        });

        $loc.__getattr__ = new pyFunc(function (self: any, name: any) {
            const nameStr = Sk.ffi.remapToJs(name);
            const value = (window as any)[nameStr];

            if (value === undefined) {
                throw new Sk.builtin.AttributeError(
                    `'window' object has no attribute '${nameStr}'`
                );
            }

            if (typeof value === "function") {
                return new pyFunc(function (...args: any[]) {
                    const jsArgs = args.map((arg) => {
                        if (arg === self) return undefined;
                        return Sk.ffi.remapToJs(arg);
                    }).filter(arg => arg !== undefined);

                    const result = value.apply(window, jsArgs);
                    return result === undefined || result === null 
                        ? pyNone 
                        : Sk.ffi.remapToPy(result);
                });
            }

            return Sk.ffi.remapToPy(value);
        });
    };

    const windowProxy = Sk.misceval.buildClass(js_mod, WindowProxyClass, "window", []);
    js_mod.window = Sk.misceval.callsimArray(windowProxy, []);

    // scrollX and scrollY properties
    Object.defineProperty(js_mod, 'scrollX', {
        get: function() {
            return new pyInt(window.scrollX);
        }
    });

    Object.defineProperty(js_mod, 'scrollY', {
        get: function() {
            return new pyInt(window.scrollY);
        }
    });

    return js_mod;
}
