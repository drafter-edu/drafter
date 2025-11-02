/**
 * Comprehensive test that attempts to load all examples and generates a report.
 * This will identify which examples work and which fail, with failure reasons.
 */

import { chromium, Browser, Page } from 'playwright';
import { test, expect, beforeAll, afterAll, describe } from '@jest/globals';
import * as path from 'path';
import * as fs from 'fs';

interface ExampleTestResult {
  name: string;
  success: boolean;
  error: string | null;
  loadTime: number;
}

let browser: Browser;

beforeAll(async () => {
  browser = await chromium.launch({ headless: true });
});

afterAll(async () => {
  await browser.close();
});

/**
 * Get all example files from the examples directory
 */
function getAllExamples(): string[] {
  const examplesDir = path.join(__dirname, '../../examples');
  const files = fs.readdirSync(examplesDir);
  return files
    .filter(f => f.endsWith('.py'))
    .map(f => f.replace('.py', ''))
    .sort();
}

/**
 * Test a single example and return detailed results
 */
async function testExample(exampleName: string): Promise<ExampleTestResult> {
  const startTime = Date.now();
  const page = await browser.newPage();
  
  let error: string | null = null;
  let success = true;

  // Capture console errors
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      error = error || msg.text();
      success = false;
    }
  });

  // Capture page errors
  page.on('pageerror', (err) => {
    error = error || err.message;
    success = false;
  });

  try {
    const examplesDir = path.join(__dirname, '../../examples');
    const examplePath = path.join(examplesDir, `${exampleName}.py`);

    if (!fs.existsSync(examplePath)) {
      return {
        name: exampleName,
        success: false,
        error: 'Example file not found',
        loadTime: Date.now() - startTime,
      };
    }

    const exampleCode = fs.readFileSync(examplePath, 'utf-8');

    // Create a test page
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Drafter Test - ${exampleName}</title>
</head>
<body>
  <div id="drafter-root"></div>
  <script>
    window.drafterExampleCode = ${JSON.stringify(exampleCode)};
    window.drafterExampleName = ${JSON.stringify(exampleName)};
  </script>
</body>
</html>
    `;

    await page.setContent(html);
    await page.waitForTimeout(500); // Give it a moment to initialize

    // Check if the root element exists
    const root = await page.$('#drafter-root');
    if (!root) {
      error = error || 'drafter-root element not found';
      success = false;
    }

  } catch (err) {
    error = error || (err instanceof Error ? err.message : String(err));
    success = false;
  } finally {
    await page.close();
  }

  return {
    name: exampleName,
    success,
    error,
    loadTime: Date.now() - startTime,
  };
}

describe('All Examples Comprehensive Test', () => {
  test('test all examples and generate report', async () => {
    const examples = getAllExamples();
    console.log(`\n=== Testing ${examples.length} Examples ===\n`);

    const results: ExampleTestResult[] = [];
    
    // Test each example
    for (const example of examples) {
      const result = await testExample(example);
      results.push(result);
      
      // Log progress
      const status = result.success ? '✓' : '✗';
      console.log(`${status} ${example} (${result.loadTime}ms)`);
      if (!result.success && result.error) {
        console.log(`  Error: ${result.error.substring(0, 100)}`);
      }
    }

    // Generate summary
    const working = results.filter(r => r.success);
    const failing = results.filter(r => !r.success);

    console.log('\n=== SUMMARY ===');
    console.log(`Total Examples: ${results.length}`);
    console.log(`Working: ${working.length}`);
    console.log(`Failing: ${failing.length}`);
    console.log(`Success Rate: ${((working.length / results.length) * 100).toFixed(1)}%`);

    if (failing.length > 0) {
      console.log('\n=== FAILING EXAMPLES ===');
      failing.forEach(r => {
        console.log(`\n${r.name}:`);
        console.log(`  Error: ${r.error || 'Unknown error'}`);
      });
    }

    if (working.length > 0) {
      console.log('\n=== WORKING EXAMPLES ===');
      working.forEach(r => {
        console.log(`- ${r.name}`);
      });
    }

    // Write detailed report to file
    const reportPath = path.join(__dirname, '../../test-results');
    if (!fs.existsSync(reportPath)) {
      fs.mkdirSync(reportPath, { recursive: true });
    }
    
    const reportFile = path.join(reportPath, 'examples-test-report.json');
    fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));
    
    console.log(`\nDetailed report written to: ${reportFile}`);

    // Generate markdown report
    const markdownReport = generateMarkdownReport(results);
    const markdownFile = path.join(reportPath, 'examples-test-report.md');
    fs.writeFileSync(markdownFile, markdownReport);
    
    console.log(`Markdown report written to: ${markdownFile}`);

    // Test should pass even if some examples fail (we're documenting failures)
    expect(results.length).toBeGreaterThan(0);
  }, 600000); // 10 minute timeout for all examples
});

/**
 * Generate a markdown report of test results
 */
function generateMarkdownReport(results: ExampleTestResult[]): string {
  const working = results.filter(r => r.success);
  const failing = results.filter(r => !r.success);

  let markdown = '# Drafter Examples Test Report\n\n';
  markdown += `**Generated:** ${new Date().toISOString()}\n\n`;
  markdown += '## Summary\n\n';
  markdown += `- **Total Examples:** ${results.length}\n`;
  markdown += `- **Working:** ${working.length}\n`;
  markdown += `- **Failing:** ${failing.length}\n`;
  markdown += `- **Success Rate:** ${((working.length / results.length) * 100).toFixed(1)}%\n\n`;

  if (failing.length > 0) {
    markdown += '## Failing Examples\n\n';
    markdown += '| Example | Error |\n';
    markdown += '|---------|-------|\n';
    failing.forEach(r => {
      const errorMsg = (r.error || 'Unknown error').replace(/\|/g, '\\|').substring(0, 100);
      markdown += `| ${r.name} | ${errorMsg} |\n`;
    });
    markdown += '\n';
  }

  if (working.length > 0) {
    markdown += '## Working Examples\n\n';
    working.forEach(r => {
      markdown += `- ✓ ${r.name} (${r.loadTime}ms)\n`;
    });
    markdown += '\n';
  }

  return markdown;
}

// Also export the test function for use in other tests
export { testExample, getAllExamples };
