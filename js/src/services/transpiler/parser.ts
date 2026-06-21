import * as parse5 from "parse5";
import * as csstree from "css-tree";

import type { TreeNode, CssRule } from "./types";

function parseStyle(cssText: string): Record<string, string> {
	const declarations: Record<string, string> = {};
	const ast = csstree.parse(cssText, { context: "declarationList" });
	csstree.walk(ast, (node: csstree.CssNode) => {
		if (node.type !== "Declaration") return;
		declarations[node.property] = csstree.generate(node.value);
	});
	return declarations;
}

function parseCss(cssText: string): CssRule[] {
	const ast = csstree.parse(cssText);
	const rules: CssRule[] = [];

	csstree.walk(ast, (node: csstree.CssNode) => {
		if (node.type !== "Rule") return;

		const selector = csstree.generate(node.prelude);
		const declarations: Record<string, string> = {};

		node.block.children.forEach((child: csstree.CssNode) => {
			if (child.type === "Declaration") {
				declarations[child.property] = csstree.generate(child.value);
			}
		});

		rules.push({ selector, declarations });
	});

	return rules;
}

function convertHtmlNode(node: any): TreeNode | null {
	if (node.nodeName === "#text") {
		const text = node.value?.trim();
		if (!text) return null;

		return {
			type: "text",
			text,
			children: [],
		};
	}

	if (node.nodeName === "#comment") {
		return {
			type: "comment",
			text: node.data,
			children: [],
		};
	}

	const attrs: Record<string, string> = {};
	let styles: Record<string, string> = {};
	for (const attr of node.attrs ?? []) {
		if (attr.name === "style") {
			styles = parseStyle(attr.value);
		} else {
			attrs[attr.name] = attr.value;
		}
	}

	const children: TreeNode[] = [];

	for (const child of node.childNodes ?? []) {
		const converted = convertHtmlNode(child);
		if (converted) children.push(converted);
	}

	const treeNode: TreeNode = {
		type: "element",
		name: node.tagName ?? node.nodeName,
		attrs,
		styles,
		children,
	};

	if (treeNode.name === "style") {
		const cssText = children
			.filter((child) => child.type === "text")
			.map((child) => child.text)
			.join("\n");

		treeNode.css = parseCss(cssText);
	}

	return treeNode;
}

export function parseHtmlCss(html: string): TreeNode {
	const document = parse5.parse(html);
	return convertHtmlNode(document) as TreeNode;
}
