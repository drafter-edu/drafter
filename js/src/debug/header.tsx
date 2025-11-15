import { t } from "../i18n";

export class DebugHeaderBar {
    private headerElement: HTMLElement;

    constructor(siteName: string) {
        this.headerElement = document.querySelector(
            ".drafter-header--"
        ) as HTMLElement;

        if (!this.headerElement) {
            throw new Error("Header element not found");
        }

        const content = this.createHeaderBar();
        this.headerElement.appendChild(content);
    }

    private createHeaderBar() {
        const title = <span>{t("app.title")}</span>;
        const hotButtons = this.createHotButtons();
        return (
            <div className="drafter-header-bar">
                {title}
                {hotButtons}
            </div>
        );
    }

    private createHotButtons() {
        return (
            <div className="drafter-header-hot-buttons">
                <button title={t("button.home")} class="drafter-home-button">
                    {t("icon.home")}
                </button>
                <button title={t("button.reset")} class="drafter-reset-button">
                    {t("icon.reset")}
                </button>
                <button title={t("button.about")} class="drafter-about-button">
                    {t("icon.about")}
                </button>
                <button title={t("button.save")} class="drafter-save-button">
                    {t("icon.save")}
                </button>
                <button title={t("button.load")} class="drafter-load-button">
                    {t("icon.load")}
                </button>
                <button
                    title={t("button.download")}
                    class="drafter-download-button"
                >
                    {t("icon.download")}
                </button>
                <button
                    title={t("button.toggle")}
                    class="drafter-toggle-button"
                >
                    {t("icon.toggle")}
                </button>
                <button title={t("button.close")} class="drafter-close-button">
                    {t("icon.close")}
                </button>
            </div>
        );
    }

    public setTitle(title: string) {
        this.headerElement.innerHTML = `<span>${title}</span>`;
    }
}
