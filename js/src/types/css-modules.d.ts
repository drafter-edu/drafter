// CSS files imported from TypeScript are bundled as raw text (see the
// ".css": "text" esbuild loader in tsup.config.ts) so components can inject
// them into their own shadow roots.
declare module "*.css" {
	const content: string;
	export default content;
}
