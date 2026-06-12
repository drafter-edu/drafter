import { getAllClientFiles, getFileContents } from "../utils/fs";
import { wordWrap } from "../utils/text";
import { Panel } from "./panel";

export class FilesPanel extends Panel {
	constructor(containerId: string, instanceId: number) {
		super(containerId, instanceId, "drafter-debug-files", "File Systems");
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
				<div class="drafter-debug-files-list drafter-debug-files-host">
					<strong>
						Host File System
						<button class="drafter-debug-refresh-host-btn">
							Refresh
						</button>
					</strong>
					<div class="drafter-debug-files-list-items"></div>
				</div>
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
	}

	public renderClientFileSystem(): void {
		const content = this.getContentElement();
		getAllClientFiles().forEach((file: string) => {
			const fileItem = document.createElement("code");
			fileItem.textContent = file;
			fileItem.addEventListener("click", () => {
				this.previewFile(file);
			});
			content
				.querySelector(
					".drafter-debug-files-local .drafter-debug-files-list-items",
				)
				?.appendChild(fileItem);
		});
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
