import pytest

from drafter import *
from drafter.components import plotting as _plotting_components
from tests.components.helpers import eval_drafter_with_source

snippets = {
    "button": {
        "regular": "Button('Hello World', 'index')",
        "function_button": "Button('Button with function ref', Button)",
        "external_link": "Button('External Link', 'http://example.com')",
        "with_arguments": """Button('With Args', 'next_page', arguments=[
            Argument('first', 'first_value'),
            Argument('second', 'second_value'),
        ])""",
        "with_style": """Button("Red", "next", style_font_color="red")""",
        "with_attributes": """Button("Attrs", "next", id="mybutton", style_background_color="#00FF00")""",
        "with_mystery_attr": """Button("Mystery Attr", "next", mystery_attr="mystery_value")""",
        "with_classes": """Button("Classy", "next", classes=["class1", "class2"])""",
        "with_class": """Button("Single Class", "next", classes=["single_class"])""",
    },
    "argument": {
        "simple": """Argument('param', 'value')""",
        "with_style": """Argument('styled_param', 'styled_value', style_font_weight="bold")""",
        "with_attributes": """Argument('attr_param', 'attr_value', id="arg1", style_font_style="italic")""",
    },
    "span": {
        "simple": """Span('Hello world!')""",
        "with_style": """Span('Styled text', style_font_size="20px", style_color="#333333")""",
        "with_attributes": """Span('Attributed text', id="myspan", style_text_decoration="underline")""",
    },
    "ol": {
        "simple": """NumberedList(['First item', 'Second item', 'Third item'])""",
        "with_style": """NumberedList(['Styled item'], style_margin_left="20px", style_color="#555555")""",
    },
    "ul": {
        "simple": """BulletedList(['First item', 'Second item', 'Third item'])""",
        "with_style": """BulletedList(['Styled item'], style_margin_left="20px", style_color="#555555")""",
    },
    "header": {
        "h1": """Header('This is a level 1 header', level=1)""",
        "h2": """Header('This is a level 2 header', level=2)""",
        "h3": """Header('This is a level 3 header', level=3)""",
        "with_style": """Header('Styled Header', level=2, style_text_align="center", style_color="#0000FF")""",
    },
    "text": {
        "simple": """Text('This is a simple text component.')""",
        "with_style": """Text('Styled text component.', style_font_family='Arial', style_font_size='16px')""",
    },
    "paragraph": {
        "simple": """Paragraph('This is a paragraph.')""",
        "multiple_items": """Paragraph('First sentence.', 'Second sentence.')""",
        "with_style": """Paragraph('Styled paragraph', style_line_height='1.5', style_margin_bottom='12px')""",
    },
    "section": {
        "simple": """Section('Section body')""",
        "with_style": """Section('Styled section', style_padding='12px', style_border='1px solid #CCC')""",
    },
    "article": {
        "simple": """Article('Article body')""",
        "with_style": """Article('Styled article', style_margin='8px')""",
    },
    "aside": {
        "simple": """Aside('Sidebar note')""",
        "with_style": """Aside('Styled aside', style_background_color='#FAFAFA')""",
    },
    "main": {
        "simple": """Main('Primary content')""",
        "with_style": """Main('Styled main', style_max_width='960px')""",
    },
    "nav": {
        "simple": """Nav('Home', 'Courses')""",
        "with_style": """Nav('Menu', style_display='flex', style_gap='8px')""",
    },
    "headercontent": {
        "simple": """HeaderContent('Page Header')""",
        "with_style": """HeaderContent('Styled Header', style_background_color='#EEE')""",
    },
    "footercontent": {
        "simple": """FooterContent('Page Footer')""",
        "with_style": """FooterContent('Styled Footer', style_padding='10px')""",
    },
    "division": {
        "simple": """Division('Hello from division')""",
        "multiple_items": """Division('One', 'Two', 'Three')""",
        "with_style": """Division('Styled division', style_background_color='#EFEFEF', style_padding='8px')""",
    },
    "row": {
        "simple": """Row(['Hello world!', 'This is a row.'])""",
        "with_style": """Row(['Styled row'], style_background_color="#DDDDDD", style_padding="10px")""",
        "with_id": """Row(['Row with ID'], id="row1", style_border="1px solid #000000")""",
    },
    "TextArea": {
        "simple": """TextArea('comments')""",
        "default_value": """TextArea('comments', 'Enter your comments here...')""",
        "boolean_flag": """TextArea('comments', 'Enter your comments here...', required=True)""",
        "with_style": """TextArea('feedback', style_width='300px', style_height='150px')""",
        "with_attributes": """TextArea('bio', 'Tell us about yourself', rows=5, cols=40, placeholder='Your bio...')""",
    },
    "textbox": {
        "simple": """TextBox('username')""",
        "with_default": """TextBox('email', 'user@example.com')""",
        "with_kind": """TextBox('password', 'password')""",
        "all_args": """TextBox('phone', '555-1234', 'tel')""",
        "with_style": """TextBox('search', style_width='300px', placeholder='Search...')""",
        "with_attributes": """TextBox('age', 'number', min=0, max=120, required=True)""",
        "with_event_handler": """TextBox('input1', on_input='handle_input')""",
        "with_event_handler_function": """TextBox('input1', on_input=Button)""",
    },
    "selectbox": {
        "simple": """SelectBox('color', ['red', 'green', 'blue'])""",
        "with_default": """SelectBox('size', ['small', 'medium', 'large'], 'medium')""",
        "missing_default_allowed": """SelectBox('size', ['small', 'medium', 'large'], 'x-large', allow_missing=True)""",
        "with_style": """SelectBox('country', ['USA', 'Canada', 'Mexico'], style_width='200px')""",
        "with_attributes": """SelectBox('category', ['A', 'B', 'C'], id='cat-select', required=True)""",
    },
    "checkbox": {
        "simple": """CheckBox('agree')""",
        "checked": """CheckBox('subscribe', True)""",
        "with_style": """CheckBox('remember_me', style_margin='10px')""",
        "with_attributes": """CheckBox('terms', required=True, id='terms-checkbox')""",
    },
    "label": {
        "simple": """Label('Username:')""",
        "with_for": """Label('Email Address:', for_id='email')""",
        "with_style": """Label('Password:', style_font_weight='bold', style_color='#333')""",
        "with_component": """Label('Name:', for_id=TextBox('name'))""",
    },
    "dateinput": {
        "simple": """DateInput('birthday')""",
        "with_default": """DateInput('appointment', '2024-12-25')""",
        "from_date": """DateInput('start_date', date1)""",
        "with_style": """DateInput('start_date', style_width='200px')""",
        "with_attributes": """DateInput('event_date', required=True, min='2024-01-01')""",
    },
    "timeinput": {
        "simple": """TimeInput('alarm')""",
        "with_default": """TimeInput('meeting_time', '14:30')""",
        "from_time": """TimeInput('lunch_time', time1)""",
        "with_style": """TimeInput('reminder', style_width='150px')""",
        "with_attributes": """TimeInput('appointment_time', required=True, step=900)""",
    },
    "datetimeinput": {
        "simple": """DateTimeInput('event')""",
        "with_default": """DateTimeInput('deadline', '2024-12-31T23:59')""",
        "from_datetime": """DateTimeInput('meeting', datetime1)""",
        "with_style": """DateTimeInput('scheduled', style_width='250px')""",
        "with_attributes": """DateTimeInput('launch_time', required=True, id='launch')""",
    },
    "link": {
        "simple": """Link('Click here', 'next_page')""",
        "external": """Link('Google', 'https://www.google.com')""",
        "with_arguments": """Link('Details', 'show_details', arguments=Argument('id', 123))""",
        "with_style": """Link('Styled Link', 'index', style_color='blue', style_text_decoration='none')""",
        "with_list_args": """Link('Multiple Args', 'process', arguments=[Argument('x', 1), Argument('y', 2)])""",
    },
    "div": {
        "simple": """Div('Hello world!')""",
        "multiple_items": """Div('First', 'Second', 'Third')""",
        "with_style": """Div('Styled div', style_background_color='#f0f0f0', style_padding='20px')""",
        "with_id": """Div('Content', id='main-content', style_border='1px solid black')""",
    },
    "box": {
        "simple": """Box('Boxed content')""",
        "with_style": """Box('Nice box', style_border='2px solid blue', style_padding='10px')""",
    },
    "linebreak": {
        "simple": """LineBreak()""",
        "with_data": """LineBreak(data_custom='value')""",
        "with_style": """LineBreak(style_margin='5px')""",
    },
    "horizontalrule": {
        "simple": """HorizontalRule()""",
        "with_style": """HorizontalRule(style_border='2px solid red', style_margin='20px')""",
    },
    "pre": {
        "simple": """Pre('code block')""",
        "multiple_lines": """Pre('line 1', 'line 2', 'line 3')""",
        "with_style": """Pre('formatted text', style_background_color='#f5f5f5', style_padding='10px')""",
    },
    "preformattedtext": {
        "simple": """PreformattedText('alias text block')""",
        "multiple_lines": """PreformattedText('line a', 'line b')""",
        "with_style": """PreformattedText('styled alias block', style_font_family='monospace')""",
    },
    "blockquote": {
        "simple": """BlockQuote(None, 'Quoted text')""",
        "with_cite": """BlockQuote('https://example.com/source', 'Cited quote')""",
        "with_style": """BlockQuote(None, 'Styled quote', style_border_left='4px solid #999')""",
    },
    "inlinecode": {
        "simple": """InlineCode('x = 42')""",
        "with_style": """InlineCode('print(value)', style_background_color='#F4F4F4')""",
    },
    "htmltag": {
        "simple": """HtmlTag('mark', 'Highlighted')""",
        "with_style": """HtmlTag('section', 'Custom body', style_padding='4px')""",
    },
    "rawhtml": {
        "simple": """RawHTML('<strong>Bold</strong>')""",
        "complex": """RawHTML('<div class="custom"><p>Paragraph</p></div>')""",
    },
    "geolocation": {
        "current_location_simple": """CurrentLocation('student_location')""",
        "current_location_hidden": """CurrentLocation('hidden_location', show=False)""",
        "current_location_with_options": """CurrentLocation('home_location', show_coordinates=True, id='geo-1')""",
        "current_location_with_handler": """CurrentLocation('spot', on_locate='record_location')""",
        "current_location_with_events_and_geo_options": """CurrentLocation('spot', enable_high_accuracy=False, timeout=2500, maximum_age=120000, on_error='handle_geo_error', on_denied='handle_geo_denied', on_timeout='handle_geo_timeout')""",
        "location_data": """Location('granted', message='OK', latitude=37.5, longitude=-77.4, accuracy=10.0)""",
    },
    "image": {
        "simple": """Image('cat.jpg')""",
        "with_dimensions": """Image('photo.png', width=400, height=300)""",
        "with_style": """Image('logo.svg', style_border='1px solid gray')""",
        "with_width_only": """Image('banner.jpg', width=800)""",
        "with_handler": """Image("clickme.png", on_click="handleImageClick")""",
    },
    "table": {
        "simple": """Table([['A', 'B'], ['C', 'D']])""",
        "with_header": """Table([['1', '2'], ['3', '4']], header=['Col1', 'Col2'])""",
        "with_style": """Table([['X', 'Y']], style_border='1px solid black', style_width='100%')""",
    },
    "output": {
        "simple": """Output('test', 'Result: 42')""",
        "with_for": """Output('named', '100%', for_id='progress1')""",
        "with_style": """Output('another', 'Success!', style_color='green', style_font_weight='bold')""",
    },
    "progress": {
        "simple": """Progress(0.5)""",
        "with_max": """Progress(75, max=100)""",
        "with_style": """Progress(0.8, max=1.0, style_width='300px', style_height='30px')""",
    },
    "download": {
        "simple": """Download('Download File', 'file.txt', 'Hello World')""",
        "with_content_type": """Download('Get CSV', 'data.csv', 'a,b,c', 'text/csv')""",
        "with_style": """Download('PDF', 'document.pdf', 'content', 'application/pdf', style_color='red')""",
    },
    "fileupload": {
        "simple": """FileUpload('document')""",
        "with_accept_string": """FileUpload('photo', accept='image/*')""",
        "with_accept_list": """FileUpload('files', accept=['image/png', 'image/jpeg'])""",
        "with_multiple": """FileUpload('attachments', accept=['.pdf', '.docx'], multiple=True)""",
        "with_attributes": """FileUpload('avatar', accept='image/*', required=True, id='avatar-upload')""",
    },
    "audio": {
        "simple": """Audio('song.mp3')""",
        "no_controls": """Audio('background.ogg', controls=False)""",
        "autoplay_loop": """Audio('theme.wav', autoplay=True, loop=True)""",
        "all_options": """Audio('sound.mp3', controls=True, autoplay=False, loop=True, muted=True)""",
        "with_style": """Audio('music.mp3', style_width='400px')""",
    },
    "video": {
        "simple": """Video('movie.mp4')""",
        "with_dimensions": """Video('tutorial.mp4', width=640, height=480)""",
        "autoplay_muted": """Video('ad.mp4', autoplay=True, muted=True)""",
        "all_options": """Video('demo.mp4', width=800, height=600, controls=True, autoplay=False, loop=True, muted=False)""",
        "with_style": """Video('clip.mp4', style_border='2px solid black')""",
    },
    "canvas": {
        "simple": """Canvas('myCanvas')""",
        "with_dimensions": """Canvas('drawArea', width=800, height=600)""",
        "with_style": """Canvas('game', width=640, height=480, style_border='1px solid black')""",
    },
    "tone": {
        "simple": """Tone('C4')""",
        "frequency": """Tone(440, duration=250)""",
        "waveform_volume": """Tone('F#3', waveform='square', volume=0.5)""",
        "auto_play_hidden": """Tone('G5', auto_play=True, show=False)""",
        "with_effects": """Tone('C4', effects=[Echo(), Reverb(amount=0.8)])""",
        "with_handlers": """Tone('C4', on_start='tone_started', on_finish='tone_done', on_error='tone_failed')""",
    },
    "melody": {
        "simple": """Melody(['C4', 'E4', 'G4'])""",
        "with_beats": """Melody([('C4', 2), ('E4', 1), ('rest', 1), ('G4', 0.5)], tempo=90)""",
        "with_controls": """Melody(['C4', 'D4'], controls=True, waveform='triangle')""",
        "auto_play": """Melody(['C4'], auto_play=True, volume=0.6)""",
        "with_handlers": """Melody(['C4', 'E4'], on_note='heard_note', on_finish='melody_done')""",
    },
    "sound": {
        "simple": """Sound('song.mp3')""",
        "with_settings": """Sound('song.mp3', volume=0.5, pan=-0.5, speed=1.5, loop=True)""",
        "with_effects": """Sound('voice.wav', effects=[Muffle(amount=0.7), Distortion()])""",
        "no_controls_autoplay": """Sound('alert.mp3', auto_play=True, controls=False)""",
        "with_visualize": """Sound('song.mp3', visualize='bars', on_play='started', on_finish='finished', on_error='failed')""",
    },
    "microphone": {
        "simple": """Microphone('mic')""",
        "with_threshold": """Microphone('mic', threshold=0.7, cooldown=2000)""",
        "with_levels": """Microphone('mic', rate=500, visualize='waveform', on_level='heard_level')""",
        "with_handlers": """Microphone('mic', on_loud='heard_loud', on_quiet='heard_quiet', on_denied='mic_denied', on_error='mic_failed')""",
        "audio_level_data": """AudioLevel('granted', message='OK', volume=0.25, peak_volume=0.9, pitch=440.0)""",
    },
    "audiorecorder": {
        "simple": """AudioRecorder('voice')""",
        "with_duration": """AudioRecorder('voice', max_duration=10000, show=False)""",
        "with_handlers": """AudioRecorder('voice', on_record='got_recording', on_denied='rec_denied', on_error='rec_failed')""",
        "recording_data": """Recording('granted', message='OK', data_url='data:audio/webm;base64,AAAA', duration=2.5, size=1024)""",
    },
    "camera": {
        "simple": """Camera('photo')""",
        "with_settings": """Camera('photo', width=1280, height=720, facing='environment', mirror=False, show=False)""",
        "with_handlers": """Camera('photo', on_capture='got_photo', on_denied='cam_denied', on_error='cam_failed')""",
        "photo_data": """Photo('granted', message='OK', data_url='data:image/png;base64,AAAA', width=640, height=480)""",
    },
    "svg": {
        "simple": """SVG('<circle cx="50" cy="50" r="40"/>')""",
        "with_dimensions": """SVG('<rect width="100" height="100"/>', width=100, height=100)""",
        "with_viewbox": """SVG('<path d="M10 10"/>', viewBox='0 0 100 100')""",
        "all_options": """SVG('<circle cx="50" cy="50" r="40"/>', width=200, height=200, viewBox='0 0 100 100', style_border='1px solid blue')""",
    },
}

if _plotting_components.has_matplotlib():
    # TODO: AI-generated, investigate later
    snippets["matplotlibplot"] = {
        "simple": """MatPlotLibPlot()""",
        "with_settings": """MatPlotLibPlot(extra_matplotlib_settings={'format': 'svg'}, close_automatically=False)""",
        "with_style": """MatPlotLibPlot(style_border='1px solid #444')""",
    }


@pytest.mark.parametrize(
    "category,name,snippet",
    [
        pytest.param(category, name, snippet, id=f"{category} :: {name}")
        for category, group in snippets.items()
        for name, snippet in group.items()
    ],
)
def test_snippet_consistent(category, name, snippet):
    obj1 = eval_drafter_with_source(snippet, "consistent", category, name)
    obj2 = eval_drafter_with_source(snippet, "consistent", category, name)

    assert obj1 == obj2, (
        f"{category} / {name}: evaluating the snippet twice "
        f"should produce equal objects.\nSnippet:\n{snippet}"
    )


@pytest.mark.parametrize(
    "category,name,snippet",
    [
        pytest.param(category, name, snippet, id=f"{category} :: {name}")
        for category, group in snippets.items()
        for name, snippet in group.items()
    ],
)
def test_snippet_repr(category, name, snippet):
    obj1 = eval_drafter_with_source(snippet, "repr", category, name)
    obj2 = eval_drafter_with_source(repr(obj1), "repr", category, name)

    assert obj1 == obj2, (
        f"{category} / {name}: repr(obj) did not match the snippet.\n\n"
        f"Snippet:\n{snippet}\n\nrepr(obj):\n{repr(obj1)}"
    )
