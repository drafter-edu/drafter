export interface LocationRequestOptions {
	maxAgeMs?: number;
	timeoutMs?: number;
	enableHighAccuracy?: boolean;
	forceRefresh?: boolean;
}

type ResolvedLocationRequestOptions = {
	maxAgeMs: number;
	timeoutMs: number;
	enableHighAccuracy: boolean;
	forceRefresh: boolean;
};

type LocationProfile = "coarse" | "fine";

type ProfileState = {
	cachedPosition?: GeolocationPosition;
	inFlight?: Promise<GeolocationPosition>;
};

const DEFAULT_REQUEST_OPTIONS: ResolvedLocationRequestOptions = {
	maxAgeMs: 30_000,
	timeoutMs: 10_000,
	enableHighAccuracy: false,
	forceRefresh: false,
};

const GEOLOCATION_UNSUPPORTED_ERROR =
	"Geolocation is not supported by your browser";

function normalizeRequestOptions(
	options: LocationRequestOptions = {},
): ResolvedLocationRequestOptions {
	return {
		maxAgeMs: options.maxAgeMs ?? DEFAULT_REQUEST_OPTIONS.maxAgeMs,
		timeoutMs: options.timeoutMs ?? DEFAULT_REQUEST_OPTIONS.timeoutMs,
		enableHighAccuracy:
			options.enableHighAccuracy ??
			DEFAULT_REQUEST_OPTIONS.enableHighAccuracy,
		forceRefresh:
			options.forceRefresh ?? DEFAULT_REQUEST_OPTIONS.forceRefresh,
	};
}

function toProfile(options: ResolvedLocationRequestOptions): LocationProfile {
	return options.enableHighAccuracy ? "fine" : "coarse";
}

function getBrowserOptions(
	options: ResolvedLocationRequestOptions,
	profile: LocationProfile,
): PositionOptions {
	return {
		maximumAge: options.forceRefresh ? 0 : Math.max(options.maxAgeMs, 0),
		timeout: Math.max(options.timeoutMs, 0),
		enableHighAccuracy: profile === "fine",
	};
}

export class GeolocationBroker {
	private readonly coarseState: ProfileState = {};

	private readonly fineState: ProfileState = {};

	getPosition(
		options: LocationRequestOptions = {},
	): Promise<GeolocationPosition> {
		const resolvedOptions = normalizeRequestOptions(options);
		const profile = toProfile(resolvedOptions);

		if (!resolvedOptions.forceRefresh) {
			const cached = this.getFreshCachedPosition(
				profile,
				resolvedOptions.maxAgeMs,
			);
			if (cached !== undefined) {
				return Promise.resolve(cached);
			}
		}

		const compatibleInFlight = this.getCompatibleInFlight(profile);
		if (compatibleInFlight !== undefined) {
			return compatibleInFlight;
		}

		return this.startAcquisition(profile, resolvedOptions);
	}

	invalidate(): void {
		this.coarseState.cachedPosition = undefined;
		this.fineState.cachedPosition = undefined;
	}

	resetForTests(): void {
		this.invalidate();
		this.coarseState.inFlight = undefined;
		this.fineState.inFlight = undefined;
	}

	peek(): GeolocationPosition | undefined {
		const coarse = this.coarseState.cachedPosition;
		const fine = this.fineState.cachedPosition;
		if (coarse === undefined) {
			return fine;
		}
		if (fine === undefined) {
			return coarse;
		}
		return fine.timestamp >= coarse.timestamp ? fine : coarse;
	}

	private getState(profile: LocationProfile): ProfileState {
		return profile === "fine" ? this.fineState : this.coarseState;
	}

	private getCompatibleInFlight(
		profile: LocationProfile,
	): Promise<GeolocationPosition> | undefined {
		if (profile === "fine") {
			return this.fineState.inFlight;
		}
		return this.fineState.inFlight ?? this.coarseState.inFlight;
	}

	private getFreshCachedPosition(
		profile: LocationProfile,
		maxAgeMs: number,
	): GeolocationPosition | undefined {
		const now = Date.now();
		const threshold = Math.max(maxAgeMs, 0);
		const candidates: GeolocationPosition[] = [];

		if (profile === "fine") {
			if (this.fineState.cachedPosition !== undefined) {
				candidates.push(this.fineState.cachedPosition);
			}
		} else {
			if (this.coarseState.cachedPosition !== undefined) {
				candidates.push(this.coarseState.cachedPosition);
			}
			if (this.fineState.cachedPosition !== undefined) {
				candidates.push(this.fineState.cachedPosition);
			}
		}

		const freshCandidates = candidates.filter(
			(position) => now - position.timestamp <= threshold,
		);
		if (freshCandidates.length === 0) {
			return undefined;
		}
		return freshCandidates.reduce((best, position) => {
			return position.timestamp > best.timestamp ? position : best;
		});
	}

	private startAcquisition(
		profile: LocationProfile,
		options: ResolvedLocationRequestOptions,
	): Promise<GeolocationPosition> {
		if (!navigator.geolocation) {
			return Promise.reject(new Error(GEOLOCATION_UNSUPPORTED_ERROR));
		}

		const state = this.getState(profile);
		const browserOptions = getBrowserOptions(options, profile);
		const acquisition = new Promise<GeolocationPosition>(
			(resolve, reject) => {
				navigator.geolocation.getCurrentPosition(
					resolve,
					reject,
					browserOptions,
				);
			},
		);

		let sharedPromise: Promise<GeolocationPosition>;
		sharedPromise = acquisition
			.then((position) => {
				state.cachedPosition = position;
				return position;
			})
			.finally(() => {
				if (state.inFlight === sharedPromise) {
					state.inFlight = undefined;
				}
			});
		state.inFlight = sharedPromise;
		return sharedPromise;
	}
}

export const geolocationBroker = new GeolocationBroker();

export function resetGeolocationBrokerForTests(): void {
	geolocationBroker.resetForTests();
}
