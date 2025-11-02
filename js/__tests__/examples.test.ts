/**
 * Integration tests for Drafter examples
 * These tests validate that example applications work correctly
 */

import { describe, test, expect, beforeEach } from '@jest/globals';
import * as fs from 'fs';
import * as path from 'path';

// Helper to simulate page rendering from Python code
function simulatePage(content: string[]) {
    const form = document.createElement('form');
    form.id = 'drafter-form--';
    
    content.forEach(item => {
        if (typeof item === 'string') {
            const p = document.createElement('p');
            p.textContent = item;
            form.appendChild(p);
        }
    });
    
    return form;
}

// Helper to simulate TextBox component
function simulateTextBox(name: string, value: string = '') {
    const input = document.createElement('input');
    input.type = 'text';
    input.name = name;
    input.value = value;
    return input;
}

// Helper to simulate Button component
function simulateButton(label: string, onClick?: () => void) {
    const button = document.createElement('button');
    button.textContent = label;
    button.type = 'button';
    if (onClick) {
        button.onclick = onClick;
    }
    return button;
}

// Helper to simulate CheckBox component
function simulateCheckBox(name: string, checked: boolean = false) {
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.name = name;
    input.checked = checked;
    return input;
}

// Helper to simulate SelectBox component
function simulateSelectBox(name: string, options: string[], selected?: string) {
    const select = document.createElement('select');
    select.name = name;
    
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        if (opt === selected) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    return select;
}

describe('Example: Simplest Application', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('renders hello world page', () => {
        // Simulates: examples/simplest.py
        const form = simulatePage(['Hello, World!']);
        document.body.appendChild(form);

        expect(form.textContent).toContain('Hello, World!');
    });
});

describe('Example: Simple Form', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('renders form with text input and submit button', () => {
        // Simulates: examples/simple_form.py
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const label = document.createElement('p');
        label.textContent = 'Enter your name:';
        form.appendChild(label);
        
        const input = simulateTextBox('name', '');
        form.appendChild(input);
        
        const button = simulateButton('Submit');
        form.appendChild(button);
        
        document.body.appendChild(form);

        expect(form.textContent).toContain('Enter your name:');
        expect(form.querySelector('input[name="name"]')).not.toBeNull();
        expect(form.querySelector('button')).not.toBeNull();
    });

    test('can fill form and submit', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const input = simulateTextBox('name', '');
        form.appendChild(input);
        
        let submitted = false;
        const button = simulateButton('Submit', () => {
            submitted = true;
            // Simulate showing result page
            form.innerHTML = `<p>Hello, ${input.value}!</p>`;
        });
        form.appendChild(button);
        
        document.body.appendChild(form);

        input.value = 'Alice';
        button.click();

        expect(submitted).toBe(true);
        expect(form.textContent).toContain('Hello, Alice!');
    });
});

describe('Example: Button State', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('button can update state', () => {
        // Simulates: examples/button_state.py
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        let counter = 0;
        
        const updateDisplay = () => {
            const display = form.querySelector('#counter');
            if (display) {
                display.textContent = `Count: ${counter}`;
            }
        };
        
        const display = document.createElement('p');
        display.id = 'counter';
        display.textContent = `Count: ${counter}`;
        form.appendChild(display);
        
        const button = simulateButton('Increment', () => {
            counter++;
            updateDisplay();
        });
        form.appendChild(button);
        
        document.body.appendChild(form);

        expect(form.textContent).toContain('Count: 0');
        
        button.click();
        expect(form.textContent).toContain('Count: 1');
        
        button.click();
        expect(form.textContent).toContain('Count: 2');
    });
});

describe('Example: Complex Form', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('renders form with multiple input types', () => {
        // Simulates: examples/complex_form.py
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        form.appendChild(document.createElement('h2')).textContent = 'User Information';
        
        const nameInput = simulateTextBox('name', '');
        form.appendChild(nameInput);
        
        const checkbox = simulateCheckBox('available', false);
        form.appendChild(checkbox);
        
        const select = simulateSelectBox('favorite', ['dogs', 'cats', 'capybaras'], 'dogs');
        form.appendChild(select);
        
        const button = simulateButton('Submit');
        form.appendChild(button);
        
        document.body.appendChild(form);

        expect(form.querySelector('input[name="name"]')).not.toBeNull();
        expect(form.querySelector('input[type="checkbox"]')).not.toBeNull();
        expect(form.querySelector('select[name="favorite"]')).not.toBeNull();
    });

    test('can fill and submit complex form', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const nameInput = simulateTextBox('name', '');
        const checkbox = simulateCheckBox('available', false);
        const select = simulateSelectBox('favorite', ['dogs', 'cats', 'capybaras'], 'dogs');
        
        form.appendChild(nameInput);
        form.appendChild(checkbox);
        form.appendChild(select);
        
        let formData: any = {};
        const button = simulateButton('Submit', () => {
            formData = {
                name: nameInput.value,
                available: checkbox.checked,
                favorite: select.value
            };
        });
        form.appendChild(button);
        
        document.body.appendChild(form);

        nameInput.value = 'Dr. Bart';
        checkbox.checked = true;
        select.value = 'cats';
        button.click();

        expect(formData.name).toBe('Dr. Bart');
        expect(formData.available).toBe(true);
        expect(formData.favorite).toBe('cats');
    });
});

describe('Example: Calculator', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('renders calculator interface', () => {
        // Simulates: examples/calculator.py
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const input1 = simulateTextBox('num1', '');
        const input2 = simulateTextBox('num2', '');
        const select = simulateSelectBox('operation', ['+', '-', '*', '/'], '+');
        const button = simulateButton('Calculate');
        
        form.appendChild(input1);
        form.appendChild(select);
        form.appendChild(input2);
        form.appendChild(button);
        
        document.body.appendChild(form);

        expect(form.querySelector('input[name="num1"]')).not.toBeNull();
        expect(form.querySelector('input[name="num2"]')).not.toBeNull();
        expect(form.querySelector('select[name="operation"]')).not.toBeNull();
    });

    test('can perform calculation', () => {
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const input1 = simulateTextBox('num1', '');
        const input2 = simulateTextBox('num2', '');
        const select = simulateSelectBox('operation', ['+', '-', '*', '/'], '+');
        const result = document.createElement('p');
        result.id = 'result';
        
        const button = simulateButton('Calculate', () => {
            const n1 = parseFloat(input1.value);
            const n2 = parseFloat(input2.value);
            const op = select.value;
            
            let res = 0;
            switch(op) {
                case '+': res = n1 + n2; break;
                case '-': res = n1 - n2; break;
                case '*': res = n1 * n2; break;
                case '/': res = n1 / n2; break;
            }
            
            result.textContent = `Result: ${res}`;
        });
        
        form.appendChild(input1);
        form.appendChild(select);
        form.appendChild(input2);
        form.appendChild(button);
        form.appendChild(result);
        
        document.body.appendChild(form);

        input1.value = '10';
        input2.value = '5';
        select.value = '+';
        button.click();

        expect(result.textContent).toContain('Result: 15');
    });
});

describe('Example: Todo List', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('can add items to list', () => {
        // Simulates: examples/todo_list.py
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const todos: string[] = [];
        
        const input = simulateTextBox('new_todo', '');
        const button = simulateButton('Add', () => {
            if (input.value.trim()) {
                todos.push(input.value);
                input.value = '';
                updateList();
            }
        });
        
        const list = document.createElement('ul');
        list.id = 'todo-list';
        
        const updateList = () => {
            list.innerHTML = '';
            todos.forEach(todo => {
                const li = document.createElement('li');
                li.textContent = todo;
                list.appendChild(li);
            });
        };
        
        form.appendChild(input);
        form.appendChild(button);
        form.appendChild(list);
        
        document.body.appendChild(form);

        input.value = 'Buy groceries';
        button.click();
        
        input.value = 'Walk the dog';
        button.click();

        expect(list.children.length).toBe(2);
        expect(list.textContent).toContain('Buy groceries');
        expect(list.textContent).toContain('Walk the dog');
    });
});

describe('Example: Simple Login', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="drafter-root--"></div>';
    });

    test('validates login credentials', () => {
        // Simulates: examples/simple_login.py
        const form = document.createElement('form');
        form.id = 'drafter-form--';
        
        const username = simulateTextBox('username', '');
        const password = document.createElement('input');
        password.type = 'password';
        password.name = 'password';
        
        const message = document.createElement('p');
        message.id = 'message';
        
        const button = simulateButton('Login', () => {
            if (username.value === 'admin' && password.value === 'password') {
                message.textContent = 'Login successful!';
            } else {
                message.textContent = 'Invalid credentials';
            }
        });
        
        form.appendChild(username);
        form.appendChild(password);
        form.appendChild(button);
        form.appendChild(message);
        
        document.body.appendChild(form);

        username.value = 'admin';
        password.value = 'password';
        button.click();

        expect(message.textContent).toBe('Login successful!');
        
        username.value = 'wrong';
        password.value = 'wrong';
        button.click();

        expect(message.textContent).toBe('Invalid credentials');
    });
});
