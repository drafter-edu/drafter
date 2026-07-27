add_website_css("""
.panel {
    border: 1px solid #ccc;
}
""")


def index(state: State) -> Page:
    return Page(
        state,
        [
            HeaderContent("Top"),
            Nav(Link("Home", "/home")),
            Main(
                Section(
                    Article(
                        Header("Title", level=1),
                        Header("Subtitle", level=2),
                        Paragraph(
                            "Paragraph", Span("text"), "and", InlineCode("x = 1"), "."
                        ),
                        Pre("""line 1
line 2"""),
                        BlockQuote("https://example.com", "Quoted"),
                        BulletedList(["First", "Second"]),
                        NumberedList(["One", "Two"]),
                        Div(
                            Image("logo.png", width=320, height=200, alt="logo"),
                            Audio("sound.mp3", autoplay=True, muted=True),
                            Video("video.mp4", width=640, height=360, loop=True),
                            Canvas("draw", width=400, height=200),
                            SVG(
                                '<rect width="100" height="50"></rect>',
                                width=100,
                                height=50,
                                viewBox="0 0 100 50",
                            ),
                        ),
                        Label("Username", for_id="username"),
                        TextBox("username", default_value="alice"),
                        TextBox("password", default_value="hunter2", kind="password"),
                        CheckBox("agree", default_value=True),
                        DateInput("birthday", default_value="2024-01-15"),
                        TimeInput("alarm", default_value="08:30:00"),
                        DateTimeInput("meeting", default_value="2024-01-15T14:30"),
                        FileUpload(
                            "documents", accept=[".pdf", ".docx"], multiple=True
                        ),
                        Argument("token", "abc123"),
                        TextArea("bio", default_value="Hello there", rows=3, cols=20),
                        SelectBox("color", ["red", "blue"], default_value="blue"),
                        Output("result", "Ready", for_id="username"),
                        ProgressBar(0.75, max=1),
                        Table([["Ada", "36"], ["Bob", "28"]], header=["Name", "Age"]),
                        HorizontalRule(),
                        LineBreak(),
                        Button("Continue", "next_page"),
                        classes="panel",
                    )
                ),
                Aside("Side notes"),
            ),
            FooterContent("Bottom"),
        ],
    )
