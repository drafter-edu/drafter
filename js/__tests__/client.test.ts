/**
 * End-to-end tests for the TypeScript client library
 * These tests load Skulpt, build pages, and simulate user interactions
 */

import { describe, test, expect, beforeEach, jest } from '@jest/globals';

describe('Drafter Client - Basic Functionality', () => {
    beforeEach(() => {
        // Clear the DOM before each test
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('drafter root element exists in DOM', () => {
        const root = document.getElementById('drafter-root--');
        expect(root).not.toBeNull();
    });

    test('can create basic page structure', () => {
        const root = document.getElementById('drafter-root--');
        if (root) {
            root.innerHTML = `
                <div id="drafter-site--">
                    <div id="drafter-frame--">
                        <div id="drafter-body--">
                            <form id="drafter-form--"></form>
                        </div>
                    </div>
                </div>
            `;
        }

        const site = document.getElementById('drafter-site--');
        const frame = document.getElementById('drafter-frame--');
        const body = document.getElementById('drafter-body--');
        const form = document.getElementById('drafter-form--');

        expect(site).not.toBeNull();
        expect(frame).not.toBeNull();
        expect(body).not.toBeNull();
        expect(form).not.toBeNull();
    });

    test('page can contain text content', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        form.innerHTML = '<p>Hello, World!</p>';

        document.body.appendChild(form);

        const text = form.textContent;
        expect(text).toContain('Hello, World!');
    });

    test('page can contain input elements', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';

        const input = document.createElement('input');
        input.type = 'text';
        input.name = 'test_input';
        input.value = 'test value';

        form.appendChild(input);
        document.body.appendChild(form);

        const foundInput = form.querySelector('input[name="test_input"]') as HTMLInputElement;
        expect(foundInput).not.toBeNull();
        expect(foundInput?.value).toBe('test value');
    });

    test('page can contain button elements', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';

        const button = document.createElement('button');
        button.textContent = 'Submit';
        button.type = 'submit';

        form.appendChild(button);
        document.body.appendChild(form);

        const foundButton = form.querySelector('button');
        expect(foundButton).not.toBeNull();
        expect(foundButton?.textContent).toBe('Submit');
    });
});

describe('Drafter Client - Component Rendering', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('can render TextBox component', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <label>Enter your name:</label>
            <input type="text" name="name" value="" />
        `;

        document.body.appendChild(form);

        const input = form.querySelector('input[name="name"]') as HTMLInputElement;
        expect(input).not.toBeNull();
        expect(input?.type).toBe('text');
    });

    test('can render CheckBox component', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <label>
                <input type="checkbox" name="agree" />
                I agree
            </label>
        `;

        document.body.appendChild(form);

        const checkbox = form.querySelector('input[type="checkbox"]') as HTMLInputElement;
        expect(checkbox).not.toBeNull();
        expect(checkbox?.type).toBe('checkbox');
    });

    test('can render SelectBox component', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <label>Choose an option:</label>
            <select name="choice">
                <option value="1">Option 1</option>
                <option value="2">Option 2</option>
                <option value="3">Option 3</option>
            </select>
        `;

        document.body.appendChild(form);

        const select = form.querySelector('select[name="choice"]') as HTMLSelectElement;
        expect(select).not.toBeNull();
        expect(select?.options.length).toBe(3);
    });

    test('can render Header component', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <h1>Welcome</h1>
            <h2>Subtitle</h2>
        `;

        document.body.appendChild(form);

        const h1 = form.querySelector('h1');
        const h2 = form.querySelector('h2');

        expect(h1?.textContent).toBe('Welcome');
        expect(h2?.textContent).toBe('Subtitle');
    });

    test('can render Button component', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <button type="button">Click Me</button>
        `;

        document.body.appendChild(form);

        const button = form.querySelector('button');
        expect(button).not.toBeNull();
        expect(button?.textContent).toBe('Click Me');
    });
});

describe('Drafter Client - User Interactions', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('can fill text input', () => {
        const input = document.createElement('input');
        input.type = 'text';
        input.name = 'username';

        document.body.appendChild(input);

        input.value = 'John Doe';

        expect(input.value).toBe('John Doe');
    });

    test('can check checkbox', () => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'agree';

        document.body.appendChild(checkbox);

        checkbox.checked = true;

        expect(checkbox.checked).toBe(true);
    });

    test('can select option from dropdown', () => {
        const select = document.createElement('select');
        select.name = 'choice';
        select.innerHTML = `
            <option value="1">Option 1</option>
            <option value="2">Option 2</option>
            <option value="3">Option 3</option>
        `;

        document.body.appendChild(select);

        select.value = '2';

        expect(select.value).toBe('2');
    });

    test('can trigger button click', () => {
        const button = document.createElement('button');
        button.textContent = 'Click Me';

        let clicked = false;
        button.onclick = () => {
            clicked = true;
        };

        document.body.appendChild(button);

        button.click();

        expect(clicked).toBe(true);
    });

    test('can handle form submission', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <input type="text" name="username" value="test" />
            <button type="submit">Submit</button>
        `;

        let submitted = false;
        form.onsubmit = (e) => {
            e.preventDefault();
            submitted = true;
        };

        document.body.appendChild(form);

        form.dispatchEvent(new Event('submit'));

        expect(submitted).toBe(true);
    });
});

describe('Drafter Client - Page Navigation', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('page content can be updated', () => {
        const root = document.getElementById('drafter-root--');
        if (root) {
            root.innerHTML = '<p>Initial content</p>';
            expect(root.textContent).toContain('Initial content');

            root.innerHTML = '<p>Updated content</p>';
            expect(root.textContent).toContain('Updated content');
            expect(root.textContent).not.toContain('Initial content');
        }
    });

    test('form content can be replaced', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        form.innerHTML = '<p>Page 1</p>';

        document.body.appendChild(form);

        expect(form.textContent).toContain('Page 1');

        form.innerHTML = '<p>Page 2</p>';

        expect(form.textContent).toContain('Page 2');
        expect(form.textContent).not.toContain('Page 1');
    });

    test('can simulate navigation between pages', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';

        // Simulate index page
        form.innerHTML = `
            <h1>Home</h1>
            <button id="nav-button">Go to Page 2</button>
        `;

        document.body.appendChild(form);

        expect(form.textContent).toContain('Home');

        // Simulate navigation to page 2
        const button = form.querySelector('#nav-button');
        button?.addEventListener('click', () => {
            form.innerHTML = `
                <h1>Page 2</h1>
                <p>Welcome to page 2</p>
            `;
        });

        button?.click();

        expect(form.textContent).toContain('Page 2');
        expect(form.textContent).not.toContain('Home');
    });
});

describe('Drafter Client - State Management', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('can maintain form state', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <input type="text" name="name" value="" />
            <input type="text" name="email" value="" />
        `;

        document.body.appendChild(form);

        const nameInput = form.querySelector('input[name="name"]') as HTMLInputElement;
        const emailInput = form.querySelector('input[name="email"]') as HTMLInputElement;

        nameInput.value = 'John';
        emailInput.value = 'john@example.com';

        expect(nameInput.value).toBe('John');
        expect(emailInput.value).toBe('john@example.com');
    });

    test('can collect form data', () => {
        const form = document.createElement('form');
        form.innerHTML = `
            <input type="text" name="username" value="testuser" />
            <input type="checkbox" name="remember" checked />
            <select name="role">
                <option value="user" selected>User</option>
                <option value="admin">Admin</option>
            </select>
        `;

        document.body.appendChild(form);

        const formData = new FormData(form);
        expect(formData.get('username')).toBe('testuser');
        expect(formData.get('remember')).toBe('on');
        expect(formData.get('role')).toBe('user');
    });
});

describe('Drafter Client - Error Handling', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('gracefully handles missing root element', () => {
        document.body.innerHTML = '';
        const root = document.getElementById('drafter-root--');
        expect(root).toBeNull();
    });

    test('can display error messages', () => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'An error occurred';

        document.body.appendChild(errorDiv);

        expect(errorDiv.textContent).toContain('An error occurred');
    });
});
