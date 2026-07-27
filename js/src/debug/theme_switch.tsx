import { showDialog } from "../dialogs";
import { t } from "../i18n";
import {
	getStoredConfigurationOverrides,
	setStoredConfigurationOverrides,
	syncWindowConfigurationOverrides,
} from "../config_overrides";

/** The theme names registered in src/drafter/styling/themes.py. */
export const AVAILABLE_THEMES = [
	"default",
	"none",
	"7",
	"98",
	"almond",
	"brutal",
	// "darkfairy",
	"daub",
	"latex",
	"magick",
	// "matcha",
	"mvp",
	"pico",
	"retro",
	"sakura",
	"simple",
	"skeleton",
	"tacit",
	"terminal",
	"water",
	"xp",
	"yorha",
];

/** The theme currently in effect: local override first, then embedded config. */
export function getCurrentTheme(): string | null {
	const override = getStoredConfigurationOverrides()["theme"];
	if (typeof override === "string") {
		return override;
	}
	const embedded = (
		window as {
			DRAFTER_MODIFIED_CONFIGURATION?: {
				client_server?: { theme?: unknown };
			};
		}
	).DRAFTER_MODIFIED_CONFIGURATION?.client_server?.theme;
	return typeof embedded === "string" ? embedded : null;
}

/**
 * Apply a theme without reloading: dispatch ``drafter-set-theme`` (the
 * same event-driven pattern as the frame toggle), which Python answers by
 * reconfiguring the server and swapping the connected theme stylesheets in
 * place. The choice is also stored as a configuration override so a later
 * page reload keeps it (the same mechanism the Configuration panel uses).
 */
export function applyTheme(theme: string): void {
	const overrides = {
		...getStoredConfigurationOverrides(),
		theme,
	};
	setStoredConfigurationOverrides(overrides);
	syncWindowConfigurationOverrides(overrides);
	window.dispatchEvent(
		new CustomEvent("drafter-set-theme", { detail: theme }),
	);
}

/**
 * Dialog listing the available themes; picking one applies it live.
 *
 * Each option is rendered as an abstract "mini preview" of its theme: the
 * button carries `drafter-theme-option-<name>`, whose CSS (in
 * drafter_debug.css) sets per-theme custom properties for the estimated
 * page background, text color, accent color, and primary font. The dialog
 * CSS pins every other visual property so the page's active theme cannot
 * bleed into the options and make them unreadable.
 */
export function openThemeSwitcher(): void {
	const current = getCurrentTheme();
	const list = (<div class="drafter-theme-list"></div>) as HTMLDivElement;
	AVAILABLE_THEMES.forEach((theme) => {
		const isCurrent = theme === current;
		const pick = (
			<button
				type="button"
				class={`drafter-theme-option drafter-theme-option-${theme} ${
					isCurrent ? "is-current" : ""
				}`}
			>
				<span class="drafter-theme-option-header">
					<span class="drafter-theme-name">{theme}</span>
					{isCurrent ? (
						<span class="drafter-theme-current-badge">
							{t("theme.current")}
						</span>
					) : null}
				</span>
				<span class="drafter-theme-swatches" aria-hidden="true">
					<span class="drafter-theme-swatch drafter-theme-swatch-bg"></span>
					<span class="drafter-theme-swatch drafter-theme-swatch-fg"></span>
					<span class="drafter-theme-swatch drafter-theme-swatch-accent"></span>
				</span>
				<span class="drafter-theme-desc">
					{t(`theme.desc.${theme}`)}
				</span>
			</button>
		) as HTMLButtonElement;
		pick.addEventListener("click", () => {
			applyTheme(theme);
		});
		list.appendChild(pick);
	});

	void showDialog({
		title: t("theme.dialog.title"),
		content: (
			<div>
				<p class="drafter-theme-note">{t("theme.dialog.note")}</p>
				{list}
			</div>
		) as HTMLElement,
		width: "560px",
		buttons: [{ label: t("saveload.close"), variant: "secondary" }],
	});
}
