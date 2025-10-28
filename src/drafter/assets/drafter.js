"use strict";
var Drafter = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.ts
  var src_exports = {};
  __export(src_exports, {
    startDrafter: () => startDrafter
  });

  // src/types/skulpt/index.ts
  var {
    builtin: {
      bool: { true$: pyTrue, false$: pyFalse },
      none: { none$: pyNone },
      NotImplemented: { NotImplemented$: pyNotImplemented },
      bool: pyBool,
      bytes: pyBytes,
      dict: pyDict,
      float_: pyFloat,
      frozenset: pyFrozenSet,
      func: pyFunc,
      int_: pyInt,
      list: pyList,
      none: pyNoneType,
      mappingproxy: pyMappingProxy,
      module: pyModule,
      object: pyObject,
      set: pySet,
      slice: pySlice,
      sk_method: pyBuiltinFunctionOrMethod,
      str: pyStr,
      tuple: pyTuple,
      type: pyType,
      classmethod: pyClassMethod,
      staticmethod: pyStaticMethod,
      property: pyProperty,
      BaseException: pyBaseException,
      SystemExit: pySystemExit,
      KeyboardInterrupt: pyKeyboardInterrupt,
      GeneratorExit: pyGeneratorExit,
      Exception: pyException,
      StopIteration: pyStopIteration,
      StopAsyncIteration: pyStopAsyncIteration,
      ArithmeticError: pyArithmeticError,
      FloatingPointError: pyFloatingPointError,
      OverflowError: pyOverflowError,
      ZeroDivisionError: pyZeroDivisionError,
      AssertionError: pyAssertionError,
      AttributeError: pyAttributeError,
      BufferError: pyBufferError,
      EOFError: pyEOFError,
      ImportError: pyImportError,
      ModuleNotFoundError: pyModuleNotFoundError,
      LookupError: pyLookupError,
      IndexError: pyIndexError,
      KeyError: pyKeyError,
      MemoryError: pyMemoryError,
      NameError: pyNameError,
      UnboundLocalError: pyUnboundLocalError,
      OSError: pyOSError,
      FileNotFoundError: pyFileNotFoundError,
      TimeoutError: pyTimeoutError,
      ReferenceError: pyReferenceError,
      RuntimeError: pyRuntimeError,
      NotImplementedError: pyNotImplementedError,
      RecursionError: pyRecursionError,
      SyntaxError: pySyntaxError,
      IndentationError: pyIndentationError,
      TabError: pyTabError,
      SystemError: pySystemError,
      TypeError: pyTypeError,
      ValueError: pyValueError,
      UnicodeError: pyUnicodeError,
      UnicodeDecodeError: pyUnicodeDecodeError,
      UnicodeEncodeError: pyUnicodeEncodeError,
      ExternalError: pyExternalError,
      checkString,
      checkBool,
      checkInt,
      checkAnySet,
      checkBytes,
      checkCallable,
      checkIterable,
      checkNone,
      issubclass: pyIsSubclass,
      isinstance: pyIsInstance,
      hasattr: pyHasAttr
    },
    misceval: {
      isTrue,
      Suspension,
      Break,
      chain: chainOrSuspend,
      tryCatch: tryCatchOrSuspend,
      retryOptionalSuspensionOrThrow,
      objectRepr,
      buildClass: buildPyClass,
      iterFor: iterForOrSuspend,
      iterArray,
      richCompareBool,
      callsimArray: pyCall,
      callsimOrSuspendArray: pyCallOrSuspend,
      arrayFromIterable,
      asyncToPromise: suspensionToPromise,
      promiseToSuspension
    },
    abstr: {
      buildNativeClass,
      copyKeywordsToNamedArgs,
      checkArgsLen,
      checkNoArg,
      checkNoKwargs,
      checkOneArg,
      keywordArrayFromPyDict,
      keywordArrayToPyDict,
      iter: pyIter,
      lookupSpecial,
      typeLookup,
      setUpModuleMethods
    },
    ffi: { toPy, toJs, proxy }
  } = Sk;
  var skulpt_default = Sk;

  // src/skulpt-tools.ts
  function builtinRead(path) {
    if (skulpt_default.builtinFiles === void 0 || skulpt_default.builtinFiles["files"][path] === void 0)
      throw "File not found: '" + path + "'";
    return skulpt_default.builtinFiles["files"][path];
  }
  var preStyle = `background-color: #f0f0f0; padding: 4px; border: 1px solid lightgrey; margin: 0px`;
  function setupSkulpt(root = "#website") {
    if (typeof skulpt_default === "undefined") {
      console.error(
        "Skulpt (global `Sk`) not found. Ensure skulpt.js and skulpt-stdlib.js are loaded before drafter.js (served from your Python assets or a CDN)."
      );
      throw new Error("Skulpt not found");
    }
    console.log(skulpt_default);
    if (typeof skulpt_default.environ == "undefined") {
      skulpt_default.environ = new skulpt_default.builtin.dict();
    }
    skulpt_default.environ.set$item(
      new skulpt_default.builtin.str("DRAFTER_SKULPT"),
      skulpt_default.builtin.bool.true$
    );
    skulpt_default.configure({
      read: builtinRead,
      __future__: skulpt_default.python3
    });
    skulpt_default.inBrowser = false;
    if (typeof skulpt_default.console === "undefined") {
      skulpt_default.console = {};
    }
    skulpt_default.console.drafter = {};
    skulpt_default.console.printPILImage = function(tag) {
      document.body.append(tag.image);
    };
    skulpt_default.console.plot = function(chart) {
      let container = document.createElement("div");
      document.body.append(container);
      return { html: [container] };
    };
    skulpt_default.console.getWidth = function() {
      return 300;
    };
    skulpt_default.console.getHeight = function() {
      return 300;
    };
    skulpt_default.console.drafter.handleError = function(code, message) {
      document.body.innerHTML = `<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div><pre style="${preStyle}">${code}: ${message}</pre></div>`;
    };
    void skulpt_default;
  }
  async function startServer(pythonCode, mainFilename = "main") {
    try {
      return skulpt_default.misceval.asyncToPromise(() => {
        return skulpt_default.importMainWithBody(
          mainFilename,
          false,
          pythonCode,
          true
        );
      }).then((result) => {
        console.log(result.$d);
        return result;
      }).catch((error) => {
        showError(error, mainFilename + ".py", pythonCode);
      });
    } catch (error) {
      showError(error, mainFilename + ".py", pythonCode);
    }
  }
  function showError(err, filenameExecuted, code) {
    console.error(err);
    console.error(err.args.v[0].v);
    document.body.innerHTML = [
      "<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div>",
      presentRunError(err, filenameExecuted, code),
      "</div>"
    ].join("\n");
  }
  function presentRunError(error, filenameExecuted, code) {
    let label = error.tp$name;
    let category = "runtime";
    let message = convertSkulptError(error, filenameExecuted, code);
    return message;
  }
  function buildTraceback(error, filenameExecuted, code) {
    return error.traceback.reverse().map((frame) => {
      if (!frame) {
        return "??";
      }
      let lineno = frame.lineno;
      let file = `File <code class="filename">"${frame.filename}"</code>, `;
      let line = `on line <code class="lineno">${lineno}</code>, `;
      let scope = frame.scope !== "<module>" && frame.scope !== void 0 ? `in scope ${frame.scope}` : "";
      let source = "";
      console.log(filenameExecuted, frame.filename, code);
      if (frame.source !== void 0) {
        source = `
<pre style="${preStyle}"><code>${frame.source}</code></pre>`;
      } else if (filenameExecuted === frame.filename && code) {
        const lines = code.split("\n");
        const lineIndex = lineno - 1;
        const lineContent = lines[lineIndex];
        source = `
<pre style="${preStyle}"><code>${lineContent}</code></pre>`;
      }
      return file + line + scope + source;
    });
  }
  function convertSkulptError(error, filenameExecuted, code) {
    let name = error.tp$name;
    let args = skulpt_default.ffi.remapToJs(error.args);
    let top = `${name}: ${args[0]}`;
    let traceback = "";
    if (name === "TimeoutError") {
      if (error.err && error.err.traceback && error.err.traceback.length) {
        const allFrames = buildTraceback(error.err, filenameExecuted, code);
        const result = ["Traceback:"];
        if (allFrames.length > 5) {
          result.push(
            ...allFrames.slice(0, 3),
            `... Hiding ${allFrames.length - 3} other stack frames ...,`,
            ...allFrames.slice(-3, -2)
          );
        } else {
          result.push(...allFrames);
        }
        traceback = result.join("\n<br>");
      }
    } else if (error.traceback && error.traceback.length) {
      traceback = "<strong>Traceback:</strong><br>\n" + buildTraceback(error, filenameExecuted, code).join("\n<br>");
    }
    return `<pre style="${preStyle}">${top}</pre>
<br>
${traceback}
<br>
<div>
    <p><strong>Advice:</strong><br>
    Some common things to check:
    <ul>
    <li>Check your site to make sure it has no errors and runs fine when not deployed.</li>
    <li>Make sure you are not using third party libraries or modules that are not supported (e.g., <code>threading</code>).</li>
    <li>Check that you are correctly referencing any files or images you are using.</li>
    </ul>
    </p>
    </div>`;
  }

  // src/index.ts
  var x = new Sk.builtin.str("hello");
  function startDrafter(options) {
    setupSkulpt();
    const targetElement = typeof options.target === "string" ? document.querySelector(options.target) : options.target;
    if (!targetElement) {
      throw new Error("Target element not found");
    }
    if (options.code) {
      return startServer(options.code, "main");
    } else if (options.url) {
      return fetch(options.url).then((response) => {
        if (!response.ok) {
          throw new Error(
            "Network response was not ok " + response.statusText
          );
        }
        return response.text();
      }).then((contents) => {
        return startServer(contents, "main");
      });
    } else {
      throw new Error("Either code or url must be provided");
    }
    console.log("Drafter setup complete.");
  }
  return __toCommonJS(src_exports);
})();
