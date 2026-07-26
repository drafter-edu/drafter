import { Panel } from "./panel";
import type { RouteParameterInfo } from "../telemetry/routes";

/**
 * The Routes panel lists every registered route as a swagger-style entry:
 * expanding a route reveals a form with one field per request parameter;
 * submitting the form dispatches a drafter-navigate event carrying the
 * route and the entered arguments, triggering a real visit.
 */
export class RoutesPanel extends Panel {
	constructor(containerId: string, instanceId: number, root: ParentNode = document) {
		super(
			containerId,
			instanceId,
			"drafter-debug-routes",
			"Registered Routes",
			root,
		);
	}

	protected get initialContent() {
		return (
			<div>
				<div
					class={`drafter-debug-routes-list drafter-debug-regular-routes-list-${this.instanceId}`}
				></div>
				<details
					class={`drafter-debug-routes-list drafter-debug-system-routes-list-${this.instanceId}`}
				>
					<summary>System Routes</summary>
				</details>
			</div>
		);
	}

	public renderRoute(
		route: string,
		signature: string,
		isSystemRoute: boolean = false,
		parameters: RouteParameterInfo[] = [],
	): void {
		const section = this.queryWithin(
			this.scopedSelector(
				isSystemRoute && route != "index"
					? "drafter-debug-system-routes-list"
					: "drafter-debug-regular-routes-list",
			),
			"DebugPanel: Routes section not found.",
		);

		const newRouteItem = (
			<details class="drafter-debug-route-signature">
				<summary>
					<strong>{route}</strong>:<code>{signature}</code>
				</summary>
				{this.buildTryItForm(route, parameters ?? [])}
			</details>
		);

		section.appendChild(newRouteItem);
	}

	/** Build the parameter form that lets the user trigger this route. */
	private buildTryItForm(
		route: string,
		parameters: RouteParameterInfo[],
	): HTMLElement {
		const inputs: Array<{ name: string; input: HTMLInputElement }> = [];

		const form = (
			<form class="drafter-debug-route-try">
				{parameters.map((parameter) => {
					const input = (
						<input
							type="text"
							name={parameter.name}
							placeholder={
								parameter.default !== null
									? `default: ${parameter.default}`
									: parameter.type || "value"
							}
						/>
					) as HTMLInputElement;
					inputs.push({ name: parameter.name, input });
					return (
						<label class="drafter-debug-route-try-field">
							<span class="drafter-debug-route-try-name">
								{parameter.name}
								{parameter.required ? " *" : ""}
							</span>
							{parameter.type ? (
								<span class="drafter-debug-route-try-type">
									{parameter.type}
								</span>
							) : null}
							{input}
						</label>
					);
				})}
				<button
					type="submit"
					class="drafter-debug-route-try-submit drafter-debug-button--"
				>
					Visit Route
				</button>
			</form>
		) as HTMLFormElement;

		form.addEventListener("submit", (event) => {
			event.preventDefault();
			const data: Record<string, string> = {};
			for (const { name, input } of inputs) {
				if (input.value !== "") {
					data[name] = input.value;
				}
			}
			window.dispatchEvent(
				new CustomEvent("drafter-navigate", {
					detail: {
						url: route,
						kwargs_json: JSON.stringify(data),
					},
				}),
			);
		});

		return form;
	}
}
