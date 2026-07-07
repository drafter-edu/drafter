from drafter import *


@dataclass
class State:
    pass


"""
So for the `Ad`, the simplest option is to just define a function that does the same thing.
You can put whatever arbitrary code you want in there. I don't know if we're planning to
support just rendering nested lists in a particular way, so wrapping it in a `Div` is
probably a good move.
"""


def Ad(product_or_service: str, text: str) -> PageContent:
    return Div(
        HorizontalRule(), Section(Header(product_or_service, 3), Paragraph(text))
    )


"""
There's also the more aggressive escape hatch of `RawHTML`, which just allows you to insert
raw HTML directly into the page.
"""


def AdRaw(
    product_or_service: str,
    text: str,
) -> PageContent:
    return RawHTML(f"""
                   <hr/>
                   <section>
                    <h3>{product_or_service}</h3>
                    <p>{text}</p>
                   </section>
                   """)


"""
If you did want to make a custom component, since it's returning more than just a single
HTML element, you'll need to use the `RenderPlan` API. It's a little more complicated
and requires diving into some of Drafter's internals.

The SelectBox, CheckBox, _HtmlList, and Table classes are examples of this in action.

Usually, it would be expected that if you're making a component, there would only
be one outermost component (rather than a list). But if you want, you can use the
`RenderPlan(kind="fragment", items=[...])` to achieve this (which is what CheckBox does).
"""
from drafter.components import PageContent, Component
from drafter.components.page_content import ComponentArgument, RenderPlan


@dataclass(repr=False)
class AdComponent(Component):
    tag = "div"
    product_or_service: str
    text: str

    ARGUMENTS = [
        ComponentArgument("product_or_service", is_content=True),
        ComponentArgument(
            "text", is_content=True
        ),  # if it's able to be rendered as nested content, then add `is_content=True`
    ]

    def __init__(self, product_or_service: str, text: str, **kwargs):
        self.product_or_service = product_or_service
        self.text = text
        self.extra_settings = kwargs

    def get_children(self, context) -> list[PageContent | RenderPlan]:
        return [
            RenderPlan(kind="tag", tag_name="hr"),
            RenderPlan(
                kind="tag",
                tag_name="section",
                children=[
                    RenderPlan(
                        kind="tag",
                        tag_name="h3",
                        children=[self.product_or_service],
                    ),
                    RenderPlan(
                        kind="tag",
                        tag_name="p",
                        children=[self.text],
                    ),
                ],
            ),
        ]


# ----------------------------------------------------------------


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Ad(
                "First Version (Simple)",
                "This is the first version of the ad, rendered as the simplest form.",
            ),
            AdRaw(
                "Second Version (Raw)",
                "This is the second version of the ad, rendered as raw HTML.",
            ),
            AdComponent(
                "Third Version (Component)",
                "This is the third version of the ad, rendered as a custom component.",
            ),
        ],
    )


start_server(State())
