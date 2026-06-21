import type { CssNode } from "css-tree";
import type { TreeNode, CssRule } from "./types";

// Other things to potentially capture:
// title element
// meta elements

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
		} else {
			return `"""${text}"""`;
		} // TODO: Handle edge cases with both kinds of triple quotes
	} else {
		return JSON.stringify(text);
	}
}

class DrafterCompiler {
	private lines: string[] = [];
	private cssRules: string[] = [];
	private title: string | null = null;

	private nodeStack: TreeNode[] = [];
	private elementStack: string[] = [];

	constructor(
		private source: string,
		private tree: TreeNode,
	) {}

	private walk(node: TreeNode): string[] {
		console.log("  ".repeat(this.nodeStack.length), node.name);
		const result: string[] = [];
		this.nodeStack.push(node);
		if (node.type === "element") {
			this.elementStack.push(node.name || "");

			const visitorFunction = (this as any)[
				`walkElement_${node.name}`
			] as ((node: TreeNode) => string[]) | undefined;

			if (visitorFunction) {
				result.push(...visitorFunction.call(this, node));
			} else {
				result.push(...this.walkGeneric(node));
			}

			this.elementStack.pop();
		} else if (node.type === "text") {
			result.push(stringify(this.walkText(node)));
		}
		this.nodeStack.pop();
		return result;
	}

	private walkElement_style(node: TreeNode): string[] {
		for (const css of node.css || []) {
			this.walkCss(css);
		}
		return [];
	}

	private walkCss(css: CssRule): void {
		const lines = [css.selector + " {"];
		Object.entries(css.declarations).forEach(([property, value]) => {
			lines.push(`    ${property}: ${value};`);
		});
		lines.push("}");
		this.cssRules.push(lines.join("\n"));
	}

	private walkElement_title(node: TreeNode): string[] {
		return [];
	}

	private walkElement_strong(node: TreeNode): string[] {
		const result = this.walkGeneric(node);
		if (result.length === 0) {
			return ["bold('')"];
		} else if (result.length === 1) {
			return [`bold(${result[0]})`];
		} else {
			return [`bold([${result.join(", ")}])`];
		}
	}

	private makeComponent(name: string, node: TreeNode) {
		const content = this.walkGeneric(node);
		const { styles, attributes, classes } = this.parseAttrs(node);
		return [callComponent(name, content, attributes, styles, classes)];
	}

	private walkElement_button(node: TreeNode): string[] {
		return this.makeComponent("Button", node);
	}

	private walkElement_div(node: TreeNode): string[] {
		return this.makeComponent("Div", node);
	}

	private walkElement_body(node: TreeNode): string[] {
		return this.walkGeneric(node);
	}

	private walkText(node: TreeNode): string {
		return node.text || "";
	}

	private walkGeneric(node: TreeNode): string[] {
		const result = [];
		for (const child of node.children || []) {
			result.push(...this.walk(child));
		}
		return result;
	}

	private parseAttrs(node: TreeNode) {
		let styles: Props = node.styles || {},
			attributes: Props = {},
			classes: string | undefined = undefined;
		if (!node.attrs) {
			return { styles, attributes, classes };
		}
		Object.entries(node.attrs).forEach(([key, value]) => {
			if (key === "class") {
				classes = value;
			} else if (key === "style") {
				Object.entries(value).forEach(([prop, val]) => {
					styles[prop] = val;
				});
			} else {
				attributes[key] = value;
			}
		});
		return {
			styles,
			attributes,
			classes,
		};
	}

	compile(): string {
		const bodyPieces = this.walk(this.tree);
		const result = [];
		if (this.cssRules.length > 0) {
			result.push(cssTemplate(this.cssRules));
		}
		if (bodyPieces.length > 0) {
			result.push(bodyTemplate(bodyPieces.join(",\n")));
		}
		console.log(result);
		return result.join("\n");
	}
}

type Props = Record<string, string>;

function callComponent(
	name: string,
	content: string[],
	attrs: Props,
	styles: Props,
	classes: string | undefined,
) {
	const result = [`${name}(`];
	const args = [];
	if (content.length > 0) {
		args.push(content.join(", "));
	}
	if (Object.keys(attrs).length > 0) {
		Object.entries(attrs).forEach(([key, value]) => {
			args.push(`${key}=${JSON.stringify(value)}`);
		});
	}
	if (Object.keys(styles).length > 0) {
		Object.entries(styles).forEach(([key, value]) => {
			const formatted = key.replace(/-/, "_");
			args.push(`style_${formatted}=${JSON.stringify(value)}`);
		});
	}
	if (classes) {
		args.push(`classes=${JSON.stringify(classes)}`);
	}
	result.push(args.join(", "));
	result.push(")");
	return result.join("");
}

export function compileTreeToDrafter(tree: TreeNode): string {
	const compiler = new DrafterCompiler(JSON.stringify(tree, null, 2), tree);
	const unit = compiler.compile();
	return unit;
}
