/**
 * Editable Drafter documentation demos.
 *
 * For every embedded demo (`div.drafter-demo`), a pencil button is added to
 * the top-right of the source code block shown above it. Clicking the pencil
 * swaps the highlighted (read-only) code for a plain-text editor and turns
 * the pencil into a run button. Running pushes the edited code into the
 * demo's live instance through the page's shared Drafter runtime host
 * (`window.Drafter.getHost().restart(...)`).
 */
(function () {
	"use strict";

	var PENCIL_ICON =
		'<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">' +
		'<path fill="currentColor" d="M20.71 7.04c.39-.39.39-1.04 0-1.41' +
		"l-2.34-2.34a.9959.9959 0 0 0-1.41 0l-1.84 1.83 3.75 3.75 1.84-1.83z" +
		'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/></svg>';
	var RUN_ICON =
		'<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">' +
		'<path fill="currentColor" d="M8 5v14l11-7L8 5z"/></svg>';

	/**
	 * The source block the plugin emits immediately before each demo. It is
	 * normally the directly preceding sibling, but a short backwards walk
	 * keeps this robust to markdown wrappers.
	 */
	function findSourceBlock(demo) {
		var element = demo.previousElementSibling;
		var steps = 0;
		while (element && steps < 4) {
			if (
				element.classList &&
				element.classList.contains("drafter-demo")
			) {
				return null;
			}
			if (element.classList && element.classList.contains("highlight")) {
				return element;
			}
			if (element.tagName === "PRE") {
				return element;
			}
			var inner = element.querySelector
				? element.querySelector(".highlight, pre")
				: null;
			if (inner) {
				return inner.closest(".highlight") || inner;
			}
			element = element.previousElementSibling;
			steps += 1;
		}
		return null;
	}

	function waitForInstance(host, instanceId, timeoutMs) {
		return new Promise(function (resolve) {
			var deadline = Date.now() + timeoutMs;
			(function poll() {
				if (host.has(instanceId)) {
					resolve(true);
				} else if (Date.now() > deadline) {
					resolve(false);
				} else {
					setTimeout(poll, 250);
				}
			})();
		});
	}

	function setupDemo(demo) {
		var demoId = demo.getAttribute("data-drafter-demo");
		var source = demoId ? findSourceBlock(demo) : null;
		if (!source || source.hasAttribute("data-drafter-editable")) {
			return;
		}
		source.setAttribute("data-drafter-editable", "true");
		source.classList.add("drafter-editable");

		var status = document.createElement("span");
		status.className = "drafter-edit-status";

		var button = document.createElement("button");
		button.type = "button";
		button.className = "drafter-edit-button";
		button.title = "Edit this code";
		button.setAttribute("aria-label", "Edit this code");
		button.innerHTML = PENCIL_ICON;

		source.appendChild(status);
		source.appendChild(button);

		var textarea = null;
		var running = false;

		function setStatus(message, isError) {
			status.textContent = message;
			status.classList.toggle("drafter-edit-status--error", !!isError);
		}

		function handleEditorKeys(event) {
			if (event.key === "Tab" && !event.shiftKey) {
				event.preventDefault();
				var start = textarea.selectionStart;
				var end = textarea.selectionEnd;
				textarea.value =
					textarea.value.slice(0, start) +
					"    " +
					textarea.value.slice(end);
				textarea.selectionStart = textarea.selectionEnd = start + 4;
			} else if (
				event.key === "Enter" &&
				(event.ctrlKey || event.metaKey)
			) {
				event.preventDefault();
				runCode();
			}
		}

		function enterEditMode() {
			var codeElement = source.querySelector("code");
			var original =
				(codeElement ? codeElement.textContent : source.textContent) ||
				"";
			original = original.replace(/\n$/, "");

			textarea = document.createElement("textarea");
			textarea.className = "drafter-edit-area";
			textarea.value = original;
			textarea.spellcheck = false;
			textarea.setAttribute("aria-label", "Editable example code");
			textarea.rows = Math.min(
				Math.max(original.split("\n").length + 1, 4),
				40,
			);
			textarea.addEventListener("keydown", handleEditorKeys);

			Array.prototype.forEach.call(source.children, function (child) {
				if (child !== button && child !== status) {
					child.setAttribute("data-drafter-hidden", "true");
				}
			});
			source.appendChild(textarea);

			button.innerHTML = RUN_ICON;
			button.title = "Run this code in the demo below (Ctrl+Enter)";
			button.setAttribute(
				"aria-label",
				"Run this code in the demo below",
			);
			button.classList.add("drafter-edit-button--run");
			textarea.focus();
		}

		function runCode() {
			if (running || !textarea) {
				return;
			}
			var code = textarea.value;
			if (!/\bstart_server\s*\(/.test(code)) {
				code = code.replace(/\s*$/, "") + "\n\nstart_server()\n";
			}
			var host =
				window.Drafter && window.Drafter.getHost
					? window.Drafter.getHost()
					: null;
			if (!host || typeof host.restart !== "function") {
				setStatus("The live demo runtime is unavailable.", true);
				return;
			}
			var instanceId = "embed-" + demoId;
			running = true;
			button.disabled = true;
			setStatus("Running…", false);
			// Lazily-loaded iframes only attach once they start loading;
			// force the load so a run before first scroll still works.
			var iframe = demo.querySelector("iframe");
			if (iframe && !host.has(instanceId)) {
				iframe.loading = "eager";
			}
			waitForInstance(host, instanceId, 30000)
				.then(function (attached) {
					if (!attached) {
						throw new Error(
							"The demo below has not finished loading yet; " +
								"try again in a moment.",
						);
					}
					return host.restart(instanceId, code);
				})
				.then(function () {
					setStatus("", false);
				})
				.catch(function (error) {
					console.error(
						"[Drafter Docs] Failed to run edited demo code:",
						error,
					);
					setStatus(
						error && error.message
							? error.message
							: "Failed to run the code.",
						true,
					);
				})
				.finally(function () {
					running = false;
					button.disabled = false;
				});
		}

		button.addEventListener("click", function () {
			if (textarea) {
				runCode();
			} else {
				enterEditMode();
			}
		});
	}

	function init() {
		var demos = document.querySelectorAll(
			"div.drafter-demo[data-drafter-demo]",
		);
		Array.prototype.forEach.call(demos, setupDemo);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
	// Material for MkDocs instant navigation re-renders pages without a
	// full reload; re-scan whenever its document observable fires.
	if (typeof document$ !== "undefined" && document$ && document$.subscribe) {
		document$.subscribe(init);
	}
})();
