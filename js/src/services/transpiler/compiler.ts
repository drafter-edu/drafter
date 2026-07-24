import type { TreeNode, CssRule } from "./types";

function cssTemplate(cssRules: string[]) {
	return `
add_website_css("""
${cssRules.join("\n")}
""")
`;
}

function bodyTemplate(pageBody: string) {
	return `
def index(state: State) -> Page:
    return Page(state, [
${pageBody}
    ])
`;
}

function stringify(text: string): string {
	if (/\n/.test(text)) {
		if (/"""/.test(text)) {
			return `'''${text}'''`;
		}
		return `"""${text}"""`;
	}
	// Match Python's repr convention: single quotes when the text contains
	// double quotes (but no single quotes), avoiding escaped quotes.
	if (text.includes('"') && !text.includes("'")) {
		return `'${text.replace(/\\/g, "\\\\")}'`;
	}
	return JSON.stringify(text);
}

type Props = Record<string, string>;

type ParsedNodeAttrs = {
	styles: Props;
	attributes: Props;
	classes: string | undefined;
};

const DIRECT_COMPONENT_TAGS: Record<string, string> = {
	span: "Span",
	div: "Div",
	p: "Paragraph",
	section: "Section",
	article: "Article",
	aside: "Aside",
	main: "Main",
	nav: "Nav",
	header: "HeaderContent",
	footer: "FooterContent",
	pre: "Pre",
	code: "InlineCode",
};

const EMPTY_COMPONENT_TAGS: Record<string, string> = {
	br: "LineBreak",
	hr: "HorizontalRule",
};

const LIST_COMPONENT_TAGS: Record<string, string> = {
	ul: "BulletedList",
	ol: "NumberedList",
};

const HEADING_TAG_LEVELS: Record<string, number> = {
	h1: 1,
	h2: 2,
	h3: 3,
	h4: 4,
	h5: 5,
	h6: 6,
};

const PASS_THROUGH_TAGS = new Set(["html", "body"]);
const NON_RENDERING_TAGS = new Set(["head"]);
const TARGET_ATTR_KEYS = ["data-nav", "href", "formaction"];

const ATTRIBUTE_COMPONENT_SPECS: Record<
	string,
	{
		componentName: string;
		positionalAttr: string;
		defaultPositional?: string;
		numericAttrs?: string[];
	}
> = {
	img: {
		componentName: "Image",
		positionalAttr: "src",
		defaultPositional: "",
		numericAttrs: ["width", "height"],
	},
	audio: {
		componentName: "Audio",
		positionalAttr: "src",
		defaultPositional: "",
	},
	video: {
		componentName: "Video",
		positionalAttr: "src",
		defaultPositional: "",
		numericAttrs: ["width", "height"],
	},
	canvas: {
		componentName: "Canvas",
		positionalAttr: "id",
		defaultPositional: "canvas",
		numericAttrs: ["width", "height"],
	},
};

const DATE_INPUT_COMPONENTS: Record<string, string> = {
	date: "DateInput",
	time: "TimeInput",
	"datetime-local": "DateTimeInput",
};

class DrafterCompiler {
	private cssRules: string[] = [];
	private title: string | null = null;

	constructor(private tree: TreeNode) {}

	private walk(node: TreeNode): string[] {
		if (node.type === "text") {
			return [stringify(this.walkText(node))];
		}
		if (node.type !== "element") {
			return [];
		}
		return this.walkElement(node);
	}

	private walkElement(node: TreeNode): string[] {
		const tag = node.name || "div";

		if (tag === "#document") {
			return this.walkChildren(node);
		}
		if (tag === "#documentType") {
			return [];
		}
		if (PASS_THROUGH_TAGS.has(tag)) {
			return this.walkChildren(node);
		}
		if (NON_RENDERING_TAGS.has(tag)) {
			this.walkChildren(node);
			return [];
		}

		const directComponent = DIRECT_COMPONENT_TAGS[tag];
		if (directComponent) {
			return this.renderDirectComponent(directComponent, node);
		}

		const emptyComponent = EMPTY_COMPONENT_TAGS[tag];
		if (emptyComponent) {
			return this.renderEmptyComponent(emptyComponent, node);
		}

		const listComponent = LIST_COMPONENT_TAGS[tag];
		if (listComponent) {
			return this.renderListComponent(listComponent, node);
		}

		const headingLevel = HEADING_TAG_LEVELS[tag];
		if (headingLevel) {
			return this.renderHeading(node, headingLevel);
		}

		const attributeSpec = ATTRIBUTE_COMPONENT_SPECS[tag];
		if (attributeSpec) {
			return this.renderAttributeDrivenComponent(node, attributeSpec);
		}

		switch (tag) {
			case "style":
				return this.handleStyle(node);
			case "title":
				return this.handleTitle(node);
			case "strong":
				return this.handleStrong(node);
			case "a":
				return this.handleLink(node);
			case "button":
				return this.handleButton(node);
			case "blockquote":
				return this.handleBlockQuote(node);
			case "svg":
				return this.handleSvg(node);
			case "label":
				return this.handleLabel(node);
			case "output":
				return this.handleOutput(node);
			case "progress":
				return this.handleProgress(node);
			case "input":
				return this.handleInput(node);
			case "textarea":
				return this.handleTextArea(node);
			case "select":
				return this.handleSelect(node);
			case "table":
				return this.handleTable(node);
			default:
				return [this.renderHtmlTag(node)];
		}
	}

	private handleStyle(node: TreeNode): string[] {
		for (const css of node.css || []) {
			this.walkCss(css);
		}
		return [];
	}

	private handleTitle(node: TreeNode): string[] {
		const value = this.walkChildren(node).join(" ").trim();
		if (value) {
			this.title = value;
		}
		return [];
	}

	private handleStrong(node: TreeNode): string[] {
		const content = this.walkChildren(node);
		if (content.length === 0) {
			return ["bold('')"];
		}
		if (content.length === 1) {
			return [`bold(${content[0]})`];
		}
		return [`bold([${content.join(", ")}])`];
	}

	private handleLink(node: TreeNode): string[] {
		const text = this.makeSingleContent(this.walkChildren(node));
		const parsed = this.parseAttrs(node);
		const href = this.popAttr(parsed.attributes, "href") || "#";
		return [
			callComponent(
				"Link",
				[text, stringify(href)],
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleButton(node: TreeNode): string[] {
		const text = this.makeSingleContent(this.walkChildren(node));
		const parsed = this.parseAttrs(node);
		const target = this.popFirstAttr(parsed.attributes, TARGET_ATTR_KEYS);
		const args = target ? [text, stringify(target)] : [text];
		return [
			callComponent(
				"Button",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleBlockQuote(node: TreeNode): string[] {
		const content = this.walkChildren(node);
		const parsed = this.parseAttrs(node);
		const cite = this.popAttr(parsed.attributes, "cite");
		const args = cite
			? [stringify(cite), ...content]
			: ["None", ...content];
		return [
			callComponent(
				"BlockQuote",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleSvg(node: TreeNode): string[] {
		const innerHtml = (node.children || [])
			.map((child) => this.serializeNodeAsHtml(child))
			.join("");
		const parsed = this.parseAttrs(node);
		const width = this.readNumeric(
			this.popAttr(parsed.attributes, "width"),
		);
		const height = this.readNumeric(
			this.popAttr(parsed.attributes, "height"),
		);
		const viewBox =
			this.popAttr(parsed.attributes, "viewBox") ||
			this.popAttr(parsed.attributes, "viewbox");

		const args = [stringify(innerHtml)];
		if (width !== undefined) {
			args.push(`width=${width}`);
		}
		if (height !== undefined) {
			args.push(`height=${height}`);
		}
		if (viewBox) {
			args.push(`viewBox=${stringify(viewBox)}`);
		}

		return [
			callComponent(
				"SVG",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleLabel(node: TreeNode): string[] {
		const text = this.makeSingleContent(this.walkChildren(node));
		const parsed = this.parseAttrs(node);
		const forId = this.popAttr(parsed.attributes, "for");
		const args = [text];
		if (forId) {
			args.push(`for_id=${stringify(forId)}`);
		}
		return [
			callComponent(
				"Label",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleOutput(node: TreeNode): string[] {
		const content = this.makeSingleContent(this.walkChildren(node));
		const parsed = this.parseAttrs(node);
		const name =
			this.popAttr(parsed.attributes, "name") ||
			this.popAttr(parsed.attributes, "id") ||
			"output";
		const forId = this.popAttr(parsed.attributes, "for");
		const args = [stringify(name), content];
		if (forId) {
			args.push(`for_id=${stringify(forId)}`);
		}
		return [
			callComponent(
				"Output",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleProgress(node: TreeNode): string[] {
		const parsed = this.parseAttrs(node);
		const value = this.popAttr(parsed.attributes, "value") || "0";
		const max = this.popAttr(parsed.attributes, "max");
		const args = [pythonLiteral(value)];
		if (max !== undefined) {
			args.push(`max=${pythonLiteral(max)}`);
		}
		return [
			callComponent(
				"Progress",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleInput(node: TreeNode): string[] {
		const parsed = this.parseAttrs(node);
		const inputType = (
			this.popAttr(parsed.attributes, "type") || "text"
		).toLowerCase();
		const name =
			this.popAttr(parsed.attributes, "name") ||
			this.popAttr(parsed.attributes, "id") ||
			"field";
		const value = this.popAttr(parsed.attributes, "value");

		if (inputType === "checkbox") {
			const checked = Object.prototype.hasOwnProperty.call(
				parsed.attributes,
				"checked",
			);
			delete parsed.attributes.checked;
			const args = [stringify(name)];
			if (checked) {
				args.push("default_value=True");
			}
			return [
				callComponent(
					"CheckBox",
					args,
					parsed.attributes,
					parsed.styles,
					parsed.classes,
				),
			];
		}

		if (inputType in DATE_INPUT_COMPONENTS) {
			return this.renderNamedInputWithDefault(
				DATE_INPUT_COMPONENTS[inputType],
				name,
				value,
				parsed,
			);
		}

		if (inputType === "file") {
			const args = [stringify(name)];
			const accept = this.popAttr(parsed.attributes, "accept");
			if (accept !== undefined) {
				if (accept.includes(",")) {
					const parts = accept
						.split(",")
						.map((item) => item.trim())
						.filter((item) => item.length > 0)
						.map((item) => stringify(item));
					args.push(`accept=[${parts.join(", ")}]`);
				} else {
					args.push(`accept=${stringify(accept)}`);
				}
			}
			if (
				Object.prototype.hasOwnProperty.call(
					parsed.attributes,
					"multiple",
				)
			) {
				delete parsed.attributes.multiple;
				args.push("multiple=True");
			}
			return [
				callComponent(
					"FileUpload",
					args,
					parsed.attributes,
					parsed.styles,
					parsed.classes,
				),
			];
		}

		if (inputType === "hidden") {
			const args = [
				stringify(name),
				value !== undefined ? pythonLiteral(value) : '""',
			];
			return [
				callComponent(
					"Argument",
					args,
					parsed.attributes,
					parsed.styles,
					parsed.classes,
				),
			];
		}

		const args = [stringify(name)];
		if (value !== undefined) {
			args.push(`default_value=${stringify(value)}`);
		}
		if (inputType !== "text") {
			args.push(`kind=${stringify(inputType)}`);
		}
		return [
			callComponent(
				"TextBox",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleTextArea(node: TreeNode): string[] {
		const parsed = this.parseAttrs(node);
		const name =
			this.popAttr(parsed.attributes, "name") ||
			this.popAttr(parsed.attributes, "id") ||
			"textarea";
		const defaultValue = this.walkChildren(node).join("");
		const args = [stringify(name)];
		if (defaultValue.trim().length > 0) {
			args.push(`default_value=${stringify(defaultValue.trim())}`);
		}
		return [
			callComponent(
				"TextArea",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleSelect(node: TreeNode): string[] {
		const parsed = this.parseAttrs(node);
		const name =
			this.popAttr(parsed.attributes, "name") ||
			this.popAttr(parsed.attributes, "id") ||
			"select";
		const options: string[] = [];
		let defaultValue: string | undefined;

		for (const child of node.children || []) {
			if (child.type !== "element" || child.name !== "option") {
				continue;
			}
			const optionAttrs = child.attrs || {};
			const optionText = this.walkChildren(child).join(" ").trim();
			const value = optionAttrs.value || optionText;
			options.push(stringify(String(value)));
			if (Object.prototype.hasOwnProperty.call(optionAttrs, "selected")) {
				defaultValue = String(value);
			}
		}

		const args = [stringify(name), `[${options.join(", ")}]`];
		if (defaultValue !== undefined) {
			args.push(`default_value=${stringify(defaultValue)}`);
		}
		return [
			callComponent(
				"SelectBox",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private handleTable(node: TreeNode): string[] {
		const parsed = this.parseAttrs(node);
		const rows: string[] = [];
		let header: string[] | null = null;
		const trNodes: TreeNode[] = [];

		for (const child of node.children || []) {
			if (
				child.type === "element" &&
				(child.name === "thead" ||
					child.name === "tbody" ||
					child.name === "tfoot")
			) {
				for (const sub of child.children || []) {
					if (sub.type === "element" && sub.name === "tr") {
						trNodes.push(sub);
					}
				}
			} else if (child.type === "element" && child.name === "tr") {
				trNodes.push(child);
			}
		}

		for (const tr of trNodes) {
			const headerCells: string[] = [];
			const bodyCells: string[] = [];
			for (const cell of tr.children || []) {
				if (cell.type !== "element") {
					continue;
				}
				if (cell.name === "th") {
					headerCells.push(
						this.makeSingleContent(this.walkChildren(cell)),
					);
				}
				if (cell.name === "td") {
					bodyCells.push(
						this.makeSingleContent(this.walkChildren(cell)),
					);
				}
			}
			if (headerCells.length > 0 && !header) {
				header = headerCells;
			}
			if (bodyCells.length > 0) {
				rows.push(`[${bodyCells.join(", ")}]`);
			}
		}

		const args = [`[${rows.join(", ")}]`];
		if (header && header.length > 0) {
			args.push(`header=[${header.join(", ")}]`);
		}
		return [
			callComponent(
				"Table",
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderDirectComponent(
		componentName: string,
		node: TreeNode,
	): string[] {
		const parsed = this.parseAttrs(node);
		const content = this.walkChildren(node);
		return [
			callComponent(
				componentName,
				content,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderEmptyComponent(
		componentName: string,
		node: TreeNode,
	): string[] {
		const parsed = this.parseAttrs(node);
		return [
			callComponent(
				componentName,
				[],
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderListComponent(
		componentName: string,
		node: TreeNode,
	): string[] {
		const parsed = this.parseAttrs(node);
		const items = this.extractListItems(node);
		return [
			callComponent(
				componentName,
				[`[${items.join(", ")}]`],
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderHeading(node: TreeNode, level: number): string[] {
		const parsed = this.parseAttrs(node);
		const body = this.makeSingleContent(this.walkChildren(node));
		return [
			callComponent(
				"Header",
				[body, `level=${level}`],
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderAttributeDrivenComponent(
		node: TreeNode,
		spec: {
			componentName: string;
			positionalAttr: string;
			defaultPositional?: string;
			numericAttrs?: string[];
		},
	): string[] {
		const parsed = this.parseAttrs(node);
		const args: string[] = [
			stringify(
				this.popAttr(parsed.attributes, spec.positionalAttr) ||
					spec.defaultPositional ||
					"",
			),
		];

		for (const key of spec.numericAttrs || []) {
			const numeric = this.readNumeric(
				this.popAttr(parsed.attributes, key),
			);
			if (numeric !== undefined) {
				args.push(`${key}=${numeric}`);
			}
		}

		return [
			callComponent(
				spec.componentName,
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderNamedInputWithDefault(
		componentName: string,
		name: string,
		value: string | undefined,
		parsed: ParsedNodeAttrs,
	): string[] {
		const args = [stringify(name)];
		if (value !== undefined) {
			args.push(`default_value=${stringify(value)}`);
		}
		return [
			callComponent(
				componentName,
				args,
				parsed.attributes,
				parsed.styles,
				parsed.classes,
			),
		];
	}

	private renderHtmlTag(node: TreeNode): string {
		const parsed = this.parseAttrs(node);
		const content = this.walkChildren(node);
		return callHtmlTag(
			node.name || "div",
			content,
			parsed.attributes,
			parsed.styles,
			parsed.classes,
		);
	}

	private walkCss(css: CssRule): void {
		const lines = [css.selector + " {"];
		Object.entries(css.declarations).forEach(([property, value]) => {
			lines.push(`    ${property}: ${value};`);
		});
		lines.push("}");
		this.cssRules.push(lines.join("\n"));
	}

	private extractListItems(node: TreeNode): string[] {
		const items: string[] = [];
		for (const child of node.children || []) {
			if (child.type !== "element" || child.name !== "li") {
				continue;
			}
			items.push(this.makeSingleContent(this.walkChildren(child)));
		}
		return items;
	}

	private walkChildren(node: TreeNode): string[] {
		const result: string[] = [];
		for (const child of node.children || []) {
			result.push(...this.walk(child));
		}
		return result;
	}

	private walkText(node: TreeNode): string {
		return node.text || "";
	}

	private makeSingleContent(parts: string[]): string {
		if (parts.length === 0) {
			return stringify("");
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return `Span(${parts.join(", ")})`;
	}

	private parseAttrs(node: TreeNode): ParsedNodeAttrs {
		const styles: Props = { ...(node.styles || {}) };
		const attributes: Props = {};
		let classes: string | undefined;

		for (const [key, value] of Object.entries(node.attrs || {})) {
			if (key === "class") {
				classes = String(value);
			} else {
				attributes[key] = value === "" ? "true" : String(value);
			}
		}

		return { styles, attributes, classes };
	}

	private popAttr(attrs: Props, key: string): string | undefined {
		const value = attrs[key];
		delete attrs[key];
		return value;
	}

	private popFirstAttr(attrs: Props, keys: string[]): string | undefined {
		for (const key of keys) {
			const value = this.popAttr(attrs, key);
			if (value !== undefined) {
				return value;
			}
		}
		return undefined;
	}

	private readNumeric(value: string | undefined): number | undefined {
		if (!value || !/^\d+$/.test(value)) {
			return undefined;
		}
		return Number(value);
	}

	private serializeNodeAsHtml(node: TreeNode): string {
		if (node.type === "text") {
			return node.text || "";
		}
		if (node.type !== "element") {
			return "";
		}
		const attrs = Object.entries(node.attrs || {})
			.map(([key, value]) => {
				if (value === "") {
					return key;
				}
				return `${key}=${JSON.stringify(value)}`;
			})
			.join(" ");
		const openTag =
			attrs.length > 0 ? `<${node.name} ${attrs}>` : `<${node.name}>`;
		const inner = (node.children || [])
			.map((child) => this.serializeNodeAsHtml(child))
			.join("");
		return `${openTag}${inner}</${node.name}>`;
	}

	compile(): string {
		const bodyPieces = this.walk(this.tree);
		const result: string[] = [];
		if (this.cssRules.length > 0) {
			result.push(cssTemplate(this.cssRules));
		}
		if (bodyPieces.length > 0) {
			result.push(bodyTemplate(bodyPieces.join(",\n")));
		}
		return result.join("\n");
	}
}

function pythonLiteral(
	value: string | number | boolean | null | undefined,
): string {
	if (value === null || value === undefined) {
		return "None";
	}
	if (typeof value === "boolean") {
		return value ? "True" : "False";
	}
	if (typeof value === "number") {
		return String(value);
	}
	if (value === "true") {
		return "True";
	}
	if (value === "false") {
		return "False";
	}
	if (/^-?\d+(\.\d+)?$/.test(value)) {
		return value;
	}
	return stringify(value);
}

function toPythonKwargKey(key: string): string {
	if (key === "for") {
		return "for_id";
	}
	if (key === "class") {
		return "classes";
	}
	return key.replace(/-/g, "_");
}

function callComponent(
	name: string,
	content: string[],
	attrs: Props,
	styles: Props,
	classes: string | undefined,
) {
	const result = [`${name}(`];
	const args: string[] = [];

	if (content.length > 0) {
		args.push(content.join(", "));
	}
	if (Object.keys(attrs).length > 0) {
		Object.entries(attrs).forEach(([key, value]) => {
			args.push(`${toPythonKwargKey(key)}=${pythonLiteral(value)}`);
		});
	}
	if (Object.keys(styles).length > 0) {
		Object.entries(styles).forEach(([key, value]) => {
			const formatted = key.replace(/-/g, "_");
			args.push(`style_${formatted}=${pythonLiteral(value)}`);
		});
	}
	if (classes) {
		args.push(`classes=${pythonLiteral(classes)}`);
	}

	result.push(args.join(", "));
	result.push(")");
	return result.join("");
}

function callHtmlTag(
	tagName: string,
	content: string[],
	attrs: Props,
	styles: Props,
	classes: string | undefined,
) {
	const args = [stringify(tagName), ...content];
	return callComponent("HtmlTag", args, attrs, styles, classes);
}

export function compileTreeToDrafter(tree: TreeNode): string {
	const compiler = new DrafterCompiler(tree);
	return compiler.compile();
}
