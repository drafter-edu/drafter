import { t } from "../i18n";

const PERSIST_AREA_SELECTOR = ".drafter-persist--";
const PERSIST_KEY_ATTR = "data-drafter-persist-key";

export class DebugFooterBar {
    private footerElement: HTMLElement;
    private routeElement: HTMLElement;
    private root: ParentNode;
    private persistButton: HTMLButtonElement;
    private persistPanel: HTMLElement;
    private persistList: HTMLElement;
    private revealButton: HTMLButtonElement;

    constructor(root: ParentNode = document) {
        this.root = root;
        this.footerElement = root.querySelector(
            ".drafter-footer--"
        ) as HTMLElement;

        if (!this.footerElement) {
            throw new Error("Footer element not found");
        }

        const content = this.createFooterBar();
        const footer = this.footerElement.appendChild(content);
        this.routeElement = this.footerElement.querySelector(
            ".drafter-footer-route"
        ) as HTMLElement;
        footer.addEventListener("click", (e) => {
            (e.target as HTMLElement).classList.toggle("truncate");
        });

        this.persistButton = footer.querySelector(
            ".drafter-footer-persist-button"
        ) as HTMLButtonElement;
        this.persistPanel = this.footerElement.appendChild(
            this.createPersistPanel() as HTMLElement
        );
        this.persistList = this.persistPanel.querySelector(
            ".drafter-footer-persist-list"
        ) as HTMLElement;
        this.revealButton = this.persistPanel.querySelector(
            ".drafter-footer-persist-reveal"
        ) as HTMLButtonElement;

        this.persistButton.addEventListener("click", (e) => {
            e.stopPropagation();
            this.persistPanel.hidden = !this.persistPanel.hidden;
            this.refreshPersisted();
        });
        this.revealButton.addEventListener("click", (e) => {
            e.stopPropagation();
            const area = this.getPersistArea();
            if (area) {
                area.hidden = !area.hidden;
            }
        });

        this.refreshPersisted();
    }

    private createFooterBar() {
        return (
            <div className="drafter-footer-bar">
                <span className="drafter-footer-label">
                    {t("footer.route")}
                </span>
                <span className="drafter-footer-route truncate"></span>
                <button
                    type="button"
                    className="drafter-footer-persist-button"
                    title={t("footer.persisted.tooltip")}
                >
                    📌 {t("footer.persisted")} (0)
                </button>
            </div>
        );
    }

    private createPersistPanel() {
        return (
            <div className="drafter-footer-persist-panel" hidden>
                <div className="drafter-footer-persist-header">
                    <span>📌 {t("footer.persisted")}</span>
                    <button
                        type="button"
                        className="drafter-footer-persist-reveal"
                        title={t("footer.persisted.reveal.tooltip")}
                    >
                        👁️ {t("footer.persisted.reveal")}
                    </button>
                </div>
                <ul className="drafter-footer-persist-list"></ul>
            </div>
        );
    }

    private getPersistArea(): HTMLElement | null {
        return this.root.querySelector(
            PERSIST_AREA_SELECTOR
        ) as HTMLElement | null;
    }

    private describeState(element: Element): string {
        if (
            element instanceof HTMLMediaElement ||
            element.tagName === "AUDIO" ||
            element.tagName === "VIDEO"
        ) {
            const media = element as HTMLMediaElement;
            return media.paused ? "⏸" : "▶";
        }
        return (element.textContent ?? "").trim();
    }

    private createPersistRow(element: Element): HTMLElement {
        const key = element.getAttribute(PERSIST_KEY_ATTR) ?? "";
        const evictButton = (
            <button
                type="button"
                className="drafter-footer-persist-evict"
                title={t("footer.persisted.evict.tooltip")}
            >
                🗑️ {t("footer.persisted.evict")}
            </button>
        ) as HTMLButtonElement;
        evictButton.addEventListener("click", (e) => {
            e.stopPropagation();
            window.dispatchEvent(
                new CustomEvent("drafter-evict-persistent", { detail: key })
            );
            this.refreshPersisted();
        });
        return (
            <li className="drafter-footer-persist-item">
                <code>{element.tagName.toLowerCase()}</code>
                <span className="drafter-footer-persist-key">{key}</span>
                <span className="drafter-footer-persist-state">
                    {this.describeState(element)}
                </span>
                {evictButton}
            </li>
        ) as HTMLElement;
    }

    public refreshPersisted() {
        const area = this.getPersistArea();
        const parked = area ? Array.from(area.children) : [];
        this.persistButton.textContent = `📌 ${t("footer.persisted")} (${parked.length})`;
        if (!this.persistList) {
            return;
        }
        this.persistList.replaceChildren(
            ...(parked.length > 0
                ? parked.map((element) => this.createPersistRow(element))
                : [
                      (
                          <li className="drafter-footer-persist-empty">
                              {t("footer.persisted.empty")}
                          </li>
                      ) as HTMLElement,
                  ])
        );
    }

    public setRoute(route: string) {
        this.routeElement.textContent = route;
        // Every response passes through here, so the persisted list and
        // count stay current without any window-level listeners to leak.
        this.refreshPersisted();
    }
}
