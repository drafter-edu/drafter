import { getHandlers } from "./utils";

/** Inject component styles once into the document head. */
function injectGeolocationStyles() {
	if (document.getElementById("drafter-geolocation-styles")) return;
	const style = document.createElement("style");
	style.id = "drafter-geolocation-styles";
	style.textContent = `
drafter-geolocation {
	display: block;
	margin: 1rem 0;
	padding: 1rem;
	border: 1px solid #ddd;
	border-radius: 8px;
	background: #f9f9f9;
	font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
drafter-geolocation .drafter-geolocation-status { text-align: center; }
drafter-geolocation .drafter-geolocation-prompt {
	display: inline-block;
	padding: 0.75rem 1.5rem;
	font-size: 1rem;
	font-weight: 600;
	color: #fff;
	background: #007bff;
	border: none;
	border-radius: 6px;
	cursor: pointer;
	transition: background 0.2s;
}
drafter-geolocation .drafter-geolocation-prompt:hover { background: #0056b3; }
drafter-geolocation .drafter-geolocation-help {
	margin-top: 0.5rem;
	font-size: 0.875rem;
	color: #666;
}
drafter-geolocation .drafter-geolocation-pending {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
}
drafter-geolocation .drafter-geolocation-spinner {
	width: 32px;
	height: 32px;
	border: 3px solid #f3f3f3;
	border-top: 3px solid #007bff;
	border-radius: 50%;
	animation: drafter-geo-spin 1s linear infinite;
}
@keyframes drafter-geo-spin {
	0% { transform: rotate(0deg); }
	100% { transform: rotate(360deg); }
}
drafter-geolocation .drafter-geolocation-granted,
drafter-geolocation .drafter-geolocation-denied,
drafter-geolocation .drafter-geolocation-unavailable,
drafter-geolocation .drafter-geolocation-error {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
}
drafter-geolocation .drafter-geolocation-success-icon { font-size: 2rem; color: #28a745; margin: 0; }
drafter-geolocation .drafter-geolocation-success-message { font-weight: 600; color: #28a745; margin: 0; }
drafter-geolocation .drafter-geolocation-error-icon { font-size: 2rem; margin: 0; }
drafter-geolocation .drafter-geolocation-error-message { font-weight: 600; color: #dc3545; margin: 0; }
drafter-geolocation .drafter-geolocation-coords {
	font-family: monospace;
	font-size: 0.875rem;
	color: #333;
	margin: 0;
}
`;
	document.head.appendChild(style);
}

type LocationData = {
	status: string;
	message?: string;
	lat?: number;
	lon?: number;
	accuracy?: number;
	altitude?: number | null;
	heading?: number | null;
	speed?: number | null;
	timestamp?: number;
};

class DrafterGeolocation extends HTMLElement {
	private hiddenInput: HTMLInputElement | null = null;
	private statusDiv: HTMLDivElement | null = null;

	connectedCallback() {
		injectGeolocationStyles();

		const name = this.getAttribute("name") || "";
		const showCoordinates =
			this.getAttribute("show-coordinates")?.toLowerCase() === "true";
		const handlers = getHandlers(this);

		// Create hidden input that form submission reads
		this.hiddenInput = document.createElement("input");
		this.hiddenInput.type = "hidden";
		this.hiddenInput.name = name;
		this.hiddenInput.value = "";
		this.appendChild(this.hiddenInput);

		// Create status container
		this.statusDiv = document.createElement("div");
		this.statusDiv.className = "drafter-geolocation-status";
		this.appendChild(this.statusDiv);

		// Handle missing geolocation API
		if (!navigator.geolocation) {
			const data: LocationData = { status: "unavailable" };
			this.hiddenInput.value = JSON.stringify(data);
			this.showUnavailable(this.statusDiv);
			if (handlers["unavailable"]) {
				this.dispatchEvent(
					new CustomEvent("unavailable", { detail: data }),
				);
			}
			return;
		}

		// Show initial prompt state
		this.showPrompt(this.statusDiv, showCoordinates, handlers);

		// If permission was already granted/denied, reflect that immediately
		if (navigator.permissions) {
			navigator.permissions
				.query({ name: "geolocation" })
				.then((result) => {
					if (result.state === "granted") {
						this.showPending(this.statusDiv!);
						this.requestPosition(
							this.statusDiv!,
							showCoordinates,
							handlers,
						);
					} else if (result.state === "denied") {
						const data: LocationData = {
							status: "denied",
							message: "Location access denied",
						};
						this.hiddenInput!.value = JSON.stringify(data);
						this.showDenied(this.statusDiv!);
						if (handlers["deny"]) {
							this.dispatchEvent(
								new CustomEvent("deny", { detail: data }),
							);
						}
					}
				})
				.catch(() => {
					/* Permissions API unsupported; prompt remains visible */
				});
		}
	}

	disconnectedCallback() {
		this.hiddenInput = null;
		this.statusDiv = null;
	}

	private showPrompt(
		statusDiv: HTMLElement,
		showCoordinates: boolean,
		handlers: Record<string, string>,
	) {
		statusDiv.innerHTML = "";

		const button = document.createElement("button");
		button.type = "button";
		button.className = "drafter-geolocation-prompt";
		button.textContent = "📍 Use my location";
		button.addEventListener("click", () => {
			this.showPending(statusDiv);
			this.requestPosition(statusDiv, showCoordinates, handlers);
		});

		const help = document.createElement("p");
		help.className = "drafter-geolocation-help";
		help.textContent =
			"Your location helps personalize your experience. Click to allow.";

		statusDiv.appendChild(button);
		statusDiv.appendChild(help);
	}

	private showPending(statusDiv: HTMLElement) {
		statusDiv.innerHTML = `
			<div class="drafter-geolocation-pending">
				<div class="drafter-geolocation-spinner"></div>
				<p>Requesting permission...</p>
			</div>`;
	}

	private showGranted(
		statusDiv: HTMLElement,
		data: LocationData,
		showCoordinates: boolean,
	) {
		const coordsHtml =
			showCoordinates && data.lat != null && data.lon != null
				? `<p class="drafter-geolocation-coords">${data.lat.toFixed(6)}, ${data.lon.toFixed(6)}${data.accuracy != null ? ` (±${Math.round(data.accuracy)}m)` : ""}</p>`
				: "";
		statusDiv.innerHTML = `
			<div class="drafter-geolocation-granted">
				<p class="drafter-geolocation-success-icon">✓</p>
				<p class="drafter-geolocation-success-message">Location available ✓</p>
				${coordsHtml}
			</div>`;
	}

	private showDenied(statusDiv: HTMLElement) {
		statusDiv.innerHTML = `
			<div class="drafter-geolocation-denied">
				<p class="drafter-geolocation-error-icon">⚠️</p>
				<p class="drafter-geolocation-error-message">Location access denied</p>
			</div>`;
	}

	private showError(statusDiv: HTMLElement, message: string) {
		statusDiv.innerHTML = `
			<div class="drafter-geolocation-error">
				<p class="drafter-geolocation-error-icon">⚠️</p>
				<p class="drafter-geolocation-error-message">${message}</p>
			</div>`;
	}

	private showUnavailable(statusDiv: HTMLElement) {
		statusDiv.innerHTML = `
			<div class="drafter-geolocation-unavailable">
				<p class="drafter-geolocation-error-icon">ℹ️</p>
				<p>Geolocation is not supported by your browser</p>
			</div>`;
	}

	private requestPosition(
		statusDiv: HTMLElement,
		showCoordinates: boolean,
		handlers: Record<string, string>,
	) {
		navigator.geolocation.getCurrentPosition(
			(position) => {
				const coords = position.coords;
				const data: LocationData = {
					status: "granted",
					message: "Location available",
					lat: coords.latitude,
					lon: coords.longitude,
					accuracy: coords.accuracy,
					altitude: coords.altitude,
					heading: coords.heading,
					speed: coords.speed,
					timestamp: position.timestamp,
				};
				this.hiddenInput!.value = JSON.stringify(data);
				this.showGranted(statusDiv, data, showCoordinates);
				if (handlers["grant"]) {
					this.dispatchEvent(
						new CustomEvent("grant", { detail: data }),
					);
				}
			},
			(error) => {
				let status = "error";
				let message = "Could not retrieve location";
				if (error.code === error.PERMISSION_DENIED) {
					status = "denied";
					message = "Location access denied";
				} else if (error.code === error.POSITION_UNAVAILABLE) {
					message = "Location information unavailable";
				} else if (error.code === error.TIMEOUT) {
					message = "Location request timed out";
				}
				const data: LocationData = { status, message };
				this.hiddenInput!.value = JSON.stringify(data);
				if (status === "denied") {
					this.showDenied(statusDiv);
					if (handlers["deny"]) {
						this.dispatchEvent(
							new CustomEvent("deny", { detail: data }),
						);
					}
				} else {
					this.showError(statusDiv, message);
					if (handlers["error"]) {
						this.dispatchEvent(
							new CustomEvent("error", { detail: data }),
						);
					}
				}
			},
			{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
		);
	}
}

customElements.define("drafter-geolocation", DrafterGeolocation);
