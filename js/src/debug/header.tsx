import { t } from "../i18n";
import { HeaderMenuBar, type MenuDefinition } from "./menubar";

const FAVICON_LINK_ID = "drafter-favicon--";

/**
 * Decorates the application frame's `.drafter-header--` with the favicon
 * and application title (top-left) and the dropdown menu bar (top-right).
 */
export class DebugHeaderBar {
	private headerElement: HTMLElement;
	private faviconElement: HTMLImageElement | null = null;
	public readonly menuBar: HeaderMenuBar;

	constructor(
		siteName: string,
		root: ParentNode = document,
		menus: MenuDefinition[] = [],
	) {
		this.headerElement = root.querySelector(
			".drafter-header--",
		) as HTMLElement;

		if (!this.headerElement) {
			throw new Error("Header element not found");
		}

		this.menuBar = new HeaderMenuBar(menus);
		const content = this.createHeaderBar();
		this.headerElement.appendChild(content);
		this.refreshFavicon();
	}

	private createHeaderBar() {
		this.faviconElement = (
			<img
				class="drafter-header-favicon"
				alt=""
				hidden
				width="64"
				height="64"
			/>
		) as HTMLImageElement;
		const title = (
			<span class="drafter-header-title">{t("app.title")}</span>
		);
		return (
			<div className="drafter-header-bar">
				<div className="drafter-header-identity">
					{this.faviconElement}
					{title}
				</div>
				{this.menuBar.element}
			</div>
		);
	}

	/**
	 * Mirror the page's favicon `<link>` (which lives in the document head,
	 * even when the site itself renders in a shadow root) into the header.
	 */
	public refreshFavicon(): void {
		if (!this.faviconElement) {
			return;
		}
		const link = document.getElementById(
			FAVICON_LINK_ID,
		) as HTMLLinkElement | null;
		const href = link?.getAttribute("href") ?? "";
		if (href) {
			this.faviconElement.src = href;
			this.faviconElement.hidden = false;
		} else {
			this.faviconElement.hidden = true;
		}
	}

	public setTitle(title: string) {
		// Only update the title span; replacing the header's innerHTML would
		// destroy the identity/menu structure rendered by the constructor.
		const titleElement = this.headerElement.querySelector(
			".drafter-header-title",
		);
		if (titleElement) {
			titleElement.textContent = title;
		}
		// Title and favicon are configured through the same path, so a title
		// update is the natural moment to re-sync the favicon mirror.
		this.refreshFavicon();
	}
}
