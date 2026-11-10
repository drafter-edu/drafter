/**
 * Entry point of the lazily loaded HTML-to-Drafter converter bundle
 * (dist/js/drafter.transpiler.js, global `DrafterTranspiler`).
 *
 * The converter depends on an HTML parser and a CSS parser that together
 * are about a third the size of Drafter's main bundle, so it is kept out of
 * that bundle and fetched only when someone opens the converter dialog (see
 * loadLazyBundle in lazy.ts).
 */
import { compileTreeToDrafter } from "./services/transpiler/compiler";
import { parseHtmlCss } from "./services/transpiler/parser";

/** Turn HTML (with any CSS in its style tags) into Drafter Python code. */
export function convertHtmlToDrafter(html: string): string {
	return compileTreeToDrafter(parseHtmlCss(html));
}
