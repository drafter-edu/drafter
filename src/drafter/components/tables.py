from dataclasses import dataclass, fields, is_dataclass
import html
from typing import List, Union, Any
from drafter.components.page_content import PageContent
from drafter.old_history import safe_repr


@dataclass
class Table(PageContent):
    rows: Union[List[List[str]], List[Any]]

    def __init__(self, rows: List[List[str]], header=None, **kwargs):
        self.rows = rows
        self.header = header
        self.extra_settings = kwargs
        self.reformat_as_tabular()

    def reformat_as_single(self):
        result = []
        for field in fields(self.rows):  # type: ignore
            value = getattr(self.rows, field.name)
            result.append(
                [
                    f"<code>{html.escape(field.name)}</code>",
                    f"<code>{html.escape(field.type.__name__)}</code>",  # type: ignore
                    f"<code>{safe_repr(value)}</code>",
                ]
            )
        self.rows = result
        if not self.header:
            self.header = ["Field", "Type", "Current Value"]

    def reformat_as_tabular(self):
        # print(self.rows, is_dataclass(self.rows))
        if is_dataclass(self.rows):
            self.reformat_as_single()
            return
        result = []
        had_dataclasses = False
        for row in self.rows:
            if is_dataclass(row):
                had_dataclasses = True
                result.append(
                    [str(getattr(row, attr)) for attr in row.__dataclass_fields__]
                )
            if isinstance(row, str):
                result.append(row)
            elif isinstance(row, list):
                result.append([str(cell) for cell in row])

        if had_dataclasses and self.header is None:
            self.header = list(row.__dataclass_fields__.keys())  # type: ignore
        self.rows = result

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        rows = "\n".join(
            f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>"
            for row in self.rows
        )
        header = (
            ""
            if not self.header
            else f"<thead><tr>{''.join(f'<th>{cell}</th>' for cell in self.header)}</tr></thead>"
        )
        return f"<table {parsed_settings}>{header}{rows}</table>"
