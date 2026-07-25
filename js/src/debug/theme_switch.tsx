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
	"mvp",
	"sakura",
	"simple",
	"skeleton",
	"tacit",
	"98",
	"xp",
	"7",
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

/** Dialog listing the available themes; picking one applies it (reloads). */
export function openThemeSwitcher(): void {
	const current = getCurrentTheme();
	const list = (
		<div class="drafter-saveload-slots drafter-theme-list"></div>
	) as HTMLDivElement;
	AVAILABLE_THEMES.forEach((theme) => {
		const isCurrent = theme === current;
		const pick = (
			<button
				type="button"
				class={`drafter-saveload-slot drafter-theme-option drafter-theme-option-${theme} ${
					isCurrent ? "is-current" : ""
				}`}
			>
				<span class="drafter-saveload-slot-name">{theme}</span>
				<span class="drafter-saveload-slot-meta">
					{isCurrent ? t("theme.current") : ""}
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
		width: "420px",
		buttons: [{ label: t("saveload.close"), variant: "secondary" }],
	});
}
