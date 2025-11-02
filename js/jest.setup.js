// Global test setup for Jest
// This file is loaded before each test file

// Set up any global mocks or utilities here
global.console = {
  ...console,
  // Suppress console logs during tests (comment out to see logs)
  // log: jest.fn(),
  // debug: jest.fn(),
  // info: jest.fn(),
  // warn: jest.fn(),
  // error: jest.fn(),
};
