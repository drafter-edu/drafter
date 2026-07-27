import { parseHtmlCss } from "../../services/transpiler/parser";
import { compileTreeToDrafter } from "../../services/transpiler/compiler";
import SAMPLE_DOCUMENT1_HTML from "./documents/simple_document.html";
import SAMPLE_DOCUMENT1_JSON from "./documents/simple_document.json";
import SAMPLE_DOCUMENT1_PYTHON from "./documents/simple_document.py";
import COMPONENT_DOCUMENT_HTML from "./documents/component_document.html";
import COMPONENT_DOCUMENT_JSON from "./documents/component_document.json";
import COMPONENT_DOCUMENT_PYTHON from "./documents/component_document.py";
import { parse, unparse } from "py-ast";

function normalizePython(code: string) {
	return unparse(parse(code.replace(/\r\n?/g, "\n")));
}

describe("parseHtmlCss", () => {
	it("should parse HTML and CSS into a tree structure", () => {
		const tree = parseHtmlCss(SAMPLE_DOCUMENT1_HTML);

		const parsed = JSON.stringify(tree, null, 2);
		expect(tree).toBeDefined();

		expect(tree).toEqual(SAMPLE_DOCUMENT1_JSON);
	});
	it("should convert HTML and CSS into Drafter Python code", () => {
		const tree = parseHtmlCss(SAMPLE_DOCUMENT1_HTML);
		const drafterCode = compileTreeToDrafter(tree);
		expect(drafterCode).toContain("add_website_css");
		expect(drafterCode).toContain("def index(state: State) -> Page:");
		const parsedGenerated = normalizePython(drafterCode);
		expect(parsedGenerated).toBeDefined();
		const roundTripGenerated = normalizePython(drafterCode);
		const parsedExpected = normalizePython(SAMPLE_DOCUMENT1_PYTHON);
		expect(roundTripGenerated).toEqual(parsedExpected);
	});

	it("should parse component document HTML and CSS into a tree structure", () => {
		const tree = parseHtmlCss(COMPONENT_DOCUMENT_HTML);

		expect(tree).toBeDefined();
		expect(tree).toEqual(COMPONENT_DOCUMENT_JSON);
	});

	it("should convert component document HTML and CSS into Drafter Python code", () => {
		const tree = parseHtmlCss(COMPONENT_DOCUMENT_HTML);
		const drafterCode = compileTreeToDrafter(tree);

		expect(drafterCode).toContain("add_website_css");
		expect(drafterCode).toContain("def index(state: State) -> Page:");

		const parsedGenerated = normalizePython(drafterCode);
		expect(parsedGenerated).toBeDefined();
		const roundTripGenerated = normalizePython(drafterCode);
		const parsedExpected = normalizePython(COMPONENT_DOCUMENT_PYTHON);
		expect(roundTripGenerated).toEqual(parsedExpected);
	});
});
