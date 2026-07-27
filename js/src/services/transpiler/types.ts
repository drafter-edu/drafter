export type TreeNode = {
	type: string;
	name?: string;
	text?: string;
	attrs?: Record<string, string>;
	styles?: Record<string, string>;
	css?: CssRule[];
	children: TreeNode[];
};

export type CssRule = {
	selector: string;
	declarations: Record<string, string>;
};
