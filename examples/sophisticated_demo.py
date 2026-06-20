from drafter import *


@dataclass
class State:
    pass


add_website_css("""
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #222;
      background: #f5f7fb;
    }

    .header {
      background: white;
      border-bottom: 1px solid #ddd;
      position: sticky;
      top: 0;
    }

    .navbar {
      max-width: 1100px;
      margin: auto;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .logo {
      font-size: 24px;
      font-weight: bold;
      color: #3b5bdb;
    }

    .nav a {
      color: #333;
      text-decoration: none;
      margin-left: 24px;
      font-weight: bold;
    }

    .nav a:hover {
      color: #3b5bdb;
    }

    .hero {
      max-width: 1100px;
      margin: auto;
      padding: 90px 24px;
      display: flex;
      align-items: center;
      gap: 50px;
    }

    .hero-text {
      flex: 1;
    }

    .hero-text h1 {
      font-size: 48px;
      margin-bottom: 20px;
      line-height: 1.1;
    }

    .hero-text p {
      font-size: 18px;
      margin-bottom: 30px;
      color: #555;
    }

    .button {
      display: inline-block;
      background: #3b5bdb;
      color: white;
      padding: 14px 24px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: bold;
    }

    .button:hover {
      background: #2746b8;
    }

    .hero-card {
      flex: 1;
      background: linear-gradient(135deg, #3b5bdb, #15aabf);
      color: white;
      padding: 40px;
      border-radius: 20px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }

    .hero-card h2 {
      margin-bottom: 15px;
      font-size: 30px;
    }

    .section {
      max-width: 1100px;
      margin: auto;
      padding: 60px 24px;
    }

    .section h2 {
      text-align: center;
      font-size: 34px;
      margin-bottom: 35px;
    }

    .cards {
      display: flex;
      gap: 24px;
    }

    .card {
      background: white;
      padding: 28px;
      border-radius: 14px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
      flex: 1;
    }

    .card h3 {
      margin-bottom: 12px;
      color: #3b5bdb;
    }

    .banner {
      background: #222;
      color: white;
      text-align: center;
      padding: 60px 24px;
    }

    .banner h2 {
      margin-bottom: 15px;
      font-size: 32px;
    }

    .footer {
      text-align: center;
      padding: 25px;
      background: white;
      color: #666;
      border-top: 1px solid #ddd;
    }

    @media (max-width: 750px) {
      .navbar,
      .hero,
      .cards {
        flex-direction: column;
        text-align: center;
      }

      .nav a {
        display: inline-block;
        margin: 10px;
      }

      .hero-text h1 {
        font-size: 36px;
      }
    }
    """)

# TODO: Do we need `Header` and `Footer` block components?
# TODO: What about `Nav`, `Section`, `Main`?
# TODO: Perhaps a generic `Block` element that can be used for all of them?


@route
def index(state: State):
    return Page(
        state,
        [
            Div(
                Div(
                    Div("Nova Studio", classes="logo"),
                    Row(
                        Link("Home", index),
                        Link("Features", "/features"),
                        Link("Work", "/work"),
                        Link("Contact", "/contact"),
                        classes="nav",
                    ),
                    classes="navbar",
                ),
                classes="header",
            ),
            Div(
                Div(
                    Div(
                        Header("Build clean, modern websites."),
                        "Nova Studio creates simple, polished web experiences using clear"
                        " design, strong layout, and beginner-friendly code.",
                        Link("Explore Features", "/features"),
                        classes="hero-text",
                    ),
                    Div(
                        Header("Front Page Demo", level=2),
                        "This page includes a navigation bar, hero section, call-to-action,"
                        " feature cards, content banner, footer, and responsive layout.",
                        classes="hero-card",
                    ),
                    classes="section hero",
                ),
                Div(
                    Header("Common Website Elements", level=2),
                    Div(
                        Div(
                            Header("Navigation Bar", level=3),
                            "A simple top menu helps visitors move around the website quickly.",
                            classes="card",
                        ),
                        Div(
                            Header("Hero Section", level=3),
                            "A large opening area introduces the website and highlights its main message.",
                            classes="card",
                        ),
                        Div(
                            Header("Feature Cards", level=3),
                            "Cards organize information into clean, readable sections.",
                            classes="card",
                        ),
                        classes="cards",
                    ),
                    id="features",
                    classes="section",
                ),
                Div(
                    Header("Simple HTML. Basic CSS. Strong Layout.", level=2),
                    "No JavaScript, no frameworks, no complex tools — just core web design.",
                    id="work",
                    classes="section banner",
                ),
                Div(
                    Header("Contact Us", level=2),
                    Div(
                        Div(
                            Header("Email", level=3),
                            "hello@novastudio.example",
                            classes="card",
                        ),
                        Div(
                            Header("Location", level=3),
                            "Design District, Web City",
                            classes="card",
                        ),
                        Div(
                            Header("Hours", level=3),
                            "Monday-Friday, 9AM - 5PM",
                            classes="card",
                        ),
                        classes="cards",
                    ),
                    classes="section",
                    id="contact",
                ),
                classes="main",
            ),
            Div(
                "© 2026 Nova Studio. All rights reserved.",
                classes="footer",
            ),
        ],
    )


start_server(State())
