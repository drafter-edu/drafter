import { DrafterHTMLElement } from "./drafterHTMLElement";

type LocationStatus =
	| "unavailable"
	| "prompt"
	| "granted"
	| "denied"
	| "pending"
	| "error";

type LocationData = {
	status: LocationStatus;
	message?: string;
	lat?: number;
	lon?: number;
	accuracy?: number;
	altitude?: number;
	heading?: number;
	speed?: number;
	timestamp?: number;
};

const GEOLOCATION_OPTIONS: PositionOptions = {
	enableHighAccuracy: true,
	timeout: 10000,
	maximumAge: 0,
};

const DENIED_HELP_INSTRUCTIONS = [
	"To enable location access:",
	"",
	"1. Click the lock or info icon in your browser's address bar",
	"2. Find Location permissions",
	"3. Change to 'Allow'",
	"4. Refresh this page",
].join("\n");

function paragraph(className: string, text: string): HTMLParagraphElement {
	const element = document.createElement("p");
	if (className) {
		element.className = className;
	}
	element.textContent = text;
	return element;
}

class CurrentLocation extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["name", "show", "show-coordinates"];
	}

	private input: HTMLInputElement | null = null;
	private statusArea: HTMLDivElement | null = null;
	private location: LocationData = { status: "prompt" };

	private getName(): string {
		return this.getAttribute("name") ?? "";
	}

	private shouldShowCoordinates(): boolean {
		return this.getBooleanAttribute("show-coordinates", false);
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	// The hidden input is what actually enters the form payload: its value is
	// the JSON-encoded location, and data-transform="json-decode" tells the
	// bridge to decode it before the router converts it to a Location.
	private renderStructure(): void {
		const input = document.createElement("input");
		input.type = "hidden";
		input.name = this.getName();
		input.setAttribute("data-transform", "json-decode");

		const statusArea = document.createElement("div");
		statusArea.className = "drafter-geolocation-status";

		this.input = input;
		this.statusArea = statusArea;
		this.replaceChildren(input, statusArea);
		this.syncVisibility();
	}

	private setLocation(location: LocationData, emit = true): void {
		this.location = location;
		if (this.input !== null) {
			this.input.value = JSON.stringify(location);
		}
		this.renderStatus();
		if (emit) {
			this.dispatchEvent(
				new CustomEvent("locate", { detail: { ...location } }),
			);
		}
	}

	private beginRequest(): void {
		this.setLocation(
			{ status: "pending", message: "Requesting permission..." },
			false,
		);
		navigator.geolocation.getCurrentPosition(
			(position) => this.handleSuccess(position),
			(error) => this.handleError(error),
			GEOLOCATION_OPTIONS,
		);
	}

	private handleSuccess(position: GeolocationPosition): void {
		const coords = position.coords;
		const location: LocationData = {
			status: "granted",
			message: "Location available",
			lat: coords.latitude,
			lon: coords.longitude,
			accuracy: coords.accuracy,
			timestamp: position.timestamp,
		};
		if (coords.altitude !== null) {
			location.altitude = coords.altitude;
		}
		if (coords.heading !== null) {
			location.heading = coords.heading;
		}
		if (coords.speed !== null) {
			location.speed = coords.speed;
		}
		this.setLocation(location);
	}

	private handleError(error: GeolocationPositionError): void {
		let status: LocationStatus = "error";
		let message = "Could not retrieve location";
		if (error.code === error.PERMISSION_DENIED) {
			status = "denied";
			message = "Location access denied";
		} else if (error.code === error.POSITION_UNAVAILABLE) {
			message = "Location information unavailable";
		} else if (error.code === error.TIMEOUT) {
			message = "Location request timed out";
		}
		this.setLocation({ status, message });
	}

	private checkExistingPermission(): void {
		if (!navigator.permissions) {
			return;
		}
		navigator.permissions
			.query({ name: "geolocation" })
			.then((result) => {
				if (!this.isConnected) {
					return;
				}
				if (result.state === "granted") {
					this.beginRequest();
				} else if (result.state === "denied") {
					this.setLocation(
						{ status: "denied", message: "Location access denied" },
						false,
					);
				}
				// If "prompt", leave the initial button visible.
			})
			.catch(() => {
				// Permissions API not fully supported; leave the prompt.
			});
	}

	private renderStatus(): void {
		if (this.statusArea === null) {
			return;
		}
		const { status, message } = this.location;
		const children: Node[] = [];

		if (status === "prompt") {
			const button = document.createElement("button");
			button.type = "button";
			button.className = "drafter-geolocation-prompt";
			button.textContent = "📍 Use my location";
			button.addEventListener("click", () => {
				this.beginRequest();
			});
			children.push(
				button,
				paragraph(
					"drafter-geolocation-help",
					"Your location helps personalize your experience. Click to allow.",
				),
			);
		} else if (status === "pending") {
			const spinner = document.createElement("div");
			spinner.className = "drafter-geolocation-spinner";
			children.push(
				spinner,
				paragraph("", message ?? "Requesting permission..."),
			);
		} else if (status === "granted") {
			children.push(
				paragraph("drafter-geolocation-success-icon", "✓"),
				paragraph(
					"drafter-geolocation-success-message",
					message ?? "Location available",
				),
			);
			const { lat, lon, accuracy } = this.location;
			if (
				this.shouldShowCoordinates() &&
				lat !== undefined &&
				lon !== undefined
			) {
				const accuracyText = accuracy
					? ` (±${Math.round(accuracy)}m)`
					: "";
				children.push(
					paragraph(
						"drafter-geolocation-coords",
						`${lat.toFixed(6)}, ${lon.toFixed(6)}${accuracyText}`,
					),
				);
			}
		} else if (status === "denied") {
			const helpButton = document.createElement("button");
			helpButton.type = "button";
			helpButton.className = "drafter-geolocation-help-link";
			helpButton.textContent = "How to enable location access";
			helpButton.addEventListener("click", () => {
				window.alert(DENIED_HELP_INSTRUCTIONS);
			});
			children.push(
				paragraph("drafter-geolocation-error-icon", "⚠️"),
				paragraph(
					"drafter-geolocation-error-message",
					message ?? "Location access denied",
				),
				helpButton,
			);
		} else if (status === "unavailable") {
			children.push(
				paragraph("drafter-geolocation-error-icon", "ℹ️"),
				paragraph(
					"",
					message ?? "Geolocation is not supported by your browser",
				),
			);
		} else {
			children.push(
				paragraph("drafter-geolocation-error-icon", "⚠️"),
				paragraph(
					"drafter-geolocation-error-message",
					message ?? "Could not retrieve location",
				),
			);
		}

		this.statusArea.dataset.status = status;
		this.statusArea.replaceChildren(...children);
	}

	connectedCallback() {
		this.renderStructure();
		if (!navigator.geolocation) {
			this.setLocation(
				{
					status: "unavailable",
					message: "Geolocation is not supported by your browser",
				},
				false,
			);
			return;
		}
		this.setLocation(
			{
				status: "prompt",
				message: "Location permission has not been requested yet",
			},
			false,
		);
		this.checkExistingPermission();
	}

	attributeChangedCallback(
		name: string,
		oldValue: string | null,
		newValue: string | null,
	) {
		if (oldValue === newValue || !this.isConnected) {
			return;
		}
		if (name === "name") {
			if (this.input !== null) {
				this.input.name = newValue ?? "";
			}
			return;
		}
		if (name === "show-coordinates") {
			this.renderStatus();
			return;
		}
		if (name === "show") {
			this.syncVisibility();
		}
	}

	disconnectedCallback() {
		this.input = null;
		this.statusArea = null;
	}
}

customElements.define("drafter-current-location", CurrentLocation);
