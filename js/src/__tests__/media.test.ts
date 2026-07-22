import { beforeEach, describe, expect, jest, test } from "@jest/globals";

import "../components/media";

describe("drafter-media", () => {
	beforeEach(() => {
		document.body.innerHTML = "";
	});

	function createWrapped(
		tag: "audio" | "video",
		autoplay: boolean,
	): {
		wrapper: HTMLElement;
		media: HTMLMediaElement;
		play: jest.Mock;
	} {
		const wrapper = document.createElement("drafter-media");
		if (autoplay) {
			wrapper.setAttribute("autoplay", "");
		}
		const media = document.createElement(tag) as HTMLMediaElement;
		const play = jest.fn(() => Promise.resolve());
		Object.defineProperty(media, "play", { value: play, configurable: true });
		wrapper.appendChild(media);
		document.body.appendChild(wrapper);
		return { wrapper, media, play };
	}

	function dispatchPageLoaded(): void {
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
	}

	test("defers audio autoplay until the page-loaded event", () => {
		const { play } = createWrapped("audio", true);

		expect(play).not.toHaveBeenCalled();
		dispatchPageLoaded();
		expect(play).toHaveBeenCalledTimes(1);
	});

	test("defers video autoplay until the page-loaded event", () => {
		const { play } = createWrapped("video", true);

		expect(play).not.toHaveBeenCalled();
		dispatchPageLoaded();
		expect(play).toHaveBeenCalledTimes(1);
	});

	test("never plays without the autoplay attribute", () => {
		const { play } = createWrapped("audio", false);

		dispatchPageLoaded();
		expect(play).not.toHaveBeenCalled();
	});

	test("only autoplays once per page view", () => {
		const { play } = createWrapped("audio", true);

		dispatchPageLoaded();
		dispatchPageLoaded();
		expect(play).toHaveBeenCalledTimes(1);
	});

	test("does not restart an adopted media element on later pages", () => {
		const { wrapper, media, play } = createWrapped("audio", true);
		dispatchPageLoaded();
		expect(play).toHaveBeenCalledTimes(1);

		// Simulate a page transition where the persistent audio element is
		// adopted into a fresh wrapper rendered by the next page.
		wrapper.remove();
		const nextWrapper = document.createElement("drafter-media");
		nextWrapper.setAttribute("autoplay", "");
		nextWrapper.appendChild(media);
		document.body.appendChild(nextWrapper);
		dispatchPageLoaded();

		expect(play).toHaveBeenCalledTimes(1);
	});

	test("starts playback when autoplay is set after the page has loaded", () => {
		const { wrapper, play } = createWrapped("audio", false);
		dispatchPageLoaded();
		expect(play).not.toHaveBeenCalled();

		wrapper.setAttribute("autoplay", "");
		expect(play).toHaveBeenCalledTimes(1);
	});

	test("cancels pending autoplay when the attribute is removed", () => {
		const { wrapper, play } = createWrapped("audio", true);

		wrapper.removeAttribute("autoplay");
		dispatchPageLoaded();
		expect(play).not.toHaveBeenCalled();
	});

	test("does not autoplay after being disconnected", () => {
		const { wrapper, play } = createWrapped("audio", true);

		wrapper.remove();
		dispatchPageLoaded();
		expect(play).not.toHaveBeenCalled();
	});

	test("swallows play() rejections from blocked autoplay", async () => {
		const wrapper = document.createElement("drafter-media");
		wrapper.setAttribute("autoplay", "");
		const media = document.createElement("audio");
		const play = jest.fn(() => Promise.reject(new Error("blocked")));
		Object.defineProperty(media, "play", { value: play, configurable: true });
		wrapper.appendChild(media);
		document.body.appendChild(wrapper);

		dispatchPageLoaded();
		expect(play).toHaveBeenCalledTimes(1);
		// Flush the rejection; the component's catch handler must absorb it
		// without surfacing an unhandled rejection.
		await Promise.resolve();
		await Promise.resolve();
	});
});
