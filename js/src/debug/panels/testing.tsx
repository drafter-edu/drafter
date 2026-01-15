import * as Diff2Html from "diff2html";
import { Panel } from "./panel";
import type { TestCaseEvent } from "../telemetry/tests";
import type { ReactElement } from "jsx-dom";

export class TestPanel extends Panel {
    private tests: TestCaseEvent[] = [];

    constructor(containerId: string, instanceId: number) {
        super(containerId, instanceId, "drafter-debug-tests", "Your Tests");
    }

    protected get initialContent() {
        return (
            <>
                <div
                    class={`drafter-debug-current-tests-summary drafter-debug-current-tests-summary-${this.instanceId}`}
                ></div>
                <br></br>
                <strong>Details: </strong>
                <div
                    class={`drafter-debug-current-tests-content-list drafter-debug-current-tests-content-list-${this.instanceId}`}
                ></div>
            </>
        );
    }

    public renderTest(testCase: TestCaseEvent): void {
        this.tests.push(testCase);
        const testList = this.queryWithin(
            this.scopedSelector("drafter-debug-current-tests-content-list"),
            "DebugPanel: Tests section not found."
        );

        const statusIcon = testCase.passed ? "✅" : "❌";
        const statusClass = testCase.passed ? "test-passed" : "test-failed";

        const testElement = (
            <div class={`test-case ${statusClass}`}>
                <div class="test-case-header">
                    <span class="test-status">{statusIcon}</span>
                    <span class="test-line">Line {testCase.line}</span>
                    <code class="test-caller">{testCase.caller}</code>
                </div>
                <div class="test-case-diff"></div>
            </div>
        );

        testList.appendChild(testElement);

        this.addDiffToTestElement(testCase, testElement);
    }

    private addDiffToTestElement(
        testCase: TestCaseEvent,
        testElement: ReactElement
    ): void {
        if (!testCase.passed) {
            const diffString = testCase.diff_html;

            console.log(diffString);

            const diffContainer = testElement.querySelector(".test-case-diff");
            if (diffContainer) {
                diffContainer.innerHTML = Diff2Html.html(diffString, {
                    drawFileList: false,
                    matching: "words",
                    diffStyle: "char",
                    outputFormat: "side-by-side",
                    // outputFormat: "line-by-line",
                });
            } else {
                throw new Error("DebugPanel: Diff container not found.");
            }
        }
    }

    public updateTestSummary(): void {
        const summaryElement = this.queryWithin(
            this.scopedSelector("drafter-debug-current-tests-summary"),
            "DebugPanel: Test summary section not found."
        );

        const totalTests = this.tests.length;
        const passedTests = this.tests.filter((t) => t.passed).length;
        const failedTests = totalTests - passedTests;

        summaryElement.replaceChildren(
            <div class="test-summary">
                <strong>Summary:</strong>
                <div>Total Tests: {totalTests}</div>
                <div>✅ Passed: {passedTests}</div>
                <div>❌ Failed: {failedTests}</div>
            </div>
        );
    }
}
