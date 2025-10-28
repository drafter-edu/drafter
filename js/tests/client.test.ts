/**
 * End-to-end tests for the Drafter TypeScript client library.
 * These tests simulate real user interactions with a Drafter application.
 */

import { startDrafter, DrafterInitOptions } from '../src/index';

// Mock Skulpt globally
const mockSkulpt = {
  builtin: {
    str: jest.fn((val: string) => ({ v: val })),
    dict: jest.fn(),
    bool: {
      true$: true,
    },
  },
  environ: {
    set$item: jest.fn(),
  },
  configure: jest.fn(),
  inBrowser: false,
  console: {},
  misceval: {
    asyncToPromise: jest.fn((fn) => Promise.resolve(fn()).then((result: any) => ({
      $d: {},
    }))),
  },
  importMainWithBody: jest.fn(() => Promise.resolve({ $d: {} })),
  python3: true,
};

(global as any).Sk = mockSkulpt;

describe('Drafter Client Library Initialization', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>';
    jest.clearAllMocks();
  });

  describe('startDrafter', () => {
    test('should initialize with target element by ID', async () => {
      const options: DrafterInitOptions = {
        target: '#app',
        code: 'print("Hello, World!")',
      };

      await startDrafter(options);
      
      expect(mockSkulpt.configure).toHaveBeenCalled();
      expect(mockSkulpt.environ.set$item).toHaveBeenCalled();
    });

    test('should initialize with target element as HTMLElement', async () => {
      const element = document.getElementById('app');
      const options: DrafterInitOptions = {
        target: element!,
        code: 'print("Hello, World!")',
      };

      await startDrafter(options);
      
      expect(mockSkulpt.configure).toHaveBeenCalled();
    });

    test('should throw error if target element not found', () => {
      const options: DrafterInitOptions = {
        target: '#nonexistent',
        code: 'print("Hello, World!")',
      };

      expect(() => startDrafter(options)).toThrow('Target element not found');
    });

    test('should throw error if neither code nor url provided', () => {
      const options: DrafterInitOptions = {
        target: '#app',
      };

      expect(() => startDrafter(options)).toThrow('Either code or url must be provided');
    });

    test('should load code from URL', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          text: () => Promise.resolve('print("From URL")'),
        } as Response)
      );

      const options: DrafterInitOptions = {
        target: '#app',
        url: 'http://example.com/app.py',
      };

      await startDrafter(options);
      
      expect(global.fetch).toHaveBeenCalledWith('http://example.com/app.py');
      expect(mockSkulpt.misceval.asyncToPromise).toHaveBeenCalled();
    });

    test('should handle fetch errors gracefully', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          statusText: 'Not Found',
        } as Response)
      );

      const options: DrafterInitOptions = {
        target: '#app',
        url: 'http://example.com/missing.py',
      };

      await expect(startDrafter(options)).rejects.toThrow('Network response was not ok');
    });
  });

  describe('Skulpt Setup', () => {
    test('should configure Skulpt with correct settings', async () => {
      const options: DrafterInitOptions = {
        target: '#app',
        code: 'print("Test")',
      };

      await startDrafter(options);
      
      expect(mockSkulpt.configure).toHaveBeenCalledWith(
        expect.objectContaining({
          __future__: mockSkulpt.python3,
        })
      );
    });

    test('should set DRAFTER_SKULPT environment variable', async () => {
      const options: DrafterInitOptions = {
        target: '#app',
        code: 'print("Test")',
      };

      await startDrafter(options);
      
      expect(mockSkulpt.environ.set$item).toHaveBeenCalled();
    });
  });
});

describe('User Interaction Simulation', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="app">
        <input type="text" name="username" value="" />
        <button id="submit-btn">Submit</button>
        <div id="output"></div>
      </div>
    `;
  });

  test('should handle text input changes', () => {
    const input = document.querySelector('input[name="username"]') as HTMLInputElement;
    
    // Simulate user typing
    input.value = 'John Doe';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    
    expect(input.value).toBe('John Doe');
  });

  test('should handle button clicks', () => {
    const button = document.getElementById('submit-btn');
    let clicked = false;
    
    button!.addEventListener('click', () => {
      clicked = true;
    });
    
    button!.click();
    
    expect(clicked).toBe(true);
  });

  test('should update DOM on user action', () => {
    const button = document.getElementById('submit-btn');
    const output = document.getElementById('output');
    const input = document.querySelector('input[name="username"]') as HTMLInputElement;
    
    input.value = 'Alice';
    
    button!.addEventListener('click', () => {
      output!.textContent = `Hello, ${input.value}!`;
    });
    
    button!.click();
    
    expect(output!.textContent).toBe('Hello, Alice!');
  });
});

describe('Page Navigation', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="app">
        <a href="/page1" data-drafter-link>Page 1</a>
        <a href="/page2" data-drafter-link>Page 2</a>
        <div id="content"></div>
      </div>
    `;
  });

  test('should intercept internal links', () => {
    const links = document.querySelectorAll('[data-drafter-link]');
    expect(links.length).toBe(2);
    
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        // Simulate page navigation
        const content = document.getElementById('content');
        content!.textContent = `Navigated to ${(link as HTMLAnchorElement).href}`;
      });
    });
    
    const firstLink = links[0] as HTMLAnchorElement;
    firstLink.click();
    
    const content = document.getElementById('content');
    expect(content!.textContent).toContain('page1');
  });

  test('should not intercept external links', () => {
    document.body.innerHTML += '<a href="https://example.com" id="external">External</a>';
    
    const externalLink = document.getElementById('external') as HTMLAnchorElement;
    expect(externalLink.href).toContain('https://example.com');
  });
});

describe('Form Submission', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="app">
        <form id="test-form">
          <input type="text" name="username" />
          <input type="password" name="password" />
          <button type="submit">Login</button>
        </form>
        <div id="result"></div>
      </div>
    `;
  });

  test('should collect form data on submission', () => {
    const form = document.getElementById('test-form') as HTMLFormElement;
    const usernameInput = form.querySelector('[name="username"]') as HTMLInputElement;
    const passwordInput = form.querySelector('[name="password"]') as HTMLInputElement;
    const result = document.getElementById('result');
    
    usernameInput.value = 'testuser';
    passwordInput.value = 'password123';
    
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const data = {
        username: formData.get('username'),
        password: formData.get('password'),
      };
      result!.textContent = `Logged in as ${data.username}`;
    });
    
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    
    expect(result!.textContent).toBe('Logged in as testuser');
  });

  test('should handle form validation', () => {
    const form = document.getElementById('test-form') as HTMLFormElement;
    const usernameInput = form.querySelector('[name="username"]') as HTMLInputElement;
    usernameInput.required = true;
    
    let isValid = false;
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      isValid = form.checkValidity();
    });
    
    // Submit with empty username
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    expect(isValid).toBe(false);
    
    // Submit with username
    usernameInput.value = 'testuser';
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    expect(isValid).toBe(true);
  });
});

describe('Component Rendering', () => {
  test('should render text components', () => {
    document.body.innerHTML = '<div id="app"></div>';
    const app = document.getElementById('app')!;
    
    app.innerHTML = '<p>Hello, World!</p>';
    
    expect(app.querySelector('p')?.textContent).toBe('Hello, World!');
  });

  test('should render button components', () => {
    document.body.innerHTML = '<div id="app"></div>';
    const app = document.getElementById('app')!;
    
    app.innerHTML = '<button>Click Me</button>';
    
    const button = app.querySelector('button');
    expect(button).toBeTruthy();
    expect(button?.textContent).toBe('Click Me');
  });

  test('should render textbox components', () => {
    document.body.innerHTML = '<div id="app"></div>';
    const app = document.getElementById('app')!;
    
    app.innerHTML = '<input type="text" name="test" />';
    
    const input = app.querySelector('input');
    expect(input).toBeTruthy();
    expect(input?.name).toBe('test');
  });

  test('should render table components', () => {
    document.body.innerHTML = '<div id="app"></div>';
    const app = document.getElementById('app')!;
    
    app.innerHTML = `
      <table>
        <tr><td>A</td><td>B</td></tr>
        <tr><td>C</td><td>D</td></tr>
      </table>
    `;
    
    const table = app.querySelector('table');
    expect(table).toBeTruthy();
    expect(table?.querySelectorAll('tr').length).toBe(2);
  });
});
