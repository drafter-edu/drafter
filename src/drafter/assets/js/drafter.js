var Drafter=(()=>{var m=Object.defineProperty;var w=Object.getOwnPropertyDescriptor;var $=Object.getOwnPropertyNames;var x=Object.prototype.hasOwnProperty;var I=(r,e)=>{for(var t in e)m(r,t,{get:e[t],enumerable:!0})},H=(r,e,t,n)=>{if(e&&typeof e=="object"||typeof e=="function")for(let s of $(e))!x.call(r,s)&&s!==t&&m(r,s,{get:()=>e[s],enumerable:!(n=w(e,s))||n.enumerable});return r};var B=r=>H(m({},"__esModule",{value:!0}),r);var M={};I(M,{runStudentCode:()=>F});var{builtin:{bool:{true$:R,false$:A},none:{none$:O},NotImplemented:{NotImplemented$:C},bool:j,bytes:q,dict:U,float_:W,frozenset:J,func:K,int_:V,list:z,none:G,mappingproxy:Z,module:Q,object:X,set:Y,slice:ee,sk_method:te,str:re,tuple:ne,type:se,classmethod:oe,staticmethod:ie,property:ae,BaseException:le,SystemExit:de,KeyboardInterrupt:ce,GeneratorExit:ue,Exception:pe,StopIteration:ye,StopAsyncIteration:ge,ArithmeticError:me,FloatingPointError:he,OverflowError:be,ZeroDivisionError:ve,AssertionError:Ee,AttributeError:fe,BufferError:Se,EOFError:ke,ImportError:Te,ModuleNotFoundError:we,LookupError:$e,IndexError:xe,KeyError:Ie,MemoryError:He,NameError:Be,UnboundLocalError:_e,OSError:Le,FileNotFoundError:Pe,TimeoutError:De,ReferenceError:Fe,RuntimeError:Me,NotImplementedError:Ne,RecursionError:Re,SyntaxError:Ae,IndentationError:Oe,TabError:Ce,SystemError:je,TypeError:qe,ValueError:Ue,UnicodeError:We,UnicodeDecodeError:Je,UnicodeEncodeError:Ke,ExternalError:Ve,checkString:ze,checkBool:Ge,checkInt:Ze,checkAnySet:Qe,checkBytes:Xe,checkCallable:Ye,checkIterable:et,checkNone:tt,issubclass:rt,isinstance:nt,hasattr:st},misceval:{isTrue:ot,Suspension:it,Break:at,chain:lt,tryCatch:dt,retryOptionalSuspensionOrThrow:ct,objectRepr:ut,buildClass:pt,iterFor:yt,iterArray:gt,richCompareBool:mt,callsimArray:ht,callsimOrSuspendArray:bt,arrayFromIterable:vt,asyncToPromise:Et,promiseToSuspension:ft},abstr:{buildNativeClass:St,copyKeywordsToNamedArgs:kt,checkArgsLen:Tt,checkNoArg:wt,checkNoKwargs:$t,checkOneArg:xt,keywordArrayFromPyDict:It,keywordArrayToPyDict:Ht,iter:Bt,lookupSpecial:_t,typeLookup:Lt,setUpModuleMethods:Pt},ffi:{toPy:Dt,toJs:Ft,proxy:Mt}}=Sk,o=Sk;function _(r){if(o.builtinFiles===void 0||o.builtinFiles.files[r]===void 0)throw"File not found: '"+r+"'";return o.builtinFiles.files[r]}var p="background-color: #f0f0f0; padding: 4px; border: 1px solid lightgrey; margin: 0px";function T(){if(typeof o>"u")throw console.error("Skulpt (global `Sk`) not found. Ensure skulpt.js and skulpt-stdlib.js are loaded before drafter.js (served from your Python assets or a CDN)."),new Error("Skulpt not found");typeof o.environ>"u"&&(o.environ=new o.builtin.dict),o.environ.set$item(new o.builtin.str("DRAFTER_SKULPT"),o.builtin.bool.true$),o.configure({read:_,__future__:o.python3}),o.inBrowser=!1,typeof o.console>"u"&&(o.console={}),o.console.drafter={},o.console.printPILImage=function(r){document.body.append(r.image)},o.console.plot=function(r){let e=document.createElement("div");return document.body.append(e),{html:[e]}},o.console.getWidth=function(){return 300},o.console.getHeight=function(){return 300},o.console.drafter.handleError=function(r,e){document.body.innerHTML=`<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div><pre style="${p}">${r}: ${e}</pre></div>`}}async function b(r,e="main",t=!0){try{return o.misceval.asyncToPromise(()=>o.importMainWithBody(e,!1,r,!0)).then(n=>(console.log(n.$d),n)).catch(n=>{if(!t)throw h(n,e+".py",r,!1);f(n,e+".py",r)})}catch(n){if(!t)throw h(n,e+".py",r,!1);f(n,e+".py",r)}}function f(r,e,t){console.error(r),console.error(r.args.v[0].v),document.body.innerHTML=["<h1>Error Running Site!</h1><div>There was an error running your site. Here is the error message:</div><div>",L(r,e,t),"</div>"].join(`
`)}function L(r,e,t){let n=r.tp$name,s="runtime";return h(r,e,t)}function S(r,e,t){return r.traceback.reverse().map(n=>{if(!n)return"??";let s=n.lineno,a=`File <code class="filename">"${n.filename}"</code>, `,i=`on line <code class="lineno">${s}</code>, `,d=n.scope!=="<module>"&&n.scope!==void 0?`in scope ${n.scope}`:"",l="";if(n.source!==void 0)l=`
<pre style="${p}"><code>${n.source}</code></pre>`;else if(e===n.filename&&t){let c=t.split(`
`),g=s-1,E=c[g];l=`
<pre style="${p}"><code>${E}</code></pre>`}return a+i+d+l})}function k(r,e,t){return r.traceback.reverse().map(n=>{if(!n)return"??";let s=n.lineno,a=`File "${n.filename}", `,i=`on line ${s}, `,d=n.scope!=="<module>"&&n.scope!==void 0?`in scope ${n.scope}`:"",l="";if(n.source!==void 0)l=""+n.source;else if(e===n.filename&&t){let c=t.split(`
`),g=s-1;l=c[g]}return a+i+d+l})}function h(r,e,t,n=!0){let s=r.tp$name,a=o.ffi.remapToJs(r.args),i=`${s}: ${a[0]}`,d="";if(s==="TimeoutError"){if(r.err&&r.err.traceback&&r.err.traceback.length){let l=(n?S:k)(r.err,e,t),c=["Traceback:"];l.length>5?c.push(...l.slice(0,3),`... Hiding ${l.length-3} other stack frames ...,`,...l.slice(-3,-2)):c.push(...l),d=c.join(`
<br>`)}}else r.traceback&&r.traceback.length&&(d=(n?`<strong>Traceback:</strong><br>
`:`Traceback:
`)+(n?S:k)(r,e,t).join(`
<br>`));return n?`<pre style="${p}">${i}</pre>
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
    </div>`:i+`
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
        `,e}attachEventHandlers(){let e=document.getElementById("debug-toggle-btn");e&&e.addEventListener("click",()=>this.toggleVisibility());let t=document.getElementById("debug-reset-btn");t&&t.addEventListener("click",()=>this.resetState());let n=document.getElementById("debug-about-btn");n&&n.addEventListener("click",()=>this.navigateToAbout());let s=document.getElementById("debug-save-state-btn");s&&s.addEventListener("click",()=>this.saveStateToLocalStorage());let a=document.getElementById("debug-load-state-btn");a&&a.addEventListener("click",()=>this.loadStateFromLocalStorage());let i=document.getElementById("debug-download-state-btn");i&&i.addEventListener("click",()=>this.downloadState());let d=document.getElementById("debug-upload-state-btn");d&&d.addEventListener("click",()=>this.uploadState())}handleTelemetryEvent(e){switch(this.events.push(e),!0){case e.event_type.startsWith("route."):this.handleRouteEvent(e);break;case e.event_type.startsWith("request."):this.handleRequestEvent(e);break;case e.event_type.startsWith("response."):this.handleResponseEvent(e);break;case e.event_type.startsWith("outcome."):this.handleOutcomeEvent(e);break;case e.event_type.startsWith("state."):this.handleStateEvent(e);break;case e.event_type.startsWith("logger.error"):this.handleErrorEvent(e);break;case e.event_type.startsWith("logger.warning"):this.handleWarningEvent(e);break;default:this.updateEventsSection()}this.render()}handleRouteEvent(e){e.event_type==="route.added"&&this.routes.set(e.data?.path||"unknown",e.data)}handleRequestEvent(e){e.event_type==="request.visit"&&(this.updateCurrentRouteSection(e.data),this.pageHistory.push({type:"request",timestamp:e.timestamp,data:e.data,request_id:e.correlation.request_id}))}handleResponseEvent(e){if(e.event_type==="response.created"&&e.data){let t=this.pageHistory.findIndex(n=>n.type==="request"&&n.request_id===e.correlation.request_id);t>=0?this.pageHistory[t]={...this.pageHistory[t],response:e.data,duration_ms:e.data.duration_ms}:this.pageHistory.push({type:"response",timestamp:e.timestamp,data:e.data,request_id:e.correlation.request_id,response_id:e.correlation.response_id})}}handleOutcomeEvent(e){e.data&&this.pageHistory.push({type:"outcome",timestamp:e.timestamp,data:e.data})}handleStateEvent(e){e.event_type==="state.updated"&&(this.currentState=e.data)}handleErrorEvent(e){this.errors.push(e)}handleWarningEvent(e){this.warnings.push(e)}render(){this.contentElement&&(this.renderErrors(),this.renderWarnings(),this.renderCurrentRoute(),this.renderState(),this.renderHistory(),this.renderRoutes(),this.renderEvents())}renderErrors(){let e=document.getElementById("debug-errors");if(e){if(this.errors.length===0){e.style.display="none";return}e.style.display="block",e.innerHTML=`
            <h4>\u274C Errors (${this.errors.length})</h4>
            <div class="debug-messages">
                ${this.errors.slice(-10).map(t=>`
                    <div class="debug-message error-message">
                        <div class="message-header">${this.escapeHtml(t.data?.message||"Unknown error")}</div>
                        <div class="message-meta">
                            <span class="message-source">${this.escapeHtml(t.source)}</span>
                            <span class="message-time">${new Date(t.timestamp).toLocaleTimeString()}</span>
                        </div>
                        ${t.data?.details?`
                            <details>
                                <summary>Details</summary>
                                <pre>${this.escapeHtml(t.data.details)}</pre>
                            </details>
                        `:""}
                    </div>
                `).join("")}
            </div>
        `}}renderWarnings(){let e=document.getElementById("debug-warnings");if(e){if(this.warnings.length===0){e.style.display="none";return}e.style.display="block",e.innerHTML=`
            <h4>\u26A0\uFE0F Warnings (${this.warnings.length})</h4>
            <div class="debug-messages">
                ${this.warnings.slice(-10).map(t=>`
                    <div class="debug-message warning-message">
                        <div class="message-header">${this.escapeHtml(t.data?.message||"Unknown warning")}</div>
                        <div class="message-meta">
                            <span class="message-source">${this.escapeHtml(t.source)}</span>
                            <span class="message-time">${new Date(t.timestamp).toLocaleTimeString()}</span>
                        </div>
                    </div>
                `).join("")}
            </div>
        `}}renderCurrentRoute(){let e=document.getElementById("debug-current-route");e&&(e.innerHTML=`
            <details open>
                <summary><h4>\u{1F5FA}\uFE0F Current Route</h4></summary>
                <div class="route-info">
                    <p><strong>Route:</strong> ${this.escapeHtml(String(this.events.find(t=>t.event_type==="request.visit")?.correlation.route||"None"))}</p>
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
                            ${this.pageHistory.slice(-20).reverse().map((t,n)=>{let s=t.data?.url||t.data?.route||"unknown",a=t.duration_ms?`${t.duration_ms.toFixed(1)}ms`:"",i=t.response?`<span class="status-badge status-${t.response.status_code>=400?"error":"ok"}">${t.response.status_code}</span>`:"";return`
                                    <li class="history-item">
                                        <span class="history-index">#${this.pageHistory.length-n}</span>
                                        <span class="history-route">${this.escapeHtml(s)}</span>
                                        ${a?`<span class="history-duration">${a}</span>`:""}
                                        ${i}
                                        <span class="history-time">${new Date(t.timestamp).toLocaleTimeString()}</span>
                                        ${t.data?`
                                            <details class="history-details">
                                                <summary>Details</summary>
                                                <pre>${this.escapeHtml(JSON.stringify(t.data,null,2))}</pre>
                                            </details>
                                        `:""}
                                    </li>
                                `}).join("")}
                        </ul>
                    `}
                </div>
            </details>
        `)}renderRoutes(){let e=document.getElementById("debug-routes");if(!e)return;let t=Array.from(this.routes.entries());e.innerHTML=`
            <details>
                <summary><h4>\u{1F6E3}\uFE0F Available Routes (${t.length})</h4></summary>
                <div class="routes-content">
                    ${t.length===0?"<p>No routes registered</p>":`
                        <ul class="routes-list">
                            ${t.map(([n,s])=>`
                                <li class="route-item">
                                    <code>${this.escapeHtml(n)}</code>
                                    ${s?.function_name?` \u2192 <code>${this.escapeHtml(s.function_name)}</code>`:""}
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
                        ${this.events.slice(-50).reverse().map((t,n)=>`
                            <li class="event-item">
                                <span class="event-index">#${this.events.length-n}</span>
                                <span class="event-type">${this.escapeHtml(t.event_type)}</span>
                                <span class="event-source">${this.escapeHtml(t.source)}</span>
                                <span class="event-time">${new Date(t.timestamp).toLocaleTimeString()}</span>
                            </li>
                        `).join("")}
                    </ul>
                </div>
            </details>
        `)}updateEventsSection(){}updateCurrentRouteSection(e){}toggleVisibility(){this.isVisible=!this.isVisible,this.contentElement&&(this.contentElement.style.display=this.isVisible?"block":"none")}resetState(){console.log("[Debug Panel] Reset state requested"),window.location.href=window.location.pathname}navigateToAbout(){console.log("[Debug Panel] Navigate to About")}saveStateToLocalStorage(){try{localStorage.setItem("drafter-debug-state",JSON.stringify(this.currentState)),console.log("[Debug Panel] State saved to localStorage")}catch(e){console.error("[Debug Panel] Failed to save state:",e)}}loadStateFromLocalStorage(){try{let e=localStorage.getItem("drafter-debug-state");e&&(this.currentState=JSON.parse(e),this.render(),console.log("[Debug Panel] State loaded from localStorage"))}catch(e){console.error("[Debug Panel] Failed to load state:",e)}}downloadState(){try{let e=JSON.stringify(this.currentState,null,2),t="data:application/json;charset=utf-8,"+encodeURIComponent(e),n=`drafter-state-${Date.now()}.json`,s=document.createElement("a");s.setAttribute("href",t),s.setAttribute("download",n),s.click()}catch(e){console.error("[Debug Panel] Failed to download state:",e)}}uploadState(){let e=document.createElement("input");e.type="file",e.accept=".json",e.onchange=t=>{let n=t.target.files?.[0];if(n){let s=new FileReader;s.onload=a=>{try{let i=a.target?.result;this.currentState=JSON.parse(i),this.render(),console.log("[Debug Panel] State loaded from file")}catch(i){console.error("[Debug Panel] Failed to parse state file:",i)}},s.readAsText(n)}},e.click()}escapeHtml(e){let t=document.createElement("div");return t.textContent=e,t.innerHTML}};var u=null;function v(r="drafter-debug--"){return u||(u=new y(r)),u}function P(){return u}function D(r){if(!u){console.warn("[Debug Panel] Not initialized yet");return}try{let e={event_type:r.event_type||"unknown",correlation:r.correlation||{},source:r.source||"unknown",id:r.id||-1,version:r.version||"0.0.1",level:r.level||"info",timestamp:r.timestamp||new Date().toISOString(),data:r.data};u.handleTelemetryEvent(e)}catch(e){console.error("[Debug Panel] Error handling telemetry:",e,r)}}typeof window<"u"&&(window.DrafterDebugPanel={init:v,get:P,handleTelemetry:D});var Kt=new Sk.builtin.str("hello");function F(r){if(T(),v("drafter-debug--"),r.code)return b(r.code,"main",r.presentErrors);if(r.url)return fetch(r.url).then(e=>{if(!e.ok)throw new Error("Network response was not ok "+e.statusText);return e.text()}).then(e=>b(e,"main"));throw new Error("Either code or url must be provided");console.log("Drafter setup complete.")}return B(M);})();
//# sourceMappingURL=drafter.js.map