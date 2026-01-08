from tests.components.snippets._base import TestableComponentSet
from drafter import *
from datetime import datetime, date, time


tests = TestableComponentSet("forms")

# Label tests
tests.label_simple = Label("Username", id="abc")
tests.label_simple = """
<label id="abc">
  Username
</label>
"""

tests.label_with_for = Label("Email", for_id="email_input", id="1")
tests.label_with_for = """
<label for="email_input" id="1">
  Email
</label>
"""

# TextBox tests
tests.textbox_simple = TextBox("username")
tests.textbox_simple = """
<input aria-label="username" id="username" name="username" type="text">
"""

tests.textbox_with_default = TextBox("email", default_value="user@example.com")
tests.textbox_with_default = """
<input aria-label="email" id="email" name="email" type="text" value="user@example.com">
"""

tests.textbox_password = TextBox("password", kind="password")
tests.textbox_password = """
<input aria-label="password" id="password" name="password" type="password">
"""

tests.textbox_email = TextBox("email_field", kind="email")
tests.textbox_email = """
<input aria-label="email_field" id="email_field" name="email_field" type="email">
"""

# TextArea tests
tests.textarea_simple = TextArea("comments")
tests.textarea_simple = """
<textarea aria-label="comments" id="comments" name="comments">
  
</textarea>
"""

tests.textarea_with_default = TextArea("bio", default_value="Tell us about yourself")
tests.textarea_with_default = """
<textarea aria-label="bio" id="bio" name="bio">
  Tell us about yourself
</textarea>
"""

tests.textarea_with_rows_cols = TextArea("feedback", rows=5, cols=40)
tests.textarea_with_rows_cols = """
<textarea aria-label="feedback" cols="40" id="feedback" name="feedback" rows="5">
  
</textarea>
"""

# SelectBox tests
tests.selectbox_simple = SelectBox("color", ["Red", "Green", "Blue"])
tests.selectbox_simple = """
<select aria-label="color" id="color" name="color">
  <option value="Red">
    Red
  </option>
  <option value="Green">
    Green
  </option>
  <option value="Blue">
    Blue
  </option>
</select>
"""

tests.selectbox_with_default = SelectBox(
    "fruit", ["Apple", "Banana", "Cherry"], "Banana"
)
tests.selectbox_with_default = """
<select aria-label="fruit" id="fruit" name="fruit">
  <option value="Apple">
    Apple
  </option>
  <option selected value="Banana">
    Banana
  </option>
  <option value="Cherry">
    Cherry
  </option>
</select>
"""

# CheckBox tests
tests.checkbox_simple = CheckBox("agree")
tests.checkbox_simple = """
<span><input id="--drafter-hidden-agree" name="agree" type="hidden" value="">
<input aria-label="agree" id="agree" name="agree" type="checkbox">
</span>
"""

tests.checkbox_checked = CheckBox("subscribe", default_value=True)
tests.checkbox_checked = """
<span><input id="--drafter-hidden-subscribe" name="subscribe" type="hidden" value="">
<input aria-label="subscribe" checked id="subscribe" name="subscribe" type="checkbox">
</span>
"""

# DateInput tests
tests.dateinput_simple = DateInput("birthdate")
tests.dateinput_simple = """
<input aria-label="birthdate" id="birthdate" name="birthdate" type="date">
"""

tests.dateinput_with_default = DateInput("start_date", default_value=date(2024, 1, 15))
tests.dateinput_with_default = """
<input aria-label="start_date" id="start_date" name="start_date" type="date" value="2024-01-15">
"""

# TimeInput tests
tests.timeinput_simple = TimeInput("meeting_time")
tests.timeinput_simple = """
<input aria-label="meeting_time" id="meeting_time" name="meeting_time" type="time">
"""

tests.timeinput_with_default = TimeInput("alarm", default_value=time(9, 30))
tests.timeinput_with_default = """
<input aria-label="alarm" id="alarm" name="alarm" type="time" value="09:30:00">
"""

# DateTimeInput tests
tests.datetimeinput_simple = DateTimeInput("appointment")
tests.datetimeinput_simple = """
<input aria-label="appointment" id="appointment" name="appointment" type="datetime-local">
"""

tests.datetimeinput_with_default = DateTimeInput(
    "event", default_value=datetime(2024, 1, 15, 14, 30)
)
tests.datetimeinput_with_default = """
<input aria-label="event" id="event" name="event" type="datetime-local" value="2024-01-15T14:30">
"""


tests.arguments_outside = Argument("secret_message", "It's a secret to everybody!")
tests.arguments_outside = """
<input id="secret_message" name="$@JSON~@$secret_message" type="hidden" value="&amp;quot;It&amp;#x27;s a secret to everybody!&amp;quot;">
"""
