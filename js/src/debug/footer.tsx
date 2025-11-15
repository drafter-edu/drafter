import { t } from "../i18n";

export class DebugFooterBar {
    private footerElement: HTMLElement;
    private routeElement: HTMLElement;

    constructor() {
        this.footerElement = document.querySelector(
            ".drafter-footer--"
        ) as HTMLElement;

        if (!this.footerElement) {
            throw new Error("Footer element not found");
        }

        const content = this.createFooterBar();
        this.footerElement.appendChild(content);
        this.routeElement = this.footerElement.querySelector(
            ".drafter-footer-route"
        ) as HTMLElement;
    }

    private createFooterBar() {
        return (
            <div className="drafter-footer-bar">
                <span>{t("footer.route")}</span>
                <span className="drafter-footer-route"></span>
            </div>
        );
    }

    public setRoute(route: string) {
        this.routeElement.textContent = route;
    }
}
