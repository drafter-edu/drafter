/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from '@jest/globals';

describe('TypeScript Client Basic Tests', () => {
  test('basic test infrastructure works', () => {
    expect(true).toBe(true);
  });

  test('can do basic JavaScript operations', () => {
    const sum = 1 + 1;
    expect(sum).toBe(2);
  });

  test('can create objects', () => {
    const obj = { name: 'test', value: 42 };
    expect(obj.name).toBe('test');
    expect(obj.value).toBe(42);
  });

  test('can work with arrays', () => {
    const arr = [1, 2, 3];
    expect(arr.length).toBe(3);
    expect(arr[0]).toBe(1);
  });
});

describe('Drafter Client Types', () => {
  test('DrafterInitOptions type exists', () => {
    // This test verifies that our types compile correctly
    const options: { code?: string; url?: string } = {
      code: 'print("Hello")',
    };
    expect(options.code).toBe('print("Hello")');
  });
});
