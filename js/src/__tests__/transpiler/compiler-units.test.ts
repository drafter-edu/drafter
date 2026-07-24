import { describe, expect, test } from "@jest/globals";

import { parseHtmlCss } from "../../services/transpiler/parser";
import { compileTreeToDrafter } from "../../services/transpiler/compiler";
import { parse } from "py-ast";

/**
 * Unit tests for the HTML→Python transpiler, exercised through the public
 * API (parseHtmlCss + compileTreeToDrafter). Assertions are made against
 * substrings of the generated Python so that the tests stay robust against
 * unrelated formatting changes in the surrounding template.
 */

function compile(html: string): string {
	return compileTreeToDrafter(parseHtmlCss(html));
}

function expectValidPython(code: string): void {
	expect(() => parse(code)).not.toThrow();
}

describe("document structure", () => {
	test("empty document compiles to an empty string", () => {
		expect(compile("")).toEqual("");
	});

	test("whitespace-only document compiles to an empty string", () => {
		expect(compile("   \n\t  ")).toEqual("");
	});

	test("body content is wrapped in an index Page function", () => {
		const code = compile("<p>Hello</p>");
		expect(code).toContain("def index(state: State) -> Page:");
		expect(code).toContain("return Page(state, [");
		expect(code).toContain('Paragraph("Hello")');
		expectValidPython(code);
	});

	test("html/body wrappers pass through without emitting components", () => {
		const code = compile("<html><body><p>Hi</p></body></html>");
		expect(code).toContain('Paragraph("Hi")');
		expect(code).not.toContain("HtmlTag(\"html\"");
		expect(code).not.toContain("HtmlTag(\"body\"");
	});

	test("doctype is ignored", () => {
		const code = compile("<!DOCTYPE html><p>Hi</p>");
		expect(code).toContain('Paragraph("Hi")');
	});

	test("comments are dropped", () => {
		const code = compile("<p>Hi<!-- secret --></p>");
		expect(code).toContain('Paragraph("Hi")');
		expect(code).not.toContain("secret");
	});

	test("title content is consumed but never emitted (current behavior)", () => {
		// The compiler records <title> text internally but compile() never
		// uses it, so the title cannot appear anywhere in the output.
		const code = compile("<title>My Page</title><p>Hi</p>");
		expect(code).toContain('Paragraph("Hi")');
		expect(code).not.toContain("My Page");
	});
});

describe("direct component tags", () => {
	test.each([
		["span", "Span"],
		["div", "Div"],
		["p", "Paragraph"],
		["section", "Section"],
		["article", "Article"],
		["aside", "Aside"],
		["main", "Main"],
		["nav", "Nav"],
		["header", "HeaderContent"],
		["footer", "FooterContent"],
		["code", "InlineCode"],
	])("<%s> maps to %s", (tag, component) => {
		const code = compile(`<${tag}>content</${tag}>`);
		expect(code).toContain(`${component}("content")`);
	});

	test("pre preserves internal newlines with triple-quoted strings", () => {
		const code = compile("<pre>line one\nline two</pre>");
		expect(code).toContain('Pre("""line one\nline two""")');
		expectValidPython(code);
	});

	test("pre containing triple double-quotes falls back to triple single-quotes", () => {
		const code = compile('<pre>say """hi"""\nok</pre>');
		expect(code).toContain("Pre('''say \"\"\"hi\"\"\"\nok''')");
		expectValidPython(code);
	});
});

describe("empty component tags", () => {
	test("<hr> maps to HorizontalRule", () => {
		expect(compile("<hr>")).toContain("HorizontalRule()");
	});

	test("<br> maps to LineBreak inline within its parent", () => {
		const code = compile("<p>a<br>b</p>");
		expect(code).toContain('Paragraph("a", LineBreak(), "b")');
	});
});

describe("headings", () => {
	test.each([[1], [2], [3], [4], [5], [6]])(
		"<h%i> maps to Header with level=%i",
		(level) => {
			const code = compile(`<h${level}>Title</h${level}>`);
			expect(code).toContain(`Header("Title", level=${level})`);
		},
	);

	test("heading with mixed content wraps content in a Span", () => {
		const code = compile("<h1>Hello <em>World</em></h1>");
		expect(code).toContain(
			'Header(Span("Hello", HtmlTag("em", "World")), level=1)',
		);
	});
});

describe("lists", () => {
	test("<ul> maps to BulletedList with li items", () => {
		const code = compile("<ul><li>One</li><li>Two</li></ul>");
		expect(code).toContain('BulletedList(["One", "Two"])');
	});

	test("<ol> maps to NumberedList", () => {
		const code = compile("<ol><li>First</li><li>Second</li></ol>");
		expect(code).toContain('NumberedList(["First", "Second"])');
	});

	test("empty list compiles to an empty item list", () => {
		const code = compile("<ul></ul>");
		expect(code).toContain("BulletedList([])");
	});

	test("list items with nested markup become single Span items", () => {
		const code = compile("<ul><li>a <strong>b</strong></li></ul>");
		expect(code).toContain('BulletedList([Span("a", bold("b"))])');
	});
});

describe("images and media", () => {
	test("<img> maps to Image with src and numeric width/height", () => {
		const code = compile('<img src="cat.png" width="100" height="50">');
		expect(code).toContain('Image("cat.png", width=100, height=50)');
	});

	test("<img> without src uses an empty positional string", () => {
		expect(compile("<img>")).toContain('Image("")');
	});

	test("<img> extra attributes become kwargs", () => {
		const code = compile('<img src="cat.png" alt="A cat">');
		expect(code).toContain('Image("cat.png", alt="A cat")');
	});

	test("non-numeric width/height are silently dropped (current behavior)", () => {
		// SUSPECTED BUG: popAttr removes width from the attribute map even
		// when readNumeric rejects the value, so "50%" is lost entirely
		// instead of being passed through as a kwarg.
		const code = compile('<img src="cat.png" width="50%">');
		expect(code).toContain('Image("cat.png")');
		expect(code).not.toContain("width");
	});

	test("<audio> maps to Audio with src", () => {
		const code = compile('<audio src="song.mp3" controls></audio>');
		expect(code).toContain('Audio("song.mp3", controls=True)');
	});

	test("<video> maps to Video with numeric dimensions", () => {
		const code = compile(
			'<video src="movie.mp4" width="640" height="480"></video>',
		);
		expect(code).toContain('Video("movie.mp4", width=640, height=480)');
	});

	test("<canvas> defaults its positional id to 'canvas'", () => {
		expect(compile("<canvas></canvas>")).toContain('Canvas("canvas")');
	});

	test("<canvas> uses its id attribute as the positional argument", () => {
		const code = compile('<canvas id="game" width="200" height="100"></canvas>');
		expect(code).toContain('Canvas("game", width=200, height=100)');
	});
});

describe("svg", () => {
	test("<svg> serializes children as raw HTML with dimensions and viewBox", () => {
		const code = compile(
			'<svg width="100" height="50" viewBox="0 0 10 10">' +
				'<circle cx="5" cy="5" r="4"></circle></svg>',
		);
		expect(code).toContain(
			"SVG('<circle cx=\"5\" cy=\"5\" r=\"4\"></circle>', " +
				'width=100, height=50, viewBox="0 0 10 10")',
		);
		expectValidPython(code);
	});

	test("<svg> without attributes emits only the serialized markup", () => {
		const code = compile("<svg><rect></rect></svg>");
		expect(code).toContain('SVG("<rect></rect>")');
	});
});

describe("text inputs", () => {
	test("text input maps to TextBox with its name", () => {
		const code = compile('<input type="text" name="username">');
		expect(code).toContain('TextBox("username")');
	});

	test("input without a type defaults to a TextBox", () => {
		const code = compile('<input name="username">');
		expect(code).toContain('TextBox("username")');
		expect(code).not.toContain("kind=");
	});

	test("value attribute becomes default_value", () => {
		const code = compile('<input type="text" name="username" value="bob">');
		expect(code).toContain('TextBox("username", default_value="bob")');
	});

	test("password input keeps TextBox with kind kwarg", () => {
		const code = compile('<input type="password" name="pw">');
		expect(code).toContain('TextBox("pw", kind="password")');
	});

	test("other input types pass through as kind", () => {
		const code = compile('<input type="email" name="contact">');
		expect(code).toContain('TextBox("contact", kind="email")');
	});

	test("name falls back to id, then to 'field'", () => {
		expect(compile('<input type="text" id="user_id">')).toContain(
			'TextBox("user_id")',
		);
		expect(compile('<input type="text">')).toContain('TextBox("field")');
	});

	test("boolean attributes on inputs become True kwargs", () => {
		const code = compile('<input type="text" name="x" disabled>');
		expect(code).toContain('TextBox("x", disabled=True)');
	});
});

describe("checkbox inputs", () => {
	test("checkbox maps to CheckBox", () => {
		const code = compile('<input type="checkbox" name="agree">');
		expect(code).toContain('CheckBox("agree")');
		expect(code).not.toContain("default_value");
	});

	test("checked checkbox sets default_value=True", () => {
		const code = compile('<input type="checkbox" name="agree" checked>');
		expect(code).toContain('CheckBox("agree", default_value=True)');
	});
});

describe("date and time inputs", () => {
	test.each([
		["date", "DateInput"],
		["time", "TimeInput"],
		["datetime-local", "DateTimeInput"],
	])("input type=%s maps to %s", (type, component) => {
		const code = compile(`<input type="${type}" name="when">`);
		expect(code).toContain(`${component}("when")`);
	});

	test("date input with a value gets default_value", () => {
		const code = compile('<input type="date" name="d" value="2024-01-01">');
		expect(code).toContain('DateInput("d", default_value="2024-01-01")');
	});
});

describe("file inputs", () => {
	test("file input maps to FileUpload", () => {
		expect(compile('<input type="file" name="upload">')).toContain(
			'FileUpload("upload")',
		);
	});

	test("single accept value stays a string", () => {
		const code = compile('<input type="file" name="upload" accept="image/png">');
		expect(code).toContain('FileUpload("upload", accept="image/png")');
	});

	test("comma-separated accept becomes a list", () => {
		const code = compile(
			'<input type="file" name="upload" accept=".png, .jpg,.gif">',
		);
		expect(code).toContain(
			'FileUpload("upload", accept=[".png", ".jpg", ".gif"])',
		);
	});

	test("multiple attribute becomes multiple=True", () => {
		const code = compile('<input type="file" name="upload" multiple>');
		expect(code).toContain('FileUpload("upload", multiple=True)');
	});
});

describe("hidden inputs", () => {
	test("hidden input maps to Argument with its value", () => {
		const code = compile('<input type="hidden" name="token" value="abc">');
		expect(code).toContain('Argument("token", "abc")');
	});

	test("numeric hidden values become Python numbers", () => {
		const code = compile('<input type="hidden" name="count" value="5">');
		expect(code).toContain('Argument("count", 5)');
	});

	test("hidden input without a value defaults to an empty string", () => {
		const code = compile('<input type="hidden" name="token">');
		expect(code).toContain('Argument("token", "")');
	});
});

describe("textarea", () => {
	test("textarea maps to TextArea with its name", () => {
		expect(compile('<textarea name="notes"></textarea>')).toContain(
			'TextArea("notes")',
		);
	});

	test("textarea content becomes default_value (double-stringified, current behavior)", () => {
		// SUSPECTED BUG: walkChildren() already stringifies the text child,
		// and handleTextArea stringifies the joined result again, so the
		// default value ends up wrapped in literal quote characters:
		// default_value='"hello world"' instead of default_value="hello world".
		const code = compile('<textarea name="notes">hello world</textarea>');
		expect(code).toContain(
			"TextArea(\"notes\", default_value='\"hello world\"')",
		);
	});

	test("textarea name falls back to id, then to 'textarea'", () => {
		expect(compile('<textarea id="memo"></textarea>')).toContain(
			'TextArea("memo")',
		);
		expect(compile("<textarea></textarea>")).toContain('TextArea("textarea")');
	});
});

describe("select", () => {
	test("select maps to SelectBox with option text (double-stringified, current behavior)", () => {
		// SUSPECTED BUG: when an <option> has no value attribute, the option
		// text has already been stringified by walkChildren(), and
		// handleSelect stringifies it again, producing '"Red"' (literal
		// quotes inside the Python string) instead of "Red".
		const code = compile(
			'<select name="color"><option>Red</option><option>Green</option></select>',
		);
		expect(code).toContain("SelectBox(\"color\", ['\"Red\"', '\"Green\"'])");
	});

	test("option value attributes take precedence over text", () => {
		const code = compile(
			'<select name="color"><option value="r">Red</option></select>',
		);
		expect(code).toContain('SelectBox("color", ["r"])');
	});

	test("selected option becomes default_value", () => {
		// The valued option ("r") is emitted cleanly; the unvalued option is
		// double-stringified (see suspected bug above).
		const code = compile(
			'<select name="color"><option value="r" selected>Red</option>' +
				"<option>Green</option></select>",
		);
		expect(code).toContain(
			"SelectBox(\"color\", [\"r\", '\"Green\"'], default_value=\"r\")",
		);
	});

	test("select name falls back to 'select'", () => {
		expect(compile("<select></select>")).toContain('SelectBox("select", [])');
	});
});

describe("tables", () => {
	test("table with th header row splits header from body rows", () => {
		const code = compile(
			"<table><tr><th>A</th><th>B</th></tr>" +
				"<tr><td>1</td><td>2</td></tr></table>",
		);
		expect(code).toContain('Table([["1", "2"]], header=["A", "B"])');
	});

	test("table without a header row omits the header kwarg", () => {
		const code = compile(
			"<table><tr><td>1</td><td>2</td></tr>" +
				"<tr><td>3</td><td>4</td></tr></table>",
		);
		expect(code).toContain('Table([["1", "2"], ["3", "4"]])');
		expect(code).not.toContain("header=");
	});

	test("thead/tbody wrappers are traversed", () => {
		const code = compile(
			"<table><thead><tr><th>Name</th></tr></thead>" +
				"<tbody><tr><td>Ada</td></tr></tbody></table>",
		);
		expect(code).toContain('Table([["Ada"]], header=["Name"])');
	});

	test("empty table compiles to an empty row list", () => {
		expect(compile("<table></table>")).toContain("Table([])");
	});
});

describe("links and buttons", () => {
	test("<a> maps to Link with text and href", () => {
		const code = compile('<a href="/about">About</a>');
		expect(code).toContain('Link("About", "/about")');
	});

	test("<a> without href defaults to '#'", () => {
		expect(compile("<a>Bare</a>")).toContain('Link("Bare", "#")');
	});

	test("<button> without a target is text-only", () => {
		const code = compile("<button>Click</button>");
		expect(code).toContain('Button("Click")');
	});

	test("<button> uses data-nav as its target", () => {
		const code = compile('<button data-nav="second_page">Go</button>');
		expect(code).toContain('Button("Go", "second_page")');
	});

	test("<button> falls back to formaction targets", () => {
		const code = compile('<button formaction="/submit">Send</button>');
		expect(code).toContain('Button("Send", "/submit")');
	});

	test("data-nav takes precedence; other target attrs remain as kwargs (current behavior)", () => {
		// popFirstAttr stops at the first matching key (data-nav), so the
		// remaining target attributes (href/formaction) are NOT consumed and
		// pass through as ordinary kwargs.
		const code = compile(
			'<button data-nav="page_a" formaction="/b">Go</button>',
		);
		expect(code).toContain('Button("Go", "page_a", formaction="/b")');
	});
});

describe("labels, output, progress", () => {
	test("<label> maps to Label with for_id", () => {
		const code = compile('<label for="username">Name:</label>');
		expect(code).toContain('Label("Name:", for_id="username")');
	});

	test("<label> without for omits for_id", () => {
		const code = compile("<label>Name:</label>");
		expect(code).toContain('Label("Name:")');
		expect(code).not.toContain("for_id");
	});

	test("<output> maps to Output with name and content", () => {
		const code = compile('<output name="result">42</output>');
		expect(code).toContain('Output("result", "42")');
	});

	test("<output> falls back to id, then to 'output', and keeps for_id", () => {
		expect(compile('<output id="sum">3</output>')).toContain(
			'Output("sum", "3")',
		);
		const code = compile('<output for="a b">0</output>');
		expect(code).toContain('Output("output", "0", for_id="a b")');
	});

	test("<progress> maps to Progress with numeric value and max", () => {
		const code = compile('<progress value="30" max="100"></progress>');
		expect(code).toContain("Progress(30, max=100)");
	});

	test("<progress> without a value defaults to 0", () => {
		const code = compile("<progress></progress>");
		expect(code).toContain("Progress(0)");
		expect(code).not.toContain("max=");
	});
});

describe("blockquote", () => {
	test("cite attribute becomes the first positional argument", () => {
		const code = compile(
			'<blockquote cite="https://example.com">Quote</blockquote>',
		);
		expect(code).toContain('BlockQuote("https://example.com", "Quote")');
	});

	test("missing cite becomes None", () => {
		const code = compile("<blockquote>Quote</blockquote>");
		expect(code).toContain('BlockQuote(None, "Quote")');
		expectValidPython(code);
	});
});

describe("strong / bold", () => {
	test("single child becomes bold(...)", () => {
		expect(compile("<strong>Bold</strong>")).toContain('bold("Bold")');
	});

	test("empty strong becomes bold('')", () => {
		expect(compile("<strong></strong>")).toContain("bold('')");
	});

	test("multiple children become a list", () => {
		const code = compile("<strong>a<em>b</em></strong>");
		expect(code).toContain('bold(["a", HtmlTag("em", "b")])');
	});
});

describe("kwarg remapping", () => {
	test("for attribute on a generic tag becomes for_id", () => {
		const code = compile('<div for="thing">x</div>');
		expect(code).toContain('Div("x", for_id="thing")');
	});

	test("hyphenated attributes become underscored kwargs", () => {
		const code = compile('<div data-foo-bar="baz">x</div>');
		expect(code).toContain('Div("x", data_foo_bar="baz")');
	});

	test("class attribute becomes the classes kwarg", () => {
		const code = compile('<div class="big red">x</div>');
		expect(code).toContain('Div("x", classes="big red")');
	});

	test("classes come after other kwargs", () => {
		const code = compile('<div id="a" class="big">x</div>');
		expect(code).toContain('Div("x", id="a", classes="big")');
	});
});

describe("literal generation", () => {
	test("plain text is double-quoted", () => {
		expect(compile("<p>hello</p>")).toContain('Paragraph("hello")');
	});

	test("text containing double quotes prefers single-quoted strings", () => {
		const code = compile('<p>He said "hi"</p>');
		expect(code).toContain("Paragraph('He said \"hi\"')");
		expectValidPython(code);
	});

	test("text containing both quote kinds uses escaped double quotes", () => {
		const code = compile("<p>He's \"fine\"</p>");
		expect(code).toContain('Paragraph("He\'s \\"fine\\"")');
		expectValidPython(code);
	});

	test("numeric attribute values become Python numbers", () => {
		const code = compile('<div data-count="3" data-x="3.14" data-n="-5">x</div>');
		expect(code).toContain("data_count=3");
		expect(code).toContain("data_x=3.14");
		expect(code).toContain("data_n=-5");
	});

	test("leading-zero numeric attributes are emitted verbatim (current behavior)", () => {
		// SUSPECTED BUG: pythonLiteral's numeric regex accepts "007" and
		// emits it verbatim, but 007 is a SyntaxError in Python 3 (leading
		// zeros are not permitted in decimal integer literals).
		const code = compile('<div data-code="007">x</div>');
		expect(code).toContain("data_code=007");
	});

	test("true/false attribute strings become True/False", () => {
		const code = compile('<div draggable="true" spellcheck="false">x</div>');
		expect(code).toContain("draggable=True");
		expect(code).toContain("spellcheck=False");
	});

	test("bare boolean attributes become True", () => {
		const code = compile("<div hidden>x</div>");
		expect(code).toContain('Div("x", hidden=True)');
	});
});

describe("style attributes", () => {
	test("inline styles become style_* kwargs with underscores", () => {
		const code = compile(
			'<div style="background-color: red; font-size: 14px;">x</div>',
		);
		expect(code).toContain('style_background_color="red"');
		expect(code).toContain('style_font_size="14px"');
	});

	test("styles combine with classes and other attributes", () => {
		const code = compile(
			'<p id="msg" class="note" style="color: blue">x</p>',
		);
		expect(code).toContain(
			'Paragraph("x", id="msg", style_color="blue", classes="note")',
		);
	});
});

describe("CSS extraction", () => {
	test("style tags become add_website_css calls", () => {
		const code = compile(
			"<style>body { color: red; } .btn { margin: 4px; }</style><p>Hi</p>",
		);
		expect(code).toContain('add_website_css("""');
		expect(code).toContain("body {");
		expect(code).toContain("color: red;");
		expect(code).toContain(".btn {");
		expect(code).toContain("margin: 4px;");
		expect(code).toContain('Paragraph("Hi")');
		expectValidPython(code);
	});

	test("style-only documents emit CSS but no index page", () => {
		const code = compile("<style>h1 { color: blue; }</style>");
		expect(code).toContain("add_website_css");
		expect(code).not.toContain("def index");
	});

	test("documents without style tags emit no add_website_css", () => {
		expect(compile("<p>Hi</p>")).not.toContain("add_website_css");
	});

	test("style tags in the head are still collected", () => {
		const code = compile(
			"<html><head><style>p { padding: 2px; }</style></head>" +
				"<body><p>Hi</p></body></html>",
		);
		expect(code).toContain("padding: 2px;");
		expect(code).toContain('Paragraph("Hi")');
	});
});

describe("unknown tags and fallbacks", () => {
	test("unknown tags fall back to HtmlTag", () => {
		const code = compile('<widget data-x="1">Hi</widget>');
		expect(code).toContain('HtmlTag("widget", "Hi", data_x=1)');
	});

	test("custom elements keep their hyphenated tag name", () => {
		const code = compile("<my-widget>Hi</my-widget>");
		expect(code).toContain('HtmlTag("my-widget", "Hi")');
	});

	test("common inline tags without direct mappings use HtmlTag", () => {
		const code = compile("<p><em>soft</em></p>");
		expect(code).toContain('HtmlTag("em", "soft")');
	});
});

describe("nesting and malformed HTML", () => {
	test("nested structures compose recursively", () => {
		const code = compile(
			'<div class="outer"><p>Hello <strong>World</strong></p></div>',
		);
		expect(code).toContain(
			'Div(Paragraph("Hello", bold("World")), classes="outer")',
		);
		expectValidPython(code);
	});

	test("unclosed tags are recovered by parse5 and still compile", () => {
		const code = compile("<div><p>unclosed <b>text");
		expect(code).toContain("Div(");
		expect(code).toContain('HtmlTag("b", "text")');
		expectValidPython(code);
	});

	test("stray closing tags do not break compilation", () => {
		const code = compile("</section><p>Hi</p></div>");
		expect(code).toContain('Paragraph("Hi")');
		expectValidPython(code);
	});

	test("a composite document produces parseable Python", () => {
		const code = compile(`
			<style>body { margin: 0; }</style>
			<h1>Form</h1>
			<label for="name">Name</label>
			<input type="text" name="name" value="bob">
			<input type="checkbox" name="ok" checked>
			<select name="c"><option selected>x</option></select>
			<table><tr><th>H</th></tr><tr><td>1</td></tr></table>
			<ul><li>a</li></ul>
			<button data-nav="next">Go</button>
			<img src="pic.png" width="10">
		`);
		expect(code).toContain("add_website_css");
		expect(code).toContain("def index(state: State) -> Page:");
		expectValidPython(code);
	});
});
