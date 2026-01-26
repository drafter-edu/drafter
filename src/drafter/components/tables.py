from dataclasses import dataclass, fields, is_dataclass
import html
from typing import Optional
from drafter.components.page_content import (
    Component,
    ComponentArgument,
    Content,
    PageContent,
)
from drafter.components.planning.render_plan import RenderPlan
from drafter.history.utils import safe_repr
from copy import deepcopy


@dataclass(repr=False)
class Table(Component):
    """Renders an HTML table from row data and optional header.

    Supports various data formats including lists of lists, dataclasses,
    and mixed content types. Automatically generates header from dataclass
    fields if not explicitly provided.

    Attributes:
        rows: List of table rows (each row is a list of cell content).
        header: Optional list of header cell content.
        tag: The HTML tag name, always 'table'.

    TODO:
        Handle 2d list, 1d list of dataclasses, 1d list of primitives.
        Handle single dataclass instance, dictionaries.
    """

    rows: list[list[Content]]
    header: Optional[list[Content]] = None

    tag = "table"

    ARGUMENTS = [
        ComponentArgument("rows", is_content=True),
        ComponentArgument("header", kind="keyword", default_value=None),
    ]
    RENAME_ATTRS = {"header": ""}

    def __init__(self, rows: list[list[Content]], header=None, **kwargs):
        """Initialize table component.

        Args:
            rows: List of table rows (each row is a list of cell content).
            header: Optional list of header cell content.
            **kwargs: Additional HTML attributes and styles.
        """
        self.rows = rows
        self.header = header
        self.extra_settings = kwargs
        # self.reformat_as_tabular()

    def render_tr(self, row_content, context):
        """Render a table row (tr) element.

        Args:
            row_content: Content for the row cells.
            context: Rendering context.

        Returns:
            RenderPlan for the tr element.
        """
        return RenderPlan(kind="tag", tag_name="tr", children=row_content)

    def render_td(self, cell_content, context):
        """Render a table cell (td) element.

        Args:
            cell_content: Content for the cell.
            context: Rendering context.

        Returns:
            RenderPlan for the td element.
        """
        return RenderPlan(kind="tag", tag_name="td", children=[cell_content])

    def render_td_code(self, cell_content, context):
        """Render a table cell with code formatting.

        Args:
            cell_content: Content for the cell.
            context: Rendering context.

        Returns:
            RenderPlan for td element with code child.
        """
        return self.render_td(
            RenderPlan(
                kind="tag",
                tag_name="code",
                children=[cell_content],
            ),
            context,
        )

    def get_tbody_from_dataclass(
        self, context
    ) -> tuple[RenderPlan, Optional[RenderPlan]]:
        """Generate table body from a dataclass instance.

        Args:
            context: Rendering context.

        Returns:
            Tuple of (tbody_plan, thead_plan) showing dataclass fields.
        """
        tbody_rows = []
        for field in fields(self.rows):  # type: ignore
            value = getattr(self.rows, field.name)
            tbody_rows.append(
                self.render_tr(
                    [
                        self.render_td_code(field.name, context),
                        self.render_td_code(field.type.__name__, context),  # type: ignore
                        self.render_td_code(safe_repr(value), context),
                    ]
                )
            )
        tbody = RenderPlan(kind="tag", tag_name="tbody", children=tbody_rows)
        thead = self.make_head(["Field", "Type", "Current Value"])
        return tbody, thead

    def get_tbody(self, context) -> tuple[RenderPlan, Optional[RenderPlan]]:
        """Generate table body from row data.

        Args:
            context: Rendering context.

        Returns:
            Tuple of (tbody_plan, thead_plan).
        """
        if is_dataclass(self.rows):
            return self.get_tbody_from_dataclass(context)
        # Add rows
        tbody_rows = []
        had_dataclasses = False
        for row in self.rows:
            if is_dataclass(row):
                had_dataclasses = True
                tbody_rows.append(
                    self.render_tr(
                        [
                            self.render_td(str(getattr(row, attr)), context)
                            for attr in row.__dataclass_fields__
                        ],
                        context,
                    )
                )
            elif isinstance(row, list):
                tbody_rows.append(
                    self.render_tr(
                        [self.render_td(str(cell), context) for cell in row], context
                    )
                )

        tbody = RenderPlan(kind="tag", tag_name="tbody", children=tbody_rows)
        if had_dataclasses and self.header is None:
            thead = self.make_head(list(row.__dataclass_fields__.keys()))  # type: ignore
        else:
            thead = None
        return tbody, thead

    def make_head(self, header) -> RenderPlan:
        """Create a table header (thead) element.

        Args:
            header: List of header cell content.

        Returns:
            RenderPlan for the thead element.
        """
        return RenderPlan(
            kind="tag",
            tag_name="thead",
            children=[
                RenderPlan(
                    kind="tag",
                    tag_name="tr",
                    children=[
                        RenderPlan(
                            kind="tag",
                            tag_name="th",
                            children=[cell],
                        )
                        for cell in header
                    ],
                )
            ],
        )

    def get_children(self, context) -> list[PageContent | RenderPlan]:
        """Get child elements (thead and tbody) for the table.

        Args:
            context: Rendering context.

        Returns:
            List of RenderPlan objects for table structure.
        """
        children = []

        tbody, thead = self.get_tbody(context)

        # Add header if present
        if self.header:
            children.append(self.make_head(self.header))
        elif thead:
            children.append(thead)
        children.append(tbody)

        return children
