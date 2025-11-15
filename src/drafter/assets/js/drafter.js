var Drafter=(()=>{var m=Object.defineProperty;var w=Object.getOwnPropertyDescriptor;var $=Object.getOwnPropertyNames;var I=Object.prototype.hasOwnProperty;var x=(t,e)=>{for(var r in e)m(t,r,{get:e[r],enumerable:!0})},B=(t,e,r,n)=>{if(e&&typeof e=="object"||typeof e=="function")for(let o of $(e))!I.call(t,o)&&o!==r&&m(t,o,{get:()=>e[o],enumerable:!(n=w(e,o))||n.enumerable});return t};var H=t=>B(m({},"__esModule",{value:!0}),t);var N={};x(N,{runStudentCode:()=>F});var{builtin:{bool:{true$:A,false$:O},none:{none$:_},NotImplemented:{NotImplemented$:C},bool:j,bytes:U,dict:W,float_:J,frozenset:q,func:K,int_:V,list:z,none:G,mappingproxy:Z,module:Q,object:X,set:Y,slice:ee,sk_method:te,str:re,tuple:ne,type:oe,classmethod:ie,staticmethod:se,property:ae,BaseException:le,SystemExit:de,KeyboardInterrupt:ce,GeneratorExit:ue,Exception:pe,StopIteration:ye,StopAsyncIteration:ge,ArithmeticError:me,FloatingPointError:he,OverflowError:ve,ZeroDivisionError:be,AssertionError:Ee,AttributeError:fe,BufferError:Se,EOFError:ke,ImportError:Te,ModuleNotFoundError:we,LookupError:$e,IndexError:Ie,KeyError:xe,MemoryError:Be,NameError:He,UnboundLocalError:Le,OSError:Pe,FileNotFoundError:De,TimeoutError:Me,ReferenceError:Fe,RuntimeError:Ne,NotImplementedError:Re,RecursionError:Ae,SyntaxError:Oe,IndentationError:_e,TabError:Ce,SystemError:je,TypeError:Ue,ValueError:We,UnicodeError:Je,UnicodeDecodeError:qe,UnicodeEncodeError:Ke,ExternalError:Ve,checkString:ze,checkBool:Ge,checkInt:Ze,checkAnySet:Qe,checkBytes:Xe,checkCallable:Ye,checkIterable:et,checkNone:tt,issubclass:rt,isinstance:nt,hasattr:ot},misceval:{isTrue:it,Suspension:st,Break:at,chain:lt,tryCatch:dt,retryOptionalSuspensionOrThrow:ct,objectRepr:ut,buildClass:pt,iterFor:yt,iterArray:gt,richCompareBool:mt,callsimArray:ht,callsimOrSuspendArray:vt,arrayFromIterable:bt,asyncToPromise:Et,promiseToSuspension:ft},abstr:{buildNativeClass:St,copyKeywordsToNamedArgs:kt,checkArgsLen:Tt,checkNoArg:wt,checkNoKwargs:$t,checkOneArg:It,keywordArrayFromPyDict:xt,keywordArrayToPyDict:Bt,iter:Ht,lookupSpecial:Lt,typeLookup:Pt,setUpModuleMethods:Dt},ffi:{toPy:Mt,toJs:Ft,proxy:Nt}}=Sk,i=Sk;function L(t){if(i.builtinFiles===void 0||i.builtinFiles.files[t]===void 0)throw"File not found: '"+t+"'";return i.builtinFiles.files[t]}var p="background-color: #f0f0f0; padding: 4px; border: 1px solid lightgrey; margin: 0px";function T(){if(typeof i>"u")throw console.error("Skulpt (global `Sk`) not found. Ensure skulpt.js and skulpt-stdlib.js are loaded before drafter.js (served from your Python assets or a CDN)."),new Error("Skulpt not found");typeof i.environ>"u"&&(i.environ=new i.builtin.dict),i.environ.set$item(new i.builtin.str("DRAFTER_SKULPT"),i.builtin.bool.true$),i.configure({read:L,__future__:i.python3}),i.inBrowser=!1,typeof i.console>"u"&&(i.console={}),i.console.drafter={},i.console.printPILImage=function(t){document.body.append(t.image)},i.console.plot=function(t){let e=document.createElement("div");return document.body.append(e),{html:[e]}},i.console.getWidth=function(){return 300},i.console.getHeight=function(){return 300},i.console.drafter.handleError=function(t,e){document.body.innerHTML=`<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div><pre style="${p}">${t}: ${e}</pre></div>`}}async function v(t,e="main",r=!0){try{return i.misceval.asyncToPromise(()=>i.importMainWithBody(e,!1,t,!0)).then(n=>(console.log(n.$d),n)).catch(n=>{if(!r)throw h(n,e+".py",t,!1);f(n,e+".py",t)})}catch(n){if(!r)throw h(n,e+".py",t,!1);f(n,e+".py",t)}}function f(t,e,r){console.error(t),console.error(t.args.v[0].v),document.body.innerHTML=["<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div>",P(t,e,r),"</div>"].join(`
`)}function P(t,e,r){let n=t.tp$name,o="runtime";return h(t,e,r)}function S(t,e,r){return t.traceback.reverse().map(n=>{if(!n)return"??";let o=n.lineno,l=`File <code class="filename">"${n.filename}"</code>, `,s=`on line <code class="lineno">${o}</code>, `,d=n.scope!=="<module>"&&n.scope!==void 0?`in scope ${n.scope}`:"",a="";if(n.source!==void 0)a=`
<pre style="${p}"><code>${n.source}</code></pre>`;else if(e===n.filename&&r){let c=r.split(`
`),g=o-1,E=c[g];a=`
<pre style="${p}"><code>${E}</code></pre>`}return l+s+d+a})}function k(t,e,r){return t.traceback.reverse().map(n=>{if(!n)return"??";let o=n.lineno,l=`File "${n.filename}", `,s=`on line ${o}, `,d=n.scope!=="<module>"&&n.scope!==void 0?`in scope ${n.scope}`:"",a="";if(n.source!==void 0)a=""+n.source;else if(e===n.filename&&r){let c=r.split(`
`),g=o-1;a=c[g]}return l+s+d+a})}function h(t,e,r,n=!0){let o=t.tp$name,l=i.ffi.remapToJs(t.args),s=`${o}: ${l[0]}`,d="";if(o==="TimeoutError"){if(t.err&&t.err.traceback&&t.err.traceback.length){let a=(n?S:k)(t.err,e,r),c=["Traceback:"];a.length>5?c.push(...a.slice(0,3),`... Hiding ${a.length-3} other stack frames ...,`,...a.slice(-3,-2)):c.push(...a),d=c.join(`
<br>`)}}else t.traceback&&t.traceback.length&&(d=(n?`<strong>Traceback:</strong><br>
`:`Traceback:
`)+(n?S:k)(t,e,r).join(`
<br>`));return n?`<pre style="${p}">${s}</pre>
<br>
${d}
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
    </div>`:s+`
`+d}var y=class{constructor(e){this.containerId=e;this.initialize()}panelElement=null;contentElement=null;events=[];routes=new Map;pageHistory=[];currentState=null;errors=[];warnings=[];isVisible=!0;initialize(){let e=document.getElementById(this.containerId);if(!e){console.warn(`Debug panel container ${this.containerId} not found`);return}this.panelElement=this.createPanelStructure(),e.appendChild(this.panelElement),this.contentElement=this.panelElement.querySelector(".drafter-debug-content"),this.attachEventHandlers()}createPanelStructure(){let e=document.createElement("div");return e.className="drafter-debug-panel",e.id="drafter-debug-panel",e.innerHTML=`
            <div class="drafter-debug-header">
                <h3>\u{1F50D} Debug Monitor</h3>
                <div class="drafter-debug-actions">
                    <button id="debug-reset-btn" title="Reset state and return to index">\u{1F504} Reset</button>
                    <button id="debug-about-btn" title="Go to About page">\u2139\uFE0F About</button>
                    <button id="debug-save-state-btn" title="Save state to localStorage">\u{1F4BE} Save State</button>
                    <button id="debug-load-state-btn" title="Load state from localStorage">\u{1F4C2} Load State</button>
                    <button id="debug-download-state-btn" title="Download state as JSON">\u2B07\uFE0F Download</button>
                    <button id="debug-upload-state-btn" title="Upload state from JSON">\u2B06\uFE0F Upload</button>
                    <button id="debug-toggle-btn" title="Toggle debug panel">\u{1F441}\uFE0F</button>
                </div>
            </div>
            <div class="drafter-debug-content">
                <div class="debug-section" id="debug-errors"></div>
                <div class="debug-section" id="debug-warnings"></div>
                <div class="debug-section" id="debug-current-route"></div>
                <div class="debug-section" id="debug-state"></div>
                <div class="debug-section" id="debug-history"></div>
                <div class="debug-section" id="debug-routes"></div>
                <div class="debug-section" id="debug-events"></div>
            </div>
        `,e}attachEventHandlers(){let e=document.getElementById("debug-toggle-btn");e&&e.addEventListener("click",()=>this.toggleVisibility());let r=document.getElementById("debug-reset-btn");r&&r.addEventListener("click",()=>this.resetState());let n=document.getElementById("debug-about-btn");n&&n.addEventListener("click",()=>this.navigateToAbout());let o=document.getElementById("debug-save-state-btn");o&&o.addEventListener("click",()=>this.saveStateToLocalStorage());let l=document.getElementById("debug-load-state-btn");l&&l.addEventListener("click",()=>this.loadStateFromLocalStorage());let s=document.getElementById("debug-download-state-btn");s&&s.addEventListener("click",()=>this.downloadState());let d=document.getElementById("debug-upload-state-btn");d&&d.addEventListener("click",()=>this.uploadState())}handleTelemetryEvent(e){switch(this.events.push(e),!0){case e.event_type.startsWith("route."):this.handleRouteEvent(e);break;case e.event_type.startsWith("request."):this.handleRequestEvent(e);break;case e.event_type.startsWith("response."):this.handleResponseEvent(e);break;case e.event_type.startsWith("outcome."):this.handleOutcomeEvent(e);break;case e.event_type.startsWith("state."):this.handleStateEvent(e);break;case e.event_type.startsWith("logger.error"):this.handleErrorEvent(e);break;case e.event_type.startsWith("logger.warning"):this.handleWarningEvent(e);break;default:this.updateEventsSection()}this.render()}handleRouteEvent(e){e.event_type==="route.added"&&this.routes.set(e.data?.path||"unknown",e.data)}handleRequestEvent(e){e.event_type==="request.visit"&&this.updateCurrentRouteSection(e.data)}handleResponseEvent(e){e.data&&this.pageHistory.push({type:"response",timestamp:e.timestamp,data:e.data})}handleOutcomeEvent(e){e.data&&this.pageHistory.push({type:"outcome",timestamp:e.timestamp,data:e.data})}handleStateEvent(e){e.event_type==="state.updated"&&(this.currentState=e.data)}handleErrorEvent(e){this.errors.push(e)}handleWarningEvent(e){this.warnings.push(e)}render(){this.contentElement&&(this.renderErrors(),this.renderWarnings(),this.renderCurrentRoute(),this.renderState(),this.renderHistory(),this.renderRoutes(),this.renderEvents())}renderErrors(){let e=document.getElementById("debug-errors");if(e){if(this.errors.length===0){e.style.display="none";return}e.style.display="block",e.innerHTML=`
            <h4>\u274C Errors (${this.errors.length})</h4>
            <div class="debug-messages">
                ${this.errors.slice(-10).map(r=>`
                    <div class="debug-message error-message">
                        <div class="message-header">${this.escapeHtml(r.data?.message||"Unknown error")}</div>
                        <div class="message-meta">
                            <span class="message-source">${this.escapeHtml(r.source)}</span>
                            <span class="message-time">${new Date(r.timestamp).toLocaleTimeString()}</span>
                        </div>
                        ${r.data?.details?`
                            <details>
                                <summary>Details</summary>
                                <pre>${this.escapeHtml(r.data.details)}</pre>
                            </details>
                        `:""}
                    </div>
                `).join("")}
            </div>
        `}}renderWarnings(){let e=document.getElementById("debug-warnings");if(e){if(this.warnings.length===0){e.style.display="none";return}e.style.display="block",e.innerHTML=`
            <h4>\u26A0\uFE0F Warnings (${this.warnings.length})</h4>
            <div class="debug-messages">
                ${this.warnings.slice(-10).map(r=>`
                    <div class="debug-message warning-message">
                        <div class="message-header">${this.escapeHtml(r.data?.message||"Unknown warning")}</div>
                        <div class="message-meta">
                            <span class="message-source">${this.escapeHtml(r.source)}</span>
                            <span class="message-time">${new Date(r.timestamp).toLocaleTimeString()}</span>
                        </div>
                    </div>
                `).join("")}
            </div>
        `}}renderCurrentRoute(){let e=document.getElementById("debug-current-route");e&&(e.innerHTML=`
            <details open>
                <summary><h4>\u{1F5FA}\uFE0F Current Route</h4></summary>
                <div class="route-info">
                    <p><strong>Route:</strong> ${this.escapeHtml(String(this.events.find(r=>r.event_type==="request.visit")?.correlation.route||"None"))}</p>
                </div>
            </details>
        `)}renderState(){let e=document.getElementById("debug-state");e&&(e.innerHTML=`
            <details open>
                <summary><h4>\u{1F4CA} Current State</h4></summary>
                <div class="state-content">
                    <pre>${this.escapeHtml(JSON.stringify(this.currentState,null,2)||"null")}</pre>
                </div>
            </details>
        `)}renderHistory(){let e=document.getElementById("debug-history");e&&(e.innerHTML=`
            <details open>
                <summary><h4>\u{1F4DC} Page History (${this.pageHistory.length})</h4></summary>
                <div class="history-content">
                    ${this.pageHistory.length===0?"<p>No history yet</p>":`
                        <ul class="history-list">
                            ${this.pageHistory.slice(-20).reverse().map((r,n)=>`
                                <li class="history-item">
                                    <span class="history-index">#${this.pageHistory.length-n}</span>
                                    <span class="history-type">${r.type}</span>
                                    <span class="history-time">${new Date(r.timestamp).toLocaleTimeString()}</span>
                                </li>
                            `).join("")}
                        </ul>
                    `}
                </div>
            </details>
        `)}renderRoutes(){let e=document.getElementById("debug-routes");if(!e)return;let r=Array.from(this.routes.entries());e.innerHTML=`
            <details>
                <summary><h4>\u{1F6E3}\uFE0F Available Routes (${r.length})</h4></summary>
                <div class="routes-content">
                    ${r.length===0?"<p>No routes registered</p>":`
                        <ul class="routes-list">
                            ${r.map(([n,o])=>`
                                <li class="route-item">
                                    <code>${this.escapeHtml(n)}</code>
                                    ${o?.function_name?` \u2192 <code>${this.escapeHtml(o.function_name)}</code>`:""}
                                </li>
                            `).join("")}
                        </ul>
                    `}
                </div>
            </details>
        `}renderEvents(){let e=document.getElementById("debug-events");e&&(e.innerHTML=`
            <details>
                <summary><h4>\u{1F4CB} Recent Events (${this.events.length})</h4></summary>
                <div class="events-content">
                    <ul class="events-list">
                        ${this.events.slice(-50).reverse().map((r,n)=>`
                            <li class="event-item">
                                <span class="event-index">#${this.events.length-n}</span>
                                <span class="event-type">${this.escapeHtml(r.event_type)}</span>
                                <span class="event-source">${this.escapeHtml(r.source)}</span>
                                <span class="event-time">${new Date(r.timestamp).toLocaleTimeString()}</span>
                            </li>
                        `).join("")}
                    </ul>
                </div>
            </details>
        `)}updateEventsSection(){}updateCurrentRouteSection(e){}toggleVisibility(){this.isVisible=!this.isVisible,this.contentElement&&(this.contentElement.style.display=this.isVisible?"block":"none")}resetState(){console.log("[Debug Panel] Reset state requested"),window.location.href=window.location.pathname}navigateToAbout(){console.log("[Debug Panel] Navigate to About")}saveStateToLocalStorage(){try{localStorage.setItem("drafter-debug-state",JSON.stringify(this.currentState)),console.log("[Debug Panel] State saved to localStorage")}catch(e){console.error("[Debug Panel] Failed to save state:",e)}}loadStateFromLocalStorage(){try{let e=localStorage.getItem("drafter-debug-state");e&&(this.currentState=JSON.parse(e),this.render(),console.log("[Debug Panel] State loaded from localStorage"))}catch(e){console.error("[Debug Panel] Failed to load state:",e)}}downloadState(){try{let e=JSON.stringify(this.currentState,null,2),r="data:application/json;charset=utf-8,"+encodeURIComponent(e),n=`drafter-state-${Date.now()}.json`,o=document.createElement("a");o.setAttribute("href",r),o.setAttribute("download",n),o.click()}catch(e){console.error("[Debug Panel] Failed to download state:",e)}}uploadState(){let e=document.createElement("input");e.type="file",e.accept=".json",e.onchange=r=>{let n=r.target.files?.[0];if(n){let o=new FileReader;o.onload=l=>{try{let s=l.target?.result;this.currentState=JSON.parse(s),this.render(),console.log("[Debug Panel] State loaded from file")}catch(s){console.error("[Debug Panel] Failed to parse state file:",s)}},o.readAsText(n)}},e.click()}escapeHtml(e){let r=document.createElement("div");return r.textContent=e,r.innerHTML}};var u=null;function b(t="drafter-debug--"){return u||(u=new y(t)),u}function D(){return u}function M(t){if(!u){console.warn("[Debug Panel] Not initialized yet");return}try{let e={event_type:t.event_type||"unknown",correlation:t.correlation||{},source:t.source||"unknown",id:t.id||-1,version:t.version||"0.0.1",level:t.level||"info",timestamp:t.timestamp||new Date().toISOString(),data:t.data};u.handleTelemetryEvent(e)}catch(e){console.error("[Debug Panel] Error handling telemetry:",e,t)}}typeof window<"u"&&(window.DrafterDebugPanel={init:b,get:D,handleTelemetry:M});var Kt=new Sk.builtin.str("hello");function F(t){if(T(),b("drafter-debug--"),t.code)return v(t.code,"main",t.presentErrors);if(t.url)return fetch(t.url).then(e=>{if(!e.ok)throw new Error("Network response was not ok "+e.statusText);return e.text()}).then(e=>v(e,"main"));throw new Error("Either code or url must be provided");console.log("Drafter setup complete.")}return H(N);})();
//# sourceMappingURL=drafter.js.map