// Jest setup file - runs before each test file
import '@testing-library/jest-dom';

// Set up any global test utilities here
global.console = {
  ...console,
  // Suppress console errors during tests unless debugging
  error: jest.fn(),
  warn: jest.fn(),
};
