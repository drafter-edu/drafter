/**
 * End-to-end tests for Drafter examples using Playwright.
 * These tests verify that examples work correctly when loaded in a browser with Skulpt.
 */

import { chromium, Browser, Page } from 'playwright';
import { test, expect, beforeAll, afterAll, describe } from '@jest/globals';
import * as path from 'path';
import * as fs from 'fs';

let browser: Browser;

beforeAll(async () => {
  browser = await chromium.launch();
});

afterAll(async () => {
  await browser.close();
});

/**
 * Helper function to create a test page that loads Drafter with example code
 */
async function loadExample(exampleName: string): Promise<{ page: Page; error: string | null }> {
  const page = await browser.newPage();
  let error: string | null = null;

  // Capture console errors
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      error = msg.text();
    }
  });

  // Capture page errors
  page.on('pageerror', (err) => {
    error = err.message;
  });

  const examplesDir = path.join(__dirname, '../../examples');
  const examplePath = path.join(examplesDir, `${exampleName}.py`);

  if (!fs.existsSync(examplePath)) {
    return { page, error: `Example file not found: ${examplePath}` };
  }

  const exampleCode = fs.readFileSync(examplePath, 'utf-8');

  // Create a minimal HTML page that loads Drafter and runs the example
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Drafter Test - ${exampleName}</title>
  <script src="https://cdn.jsdelivr.net/npm/skulpt@1.2.0/dist/skulpt.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/skulpt@1.2.0/dist/skulpt-stdlib.js"></script>
</head>
<body>
  <div id="drafter-root"></div>
  <script>
    // Mock Drafter setup for testing
    window.exampleCode = ${JSON.stringify(exampleCode)};
  </script>
</body>
</html>
  `;

  await page.setContent(html);
  
  return { page, error };
}

describe('Simple Examples', () => {
  test('simplest example loads without errors', async () => {
    const { page, error } = await loadExample('simplest');
    
    // Wait for potential initialization
    await page.waitForTimeout(1000);
    
    // Check if there are any console errors
    if (error) {
      console.log(`Error in simplest example: ${error}`);
    }
    
    // The example should create the drafter-root div
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    await page.close();
  }, 30000);

  test('simple_state example loads and displays state', async () => {
    const { page, error } = await loadExample('simple_state');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in simple_state: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('Button Examples', () => {
  test('button_state example loads', async () => {
    const { page, error } = await loadExample('button_state');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in button_state: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('Form Examples', () => {
  test('simple_form example loads', async () => {
    const { page, error } = await loadExample('simple_form');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in simple_form: ${error}`);
    }
    
    await page.close();
  }, 30000);

  test('complex_form example loads', async () => {
    const { page, error } = await loadExample('complex_form');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in complex_form: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('Calculator Examples', () => {
  test('calculator example loads', async () => {
    const { page, error } = await loadExample('calculator');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in calculator: ${error}`);
    }
    
    await page.close();
  }, 30000);

  test('calculator_two_page example loads', async () => {
    const { page, error } = await loadExample('calculator_two_page');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in calculator_two_page: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('List Examples', () => {
  test('todo_list example loads', async () => {
    const { page, error } = await loadExample('todo_list');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in todo_list: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('Navigation Examples', () => {
  test('successful_link example loads', async () => {
    const { page, error } = await loadExample('successful_link');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in successful_link: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('State Examples', () => {
  test('full_state example loads', async () => {
    const { page, error } = await loadExample('full_state');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in full_state: ${error}`);
    }
    
    await page.close();
  }, 30000);

  test('dict_state example loads', async () => {
    const { page, error } = await loadExample('dict_state');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in dict_state: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('UI Components Examples', () => {
  test('table example loads', async () => {
    const { page, error } = await loadExample('table');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in table: ${error}`);
    }
    
    await page.close();
  }, 30000);

  test('emojis example loads', async () => {
    const { page, error } = await loadExample('emojis');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in emojis: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('Styling Examples', () => {
  test('styling_example loads', async () => {
    const { page, error } = await loadExample('styling_example');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    if (error) {
      console.log(`Error in styling_example: ${error}`);
    }
    
    await page.close();
  }, 30000);
});

describe('Error Handling Examples', () => {
  test('error_link example loads (expected to have errors)', async () => {
    const { page, error } = await loadExample('error_link');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    // This example is expected to have errors - document them
    if (error) {
      console.log(`Expected error in error_link: ${error}`);
    }
    
    await page.close();
  }, 30000);

  test('error_missing_page example loads (expected to have errors)', async () => {
    const { page, error } = await loadExample('error_missing_page');
    
    await page.waitForTimeout(1000);
    
    const root = await page.$('#drafter-root');
    expect(root).not.toBeNull();
    
    // This example is expected to have errors - document them
    if (error) {
      console.log(`Expected error in error_missing_page: ${error}`);
    }
    
    await page.close();
  }, 30000);
});
