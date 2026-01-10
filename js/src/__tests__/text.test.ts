/**
 * Tests for text and layout components in Drafter
 */

import { describe, test, expect, beforeEach, afterEach } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { within } from "@testing-library/dom";
import { runStudentCode, clearDrafterSiteRoot } from "../skulpt.index";

const TEXT_LAYOUT_CODE = `
from drafter import *

hide_debug_information()

@route
def index():
    return Page(None, [
        "Plain text",
        Text(
            "Styled text",
            classes=["fancy", "highlight"],
            style_color="red",
            style_font_weight="bold",
            aria_label="Styled label",
            data_testid="styled-text",
        ),
        Header("Heading Level 3", level=3, data_testid="heading"),
        Text("I am hidden", hidden=True, data_testid="hidden-text"),
        Span("Auto id span", data_testid="span-auto-id"),
        LineBreak(data_testid="line-break"),
        HorizontalRule(data_testid="hr-rule"),
        Span("Span first ", "second ", content=["third"], data_testid="span-merged"),
        Div("Box content", data_testid="div-box", id="custom-div", style_background="pink"),
        Row("Row item", Div("Row child", data_testid="row-child"), data_testid="row-container"),
        NumberedList(["One", "Two"], data_testid="numbered-list"),
        BulletedList(["Red", "Blue"], data_testid="bulleted-list"),
        Pre("preformatted content", style_font_family="monospace", data_testid="pre-block"),
        RawHTML("<span data-testid='raw-html' data-custom='safe'><strong>Raw bold</strong></span>"),
    ])

start_server()
`;

const INVALID_HEADER_CODE = `
from drafter import *

@route
def index():
    return Page(None, [Header("Bad", level=0)])

start_server()
`;

describe("Text and Layout Components", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    afterEach(() => {
        try {
            clearDrafterSiteRoot();
        } catch (err) {
            // ignore if root was not created
        }
    });

    test("renders text elements with styling, attributes, and raw HTML", async () => {
        await runStudentCode({ code: TEXT_LAYOUT_CODE, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
        const app = within(drafterBody as HTMLElement);

        expect(app.getByText(/Plain text/)).toBeTruthy();

        const styled = await app.findByTestId("styled-text");
        expect(styled.tagName).toBe("SPAN");
        expect((styled as HTMLElement).classList.contains("fancy")).toBe(true);
        expect((styled as HTMLElement).classList.contains("highlight")).toBe(
            true
        );
        expect((styled as HTMLElement).getAttribute("aria-label")).toBe(
            "Styled label"
        );
        const styledStyle = (styled as HTMLElement).getAttribute("style") || "";
        expect(styledStyle).toMatch(/color:\s*red/);
        expect(styledStyle).toMatch(/font-weight:\s*bold/);

        const hidden = await app.findByTestId("hidden-text");
        expect(hidden.hasAttribute("hidden")).toBe(true);

        const autoIdSpan = await app.findByTestId("span-auto-id");
        expect(autoIdSpan.id).toMatch(/^drafter-component-/);

        const heading = await app.findByTestId("heading");
        expect(heading.tagName).toBe("H3");
        expect(heading.textContent).toContain("Heading Level 3");

        const raw = await app.findByTestId("raw-html");
        expect(raw.getAttribute("data-custom")).toBe("safe");
        expect(raw.querySelector("strong")).not.toBeNull();
        expect(raw.textContent?.trim()).toBe("Raw bold");
    });

    test("renders layout containers, lists, and structural elements correctly", async () => {
        await runStudentCode({ code: TEXT_LAYOUT_CODE, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
        const app = within(drafterBody as HTMLElement);

        const lineBreak = await app.findByTestId("line-break");
        expect(lineBreak.tagName).toBe("BR");
        const hr = await app.findByTestId("hr-rule");
        expect(hr.tagName).toBe("HR");

        const mergedSpan = await app.findByTestId("span-merged");
        expect(mergedSpan.tagName).toBe("SPAN");
        expect(mergedSpan.textContent).toMatch(/Span\s*first\s*second\s*third/);

        const divBox = await app.findByTestId("div-box");
        expect(divBox.tagName).toBe("DIV");
        expect(divBox.id).toBe("custom-div");
        const divStyle = (divBox as HTMLElement).getAttribute("style") || "";
        expect(divStyle).toMatch(/background:\s*pink/);

        const row = await app.findByTestId("row-container");
        const rowStyle = (row as HTMLElement).getAttribute("style") || "";
        expect(rowStyle).toMatch(/display:\s*flex/);
        expect(rowStyle).toMatch(/flex-direction:\s*row/);
        expect(rowStyle).toMatch(/align-items:\s*center/);
        expect(app.getByTestId("row-child").textContent).toContain("Row child");

        const numbered = await app.findByTestId("numbered-list");
        expect(numbered.tagName).toBe("OL");
        const numberedItems = numbered.querySelectorAll("li");
        expect(numberedItems.length).toBe(2);
        expect(numberedItems[0].textContent).toContain("One");
        expect(numberedItems[1].textContent).toContain("Two");

        const bulleted = await app.findByTestId("bulleted-list");
        expect(bulleted.tagName).toBe("UL");
        const bulletItems = bulleted.querySelectorAll("li");
        expect(bulletItems.length).toBe(2);
        expect(bulletItems[0].textContent).toContain("Red");
        expect(bulletItems[1].textContent).toContain("Blue");

        const preBlock = await app.findByTestId("pre-block");
        expect(preBlock.tagName).toBe("PRE");
        const preStyle = (preBlock as HTMLElement).getAttribute("style") || "";
        expect(preStyle).toMatch(/font-family:\s*monospace/);
    });
});
