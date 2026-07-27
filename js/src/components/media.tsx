import { DrafterHTMLElement } from "./drafterHTMLElement";
import { DRAFTER_PAGE_LOADED_EVENT } from "./events";

/**
 * Media elements whose deferred autoplay has already been triggered.
 * Tracked per media element (not per wrapper) so a persistent
 * <audio>/<video> adopted into a fresh wrapper on the next page does not
 * restart on every navigation, mirroring how the native autoplay attribute
 * only fires once per element.
 */
const alreadyAutoplayed = new WeakSet<HTMLMediaElement>();

/**
 * Wrapper around native <audio>/<video> elements that defers autoplay until
 * the drafter page-loaded event. The server renders the media element
 * without its autoplay attribute and puts autoplay on this wrapper instead,
 * so playback starts once the page has finished loading rather than while
 * the new page's HTML is still being inserted.
 */
class DrafterMedia extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["autoplay"];
	}

	private waitingForPageLoad = false;

	private pageLoadedForCurrentView = false;

	private handlePageLoaded = (_event: Event): void => {
		if (!this.isConnected) {
			return;
		}
		this.pageLoadedForCurrentView = true;
		if (!this.waitingForPageLoad) {
			return;
		}
		this.waitingForPageLoad = false;
		this.startAutoplay();
	};

	private isAutoPlay(): boolean {
		return this.getBooleanAttribute("autoplay", false);
	}

	/**
	 * Looked up lazily (not cached at connect time) because persistence
	 * adoption may swap the freshly-rendered media element for the parked
	 * one after this wrapper is connected.
	 */
	private getMediaElement(): HTMLMediaElement | null {
		return this.querySelector("audio, video");
	}

	private startAutoplay(): void {
		const media = this.getMediaElement();
		if (media === null || alreadyAutoplayed.has(media)) {
			return;
		}
		alreadyAutoplayed.add(media);
		void media.play()?.catch?.(() => {
			// Autoplay was blocked by the browser; the user can still start
			// playback from the element's native controls.
		});
	}

	connectedCallback() {
		this.pageLoadedForCurrentView = false;
		window.addEventListener(DRAFTER_PAGE_LOADED_EVENT, this.handlePageLoaded);
		this.waitingForPageLoad = this.isAutoPlay();
	}

	attributeChangedCallback(
		name: string,
		oldValue: string | null,
		newValue: string | null,
	) {
		if (oldValue === newValue || !this.isConnected || name !== "autoplay") {
			return;
		}
		if (!this.isAutoPlay()) {
			this.waitingForPageLoad = false;
			return;
		}
		if (this.pageLoadedForCurrentView) {
			this.startAutoplay();
		} else {
			this.waitingForPageLoad = true;
		}
	}

	disconnectedCallback() {
		window.removeEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.waitingForPageLoad = false;
		this.pageLoadedForCurrentView = false;
	}
}

customElements.define("drafter-media", DrafterMedia);
