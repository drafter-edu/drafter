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
 * Store a theme choice as a configuration override and reload so the site
 * re-renders with it. Theme CSS is injected during site setup, so a reload
 * is the reliable way to apply it (overrides re-apply automatically, the
 * same mechanism the Configuration panel uses).
 */
export function applyTheme(
	theme: string,
	// Injectable for tests: jsdom's window.location cannot be stubbed.
	reload: () => void = () => window.location.reload(),
): void {
	const overrides = {
		...getStoredConfigurationOverrides(),
		theme,
	};
	setStoredConfigurationOverrides(overrides);
	syncWindowConfigurationOverrides(overrides);
	reload();
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
