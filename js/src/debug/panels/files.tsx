import { t } from "../../i18n";
import { requestHostFileListing, type HostFileEntry } from "../dev_server";
import { getAllClientFiles, getFileContents } from "../utils/fs";
import { wordWrap } from "../utils/text";
import { Panel } from "./panel";

/**
 * Environment tab: the files Python can reach.
 *
 * The Client File System is the virtual file system inside the browser,
 * where the student's program actually runs. The Host File System is the
 * project folder on the student's computer, as the local development
 * server reports it; a deployed site has no such server, so that half is
 * only built when `showHostFiles` is set (the page came from the
 * development server).
 */
export class FilesPanel extends Panel {
	/** The folder of the project being listed; "" is the project folder. */
	private hostPath = "";
	/** Counts host listings asked for, so a slow answer cannot overwrite a newer one. */
	private hostRequestCount = 0;

	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
		private readonly showHostFiles: boolean = false,
	) {
		super(containerId, instanceId, "drafter-debug-files", "File Systems", root);
	}

	protected get initialContent() {
		return (
			<div
				class={`drafter-debug-files-content drafter-debug-files-content-${this.instanceId}`}
			>
				<div class="drafter-debug-files-list drafter-debug-files-local">
					<strong>
						Client File System
						<button class="drafter-debug-refresh-client-btn">
							Refresh
						</button>
					</strong>
					<div class="drafter-debug-files-list-items"></div>
				</div>
				{this.showHostFiles ? (
					<div class="drafter-debug-files-list drafter-debug-files-host">
						<strong>
							Host File System
							<button class="drafter-debug-refresh-host-btn">
								Refresh
							</button>
						</strong>
						<div class="drafter-debug-files-list-items"></div>
					</div>
				) : null}
			</div>
		);
	}

	public override initialize() {
		// Setup event handlers after structure is created
		const refreshClientButton = this.getContentElement().querySelector(
			".drafter-debug-refresh-client-btn",
		);
		if (refreshClientButton) {
			refreshClientButton.addEventListener("click", () => {
				this.renderClientFileSystem();
			});
		}
		if (this.showHostFiles) {
			this.getContentElement()
				.querySelector(".drafter-debug-refresh-host-btn")
				?.addEventListener("click", () => {
					void this.renderHostFileSystem();
				});
			void this.renderHostFileSystem();
		}
	}

	public renderClientFileSystem(): void {
		const list = this.getContentElement().querySelector(
			".drafter-debug-files-local .drafter-debug-files-list-items",
		);
		if (!list) {
			return;
		}
		// Replace, not append: each Refresh shows the files as they are now.
		list.replaceChildren(
			...getAllClientFiles().map((file: string) => {
				const fileItem = document.createElement("code");
				fileItem.textContent = file;
				fileItem.addEventListener("click", () => {
					this.previewFile(file);
				});
				return fileItem;
			}),
		);
	}

	/**
	 * Fill the Host File System list with the current folder's entries, as
	 * the development server reports them. Folders end in `/` and can be
	 * clicked to look inside; `../` goes back up. When the server gives no
	 * listing, the list says so instead of staying empty.
	 */
	public async renderHostFileSystem(): Promise<void> {
		const list = this.getContentElement().querySelector(
			".drafter-debug-files-host .drafter-debug-files-list-items",
		);
		if (!list) {
			return;
		}
		const request = ++this.hostRequestCount;
		const entries = await requestHostFileListing(this.hostPath);
		if (request !== this.hostRequestCount) {
			return;
		}
		const items: HTMLElement[] = [];
		if (this.hostPath !== "") {
			// Offered even when the folder could not be listed (it may have
			// been deleted), so there is always a way back out of it.
			items.push(
				this.hostFolderItem("../", parentFolder(this.hostPath), "up"),
			);
		}
		if (entries === null) {
			items.push(this.hostNote(t("files.host.unavailable")));
		} else if (entries.length === 0) {
			items.push(this.hostNote(t("files.host.empty")));
		} else {
			for (const entry of entries) {
				items.push(this.hostEntryItem(entry));
			}
		}
		list.replaceChildren(...items);
	}

	private hostNote(message: string): HTMLElement {
		return (
			<span class="drafter-debug-files-host-note">{message}</span>
		) as HTMLElement;
	}

	private hostEntryItem(entry: HostFileEntry): HTMLElement {
		if (entry.is_dir) {
			const inside = this.hostPath
				? `${this.hostPath}/${entry.name}`
				: entry.name;
			return this.hostFolderItem(`${entry.name}/`, inside, "folder");
		}
		return (
			<code class="drafter-debug-files-host-file">{entry.name}</code>
		) as HTMLElement;
	}

	/** A clickable entry that lists another folder when pressed. */
	private hostFolderItem(
		label: string,
		target: string,
		kind: "folder" | "up",
	): HTMLElement {
		const item = (
			<code
				class={`drafter-debug-files-host-${kind}`}
				role="button"
				tabIndex={0}
			>
				{label}
			</code>
		) as HTMLElement;
		const open = () => {
			this.hostPath = target;
			void this.renderHostFileSystem();
		};
		item.addEventListener("click", open);
		item.addEventListener("keydown", (event) => {
			if (event.key === "Enter" || event.key === " ") {
				event.preventDefault();
				open();
			}
		});
		return item;
	}

	private previewFile(file: string): void {
		// Pop-up a simple preview in a dialog box
		const dialog = document.createElement("div");
		dialog.style.position = "fixed";
		dialog.style.top = "50%";
		dialog.style.left = "50%";
		dialog.style.transform = "translate(-50%, -50%)";
		dialog.style.backgroundColor = "#fff";
		dialog.style.border = "1px solid #ccc";
		dialog.style.padding = "20px";
		dialog.style.zIndex = "10000";

		const title = document.createElement("h2");
		title.textContent = `Preview: ${file}`;
		const content = document.createElement("pre");
		content.textContent = `Loading...`;

		dialog.appendChild(title);
		dialog.appendChild(content);
		document.body.appendChild(dialog);

		content.textContent = wordWrap(
			getFileContents(file) || "Unable to load file.",
			80,
		);

		// Close dialog on click outside
		dialog.addEventListener("click", (e) => {
			if (e.target === dialog) {
				document.body.removeChild(dialog);
			}
		});
	}
}

/** The folder that holds `path` ("" for a folder directly in the project). */
function parentFolder(path: string): string {
	const cut = path.lastIndexOf("/");
	return cut === -1 ? "" : path.slice(0, cut);
}
