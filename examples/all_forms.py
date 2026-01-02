from drafter import start_server, route, Label, TextBox, CheckBox, DateTimeInput, DateInput, TimeInput, Button, Page
from dataclasses import dataclass
from datetime import date, time, datetime


@dataclass
class State:
    name: str
    is_cool: bool
    when: datetime
    at_time: time
    birthday: date
    
@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            "Please fill out the form below:",
            Label("Name:", for_id="name_input"),
            TextBox("name_input", state.name),
            Label("Are you cool?", for_id="cool_checkbox"),
            CheckBox("cool_checkbox", state.is_cool),
            Label("When?", for_id="when_input"),
            DateTimeInput("when_input", state.when),
            Label("At Time:", for_id="at_time_input"),
            TimeInput("at_time_input", state.at_time),
            Label("Birthday:", for_id="birthday_input"),
            DateInput("birthday_input", state.birthday),
            Button("Submit", "process_form"),
        ],
    )
    
@route
def process_form(
    state: State,
    name_input: str,
    cool_checkbox: bool,
    birthday_input: date,
    when_input: datetime,
    at_time_input: time,
) -> Page:
    state.name = name_input
    state.is_cool = cool_checkbox
    state.birthday = birthday_input
    state.when = when_input
    state.at_time = at_time_input
    return index(state)


start_server(State("Bart", True, datetime.now(),
                   time(13, 30), date(2010, 4, 1)))