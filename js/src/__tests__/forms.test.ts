/**
 * Comprehensive tests for Drafter form components functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { runStudentCode, clearDrafterSiteRoot } from "../skulpt.index";

const TEXTBOX_CODE = `
from drafter import *

@dataclass
class State:
    name: str
    email: str

@route
def index(state: State):
    return Page(state, [
        "Enter your information:",
        Label("Name:", for_id="name_field"),
        TextBox("name_field", state.name),
        Label("Email:", for_id="email_field"),
        TextBox("email_field", state.email, kind="email"),
        f"Name: {state.name}:)",
        f"Email: {state.email}:)",
        Button("Update", update)
    ])

@route
def update(state: State, name_field: str, email_field: str):
    state.name = name_field
    state.email = email_field
    return index(state)

start_server(State("John Doe", "john@example.com"))
`;

const CHECKBOX_CODE = `
from drafter import *

@dataclass
class State:
    subscribed: bool
    terms_accepted: bool

@route
def index(state: State):
    return Page(state, [
        "Preferences:",
        Label("Subscribe to newsletter:", for_id="subscribe"),
        CheckBox("subscribe", state.subscribed),
        Label("Accept terms:", for_id="terms"),
        CheckBox("terms", state.terms_accepted),
        f"Subscribed: {state.subscribed}",
        f"Terms: {state.terms_accepted}",
        Button("Save", save)
    ])

@route
def save(state: State, subscribe: bool, terms: bool):
    state.subscribed = subscribe
    state.terms_accepted = terms
    return index(state)

start_server(State(False, False))
`;

const TEXTAREA_CODE = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        "Enter a message:",
        Label("Message:", for_id="msg"),
        TextArea("msg", state.message),
        f"Current message: {state.message}",
        Button("Submit", submit)
    ])

@route
def submit(state: State, msg: str):
    state.message = msg
    return index(state)

start_server(State("Hello World"))
`;

const SELECTBOX_CODE = `
from drafter import *

@dataclass
class State:
    color: str
    size: str

@route
def index(state: State):
    return Page(state, [
        "Choose options:",
        Label("Color:", for_id="color_choice"),
        SelectBox("color_choice", ["red", "blue", "green"], state.color),
        Label("Size:", for_id="size_choice"),
        SelectBox("size_choice", ["small", "medium", "large"], state.size),
        f"Color: {state.color}",
        f"Size: {state.size}",
        Button("Apply", apply)
    ])

@route
def apply(state: State, color_choice: str, size_choice: str):
    state.color = color_choice
    state.size = size_choice
    return index(state)

start_server(State("red", "medium"))
`;

const DATE_TIME_CODE = `
from drafter import *
from datetime import datetime, date, time

@dataclass
class State:
    appointment: datetime
    birthday: date
    meeting_time: time

@route
def index(state: State):
    return Page(state, [
        "Schedule information:",
        Label("Appointment:", for_id="appt"),
        DateTimeInput("appt", state.appointment),
        Label("Birthday:", for_id="bday"),
        DateInput("bday", state.birthday),
        Label("Meeting time:", for_id="meeting"),
        TimeInput("meeting", state.meeting_time),
        f"Appointment Chosen: {state.appointment}",
        f"Birthday Chosen: {state.birthday}",
        f"Meeting Chosen: {state.meeting_time}",
        Button("Save", save)
    ])

@route
def save(state: State, appt: datetime, bday: date, meeting: time):
    state.appointment = appt
    state.birthday = bday
    state.meeting_time = meeting
    return index(state)

start_server(State(datetime(2025, 6, 15, 14, 30), date(1990, 5, 20), time(10, 0)))
`;

const ALL_FORMS_CODE = `
from drafter import *
from datetime import datetime, date, time

@dataclass
class State:
    name: str
    bio: str
    is_student: bool
    grade: str
    appointment: datetime
    birthday: date
    wake_time: time

@route
def index(state: State):
    return Page(state, [
        "Complete Form:",
        Label("Name:", for_id="name"),
        TextBox("name", state.name),
        Label("Bio:", for_id="bio"),
        TextArea("bio", state.bio),
        Label("Student status:", for_id="student"),
        CheckBox("student", state.is_student),
        Label("Grade:", for_id="grade"),
        SelectBox("grade", ["A", "B", "C", "D", "F"], state.grade),
        Label("Appointment:", for_id="appt"),
        DateTimeInput("appt", state.appointment),
        Label("Birthday:", for_id="bday"),
        DateInput("bday", state.birthday),
        Label("Wake time:", for_id="wake"),
        TimeInput("wake", state.wake_time),
        Button("Submit All", submit_all)
    ])

@route
def submit_all(state: State, name: str, bio: str, student: bool, grade: str, 
               appt: datetime, bday: date, wake: time):
    state.name = name
    state.bio = bio
    state.is_student = student
    state.grade = grade
    state.appointment = appt
    state.birthday = bday
    state.wake_time = wake
    return Page(state, [
        "Submission complete!",
        f"Name: {name}",
        f"Bio: {bio}",
        f"Student: {student}",
        f"Grade: {grade}",
        f"Appointment: {appt}",
        f"Birthday: {bday}",
        f"Wake time: {wake}",
        Button("Back", index)
    ])

start_server(State("Alice", "A student", True, "A", 
                   datetime(2025, 12, 1, 9, 0), date(2000, 1, 1), time(7, 0)))
`;

const EMPTY_DEFAULTS_CODE = `
from drafter import *

@dataclass
class State:
    name: str
    accepted: bool
    notes: str

@route
def index(state: State):
    return Page(state, [
        "Form with empty defaults:",
        TextBox("name_input", state.name),
        CheckBox("accept_input", state.accepted),
        TextArea("notes_input", state.notes),
        f"Name: '{state.name}'",
        f"Accepted: {state.accepted}",
        f"Notes: '{state.notes}'",
        Button("Submit", submit)
    ])

@route
def submit(state: State, name_input: str, accept_input: bool, notes_input: str):
    state.name = name_input
    state.accepted = accept_input
    state.notes = notes_input
    return index(state)

start_server(State("", False, ""))
`;

const LABEL_ASSOCIATION_CODE = `
from drafter import *

@dataclass
class State:
    value: str

@route
def index(state: State):
    label_text = TextBox("text_field", state.value)
    return Page(state, [
        "Label association test:",
        Label("Using string ID:", for_id="text_field"),
        label_text,
        Label("Using component:", for_id=label_text),
        TextBox("another_field", "test"),
        f"Value: {state.value}",
        Button("Update", update)
    ])

@route
def update(state: State, text_field: str, another_field: str):
    state.value = text_field
    return index(state)

start_server(State("initial"))
`;

const MULTIPLE_SAME_TYPE_CODE = `
from drafter import *

@dataclass
class State:
    first: str
    second: str
    third: str

@route
def index(state: State):
    return Page(state, [
        "Multiple text boxes:",
        TextBox("first_box", state.first),
        TextBox("second_box", state.second),
        TextBox("third_box", state.third),
        f"First: {state.first}",
        f"Second: {state.second}",
        f"Third: {state.third}",
        Button("Update All", update_all)
    ])

@route
def update_all(state: State, first_box: str, second_box: str, third_box: str):
    state.first = first_box
    state.second = second_box
    state.third = third_box
    return index(state)

start_server(State("A", "B", "C"))
`;

const SPECIAL_CHARACTERS_CODE = `
from drafter import *

@dataclass
class State:
    text: str

@route
def index(state: State):
    return Page(state, [
        "Special characters test:",
        TextBox("input", state.text),
        TextArea("textarea", state.text),
        f"Text: {state.text}",
        Button("Update", update)
    ])

@route
def update(state: State, input: str, textarea: str):
    state.text = input
    return index(state)

start_server(State("Test <>&\\"'"))
`;

describe("Drafter Form Components Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    describe("TextBox Component", () => {
        test("can load and display TextBox with default values", async () => {
            await runStudentCode({
                code: TEXTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            expect(drafterBody).not.toBeNull();
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Name: John Doe:\)/);
            await app.findByText(/Email: john@example.com:\)/);
        });

        test("can update TextBox values", async () => {
            await runStudentCode({
                code: TEXTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const nameInput = app.getByRole("textbox", { name: /name_field/i });
            await userEvent.clear(nameInput);
            await userEvent.type(nameInput, "Jane Smith:)");

            const emailInput = app.getByRole("textbox", {
                name: /email_field/i,
            });
            await userEvent.clear(emailInput);
            await userEvent.type(emailInput, "jane@test.com");

            const button = await app.findByRole("button", { name: /update/i });
            await userEvent.click(button);

            await app.findByText(/Name: Jane Smith:\)/);
            await app.findByText(/Email: jane@test.com:\)/);
        });

        test("TextBox preserves empty strings", async () => {
            await runStudentCode({
                code: EMPTY_DEFAULTS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Name: ''/);

            const nameInput = app.getByRole("textbox", { name: /name_input/i });
            await userEvent.type(nameInput, "New Name");

            const button = await app.findByRole("button", { name: /submit/i });
            await userEvent.click(button);

            await app.findByText(/Name: 'New Name'/);
        });
    });

    describe("CheckBox Component", () => {
        test("can load and display CheckBox with default values", async () => {
            await runStudentCode({
                code: CHECKBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Subscribed: False/);
            await app.findByText(/Terms: False/);
        });

        test("can toggle CheckBox values", async () => {
            await runStudentCode({
                code: CHECKBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const subscribeCheckbox = app.getByRole("checkbox", {
                name: /subscribe/i,
            });
            await userEvent.click(subscribeCheckbox);

            const termsCheckbox = app.getByRole("checkbox", { name: /terms/i });
            await userEvent.click(termsCheckbox);

            const button = await app.findByRole("button", { name: /save/i });
            await userEvent.click(button);

            await app.findByText(/Subscribed: True/);
            await app.findByText(/Terms: True/);
        });

        test("can toggle CheckBox from true to false", async () => {
            await runStudentCode({
                code: CHECKBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            // First set to true
            const subscribeCheckbox = app.getByRole("checkbox", {
                name: /subscribe/i,
            });
            await userEvent.click(subscribeCheckbox);
            await userEvent.click(
                await app.findByRole("button", { name: /save/i })
            );
            await app.findByText(/Subscribed: True/);

            // Then toggle back to false
            const subscribeCheckbox2 = app.getByRole("checkbox", {
                name: /subscribe/i,
            });
            await userEvent.click(subscribeCheckbox2);
            await userEvent.click(
                await app.findByRole("button", { name: /save/i })
            );
            await app.findByText(/Subscribed: False/);
        });
    });

    describe("TextArea Component", () => {
        test("can load and display TextArea with default value", async () => {
            await runStudentCode({
                code: TEXTAREA_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Current message: Hello World/);
        });

        test("can update TextArea with multiline text", async () => {
            await runStudentCode({
                code: TEXTAREA_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const textarea = app.getByRole("textbox", { name: /msg/i });
            await userEvent.clear(textarea);
            await userEvent.type(textarea, "Line 1{Enter}Line 2{Enter}Line 3");

            const button = await app.findByRole("button", { name: /submit/i });
            await userEvent.click(button);

            await app.findByText(/Current message: Line 1/);
        });

        test("TextArea handles empty values", async () => {
            await runStudentCode({
                code: EMPTY_DEFAULTS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Notes: ''/);

            const textarea = app.getByRole("textbox", { name: /notes_input/i });
            await userEvent.type(textarea, "Some notes");

            const button = await app.findByRole("button", { name: /submit/i });
            await userEvent.click(button);

            await app.findByText(/Notes: 'Some notes'/);
        });
    });

    describe("SelectBox Component", () => {
        test("can load and display SelectBox with default value", async () => {
            await runStudentCode({
                code: SELECTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Color: red/);
            await app.findByText(/Size: medium/);
        });

        test("can change SelectBox values", async () => {
            await runStudentCode({
                code: SELECTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const colorSelect = app.getByRole("combobox", {
                name: /color_choice/i,
            });
            await userEvent.selectOptions(colorSelect, "blue");

            const sizeSelect = app.getByRole("combobox", {
                name: /size_choice/i,
            });
            await userEvent.selectOptions(sizeSelect, "large");

            const button = await app.findByRole("button", { name: /apply/i });
            await userEvent.click(button);

            await app.findByText(/Color: blue/);
            await app.findByText(/Size: large/);
        });

        test("SelectBox maintains options list", async () => {
            await runStudentCode({
                code: SELECTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const colorSelect = app.getByRole("combobox", {
                name: /color_choice/i,
            }) as HTMLSelectElement;
            expect(colorSelect.options.length).toBe(3);
            expect(colorSelect.options[0].value).toBe("red");
            expect(colorSelect.options[1].value).toBe("blue");
            expect(colorSelect.options[2].value).toBe("green");
        });
    });

    describe("Date and Time Components", () => {
        test("can load DateTimeInput, DateInput, and TimeInput", async () => {
            await runStudentCode({
                code: DATE_TIME_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Appointment Chosen:/);
            await app.findByText(/Birthday Chosen:/);
            await app.findByText(/Meeting Chosen:/);
        });

        test("date/time inputs are present in the DOM", async () => {
            await runStudentCode({
                code: DATE_TIME_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const apptInput = app.getByLabelText(/appt/i);
            expect(apptInput).not.toBeNull();
            expect(apptInput.getAttribute("type")).toBe("datetime-local");

            const bdayInput = app.getByLabelText(/bday/i);
            expect(bdayInput).not.toBeNull();
            expect(bdayInput.getAttribute("type")).toBe("date");

            const meetingInput = app.getByLabelText(/meeting/i);
            expect(meetingInput).not.toBeNull();
            expect(meetingInput.getAttribute("type")).toBe("time");
        });
    });

    describe("Label Component", () => {
        test("Label associates with form fields using string ID", async () => {
            await runStudentCode({
                code: LABEL_ASSOCIATION_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const labels = drafterBody?.querySelectorAll("label");
            expect(labels).not.toBeNull();
            expect(labels!.length).toBeGreaterThan(0);

            // Check that at least one label has a for attribute
            const hasForAttribute = Array.from(labels!).some(
                (label) => label.getAttribute("for") !== null
            );
            expect(hasForAttribute).toBe(true);
        });
    });

    describe("Complex Form Integration", () => {
        test("can load application with all form types", async () => {
            await runStudentCode({
                code: ALL_FORMS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            expect(drafterBody).not.toBeNull();
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Complete Form:/);
        });

        test("can submit form with all input types", async () => {
            await runStudentCode({
                code: ALL_FORMS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const nameInput = app.getByRole("textbox", { name: /name/i });
            await userEvent.clear(nameInput);
            await userEvent.type(nameInput, "Bob");

            const gradeSelect = app.getByRole("combobox", { name: /grade/i });
            await userEvent.selectOptions(gradeSelect, "B");

            const button = await app.findByRole("button", {
                name: /submit all/i,
            });
            await userEvent.click(button);

            await app.findByText(/Submission complete!/);
            await app.findByText(/Name: Bob/);
            await app.findByText(/Grade: B/);
        });

        test("can navigate back after submission", async () => {
            await runStudentCode({
                code: ALL_FORMS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const submitButton = await app.findByRole("button", {
                name: /submit all/i,
            });
            await userEvent.click(submitButton);

            await app.findByText(/Submission complete!/);

            const backButton = await app.findByRole("button", {
                name: /back/i,
            });
            await userEvent.click(backButton);

            await app.findByText(/Complete Form:/);
        });
    });

    describe("Multiple Fields of Same Type", () => {
        test("can handle multiple TextBox components independently", async () => {
            await runStudentCode({
                code: MULTIPLE_SAME_TYPE_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/First: A/);
            await app.findByText(/Second: B/);
            await app.findByText(/Third: C/);

            const firstBox = app.getByRole("textbox", { name: /first_box/i });
            await userEvent.clear(firstBox);
            await userEvent.type(firstBox, "X");

            const secondBox = app.getByRole("textbox", { name: /second_box/i });
            await userEvent.clear(secondBox);
            await userEvent.type(secondBox, "Y");

            const thirdBox = app.getByRole("textbox", { name: /third_box/i });
            await userEvent.clear(thirdBox);
            await userEvent.type(thirdBox, "Z");

            const button = await app.findByRole("button", {
                name: /update all/i,
            });
            await userEvent.click(button);

            await app.findByText(/First: X/);
            await app.findByText(/Second: Y/);
            await app.findByText(/Third: Z/);
        });
    });

    describe("Special Characters Handling", () => {
        test("handles special HTML characters in form inputs", async () => {
            await runStudentCode({
                code: SPECIAL_CHARACTERS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const input = app.getByRole("textbox", { name: /input/i });
            await userEvent.clear(input);
            await userEvent.type(input, "Test <>&");

            const button = await app.findByRole("button", { name: /update/i });
            await userEvent.click(button);

            // The text should be properly escaped and displayed
            await app.findByText(/Text: Test <>&/);
        });
    });

    describe("Form State Persistence", () => {
        test("form maintains state across multiple interactions", async () => {
            await runStudentCode({
                code: TEXTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            // First update
            const nameInput = app.getByRole("textbox", { name: /name_field/i });
            await userEvent.clear(nameInput);
            await userEvent.type(nameInput, "First Name:)");
            await userEvent.click(
                await app.findByRole("button", { name: /update/i })
            );
            await app.findByText(/Name: First Name:\)/);
            // Second update
            const nameInput2 = app.getByRole("textbox", {
                name: /name_field/i,
            });
            await userEvent.clear(nameInput2);
            await userEvent.type(nameInput2, "Second Name");
            await userEvent.click(
                await app.findByRole("button", { name: /update/i })
            );
            await app.findByText(/Name: Second Name:\)/);

            // Third update
            const nameInput3 = app.getByRole("textbox", {
                name: /name_field/i,
            });
            await userEvent.clear(nameInput3);
            await userEvent.type(nameInput3, "Third Name");
            await userEvent.click(
                await app.findByRole("button", { name: /update/i })
            );
            await app.findByText(/Name: Third Name:\)/);
        });
    });

    describe("Empty and Default Values", () => {
        test("forms handle empty initial values correctly", async () => {
            await runStudentCode({
                code: EMPTY_DEFAULTS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            await app.findByText(/Name: ''/);
            await app.findByText(/Accepted: False/);
            await app.findByText(/Notes: ''/);
        });

        test("can update from empty values to non-empty values", async () => {
            await runStudentCode({
                code: EMPTY_DEFAULTS_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const nameInput = app.getByRole("textbox", { name: /name_input/i });
            await userEvent.type(nameInput, "New User");

            const checkbox = app.getByRole("checkbox", {
                name: /accept_input/i,
            });
            await userEvent.click(checkbox);

            const textarea = app.getByRole("textbox", { name: /notes_input/i });
            await userEvent.type(textarea, "Important notes");

            const button = await app.findByRole("button", { name: /submit/i });
            await userEvent.click(button);

            await app.findByText(/Name: 'New User'/);
            await app.findByText(/Accepted: True/);
            await app.findByText(/Notes: 'Important notes'/);
        });

        test("can clear non-empty values to empty", async () => {
            await runStudentCode({
                code: TEXTBOX_CODE,
                presentErrors: false,
            });
            const drafterBody = document.querySelector("#drafter-body--");
            const app = within(drafterBody as HTMLElement);

            const nameInput = app.getByRole("textbox", { name: /name_field/i });
            await userEvent.clear(nameInput);

            const button = await app.findByRole("button", { name: /update/i });
            await userEvent.click(button);

            await app.findByText(/^Name:\s*:\)/);
        });
    });
});
