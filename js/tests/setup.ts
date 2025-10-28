/**
 * Jest setup file for Drafter TypeScript client tests.
 * This file runs before each test suite.
 */

// Mock global objects that may not be available in jsdom
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
};

// Setup any global test utilities
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  
  // Reset the DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
});
