"""Targets describing where and how payload content is applied in the DOM.

Defines the `Target` dataclass, which fragments use to identify the
element(s) to update on the client, and the `DEFAULT_BODY_TARGET` used by
full `Page` responses.
"""

from dataclasses import dataclass

from drafter.site.site import DRAFTER_TAG_IDS


@dataclass
class Target:
    """Describes which DOM element(s) a payload's content applies to, and how.

    The selector fields (`id`, `tag`, `class_name`, `selector`,
    `data_attribute`, `attribute`, and `nth_child`) are combined by
    `to_selector` into a single CSS selector identifying the element(s) to
    act on, with the search optionally modified by `closest`, `within`,
    and `all`. The action flags (`is_page_load`, `replace`, `remove`,
    `html`, `append`, `prepend`, `before`, and `after`) then choose how
    the rendered content is applied to the matched element(s), while
    `attributes_to_set`, `styles_to_set`, and `class_toggles` describe
    additional mutations to perform. If no elements match, the `fallback`
    target (when set) is used instead.

    Attributes:
        id: HTML id of the element to match (rendered as `#id`).
        tag: Tag name of the element to match (e.g., `div`).
        class_name: Class name(s) to match; multiple classes may be
            separated by whitespace.
        selector: Explicit CSS selector. If it contains combinators or
            commas it is used verbatim as the whole selector; otherwise it
            serves as a base that the other selector fields are appended to.
        data_attribute: Data attribute to match, given as `data-x` or
            `data-x='value'`.
        attribute: Mapping of attribute names to required values, each
            rendered as an `[name='value']` selector part.
        nth_child: Appends an `:nth-child(n)` clause to the selector.
    """

    # Selectors
    id: str | None = None
    tag: str | None = None
    class_name: str | None = None
    selector: str | None = None
    data_attribute: str | None = None
    attribute: dict[str, str] | None = None
    nth_child: int | None = None
    closest: bool = False
    """Find the nearest ancestor matching the selector."""
    within: "Target | None" = None
    """Constrain the search to elements within the target element."""

    all: bool = False
    """Whether to modify all matching elements or just the first."""

    # Actions
    is_page_load: bool = False
    """Indicates that this is a full page load, resetting most content."""
    replace: bool = False
    """Replace the entire node, not just its children."""
    remove: bool = False
    """Only remove the matching element."""
    html: bool = False
    """Set the innerHTML."""
    append: bool = False
    """Add content to the end of the element (inside)."""
    prepend: bool = False
    """Add content to the beginning of the element (inside)."""
    before: bool = False
    """Insert content before the element (as a sibling)."""
    after: bool = False
    """Insert content after the element (as a sibling)."""

    attributes_to_set: dict[str, str] | None = None
    """Additional HTML attributes to update (must be strings)."""
    styles_to_set: dict[str, str] | None = None
    """Additional CSS styles to update (must be strings)."""
    class_toggles: dict[str, bool] | None = None
    """Class toggles to apply (class name -> whether to add/remove)."""

    fallback: "Target | None" = None
    """If this target fails to find any elements, use the fallback instead."""

    def __repr__(self) -> str:
        """Represent the target by only the fields that were explicitly set."""
        pieces = []
        if self.id:
            pieces.append(f"id='{self.id}'")
        if self.tag:
            pieces.append(f"tag='{self.tag}'")
        if self.class_name:
            pieces.append(f"class_name='{self.class_name}'")
        if self.selector:
            pieces.append(f"selector='{self.selector}'")
        if self.data_attribute:
            pieces.append(f"data_attribute='{self.data_attribute}'")
        if self.attribute:
            pieces.append(f"attribute={self.attribute}")
        if self.nth_child is not None:
            pieces.append(f"nth_child={self.nth_child}")
        if self.closest:
            pieces.append("closest=True")
        if self.within:
            pieces.append(f"within={self.within}")
        if self.all:
            pieces.append("all=True")
        if self.replace:
            pieces.append("replace=True")
        if self.remove:
            pieces.append("remove=True")
        if self.html:
            pieces.append("html=True")
        if self.append:
            pieces.append("append=True")
        if self.prepend:
            pieces.append("prepend=True")
        if self.before:
            pieces.append("before=True")
        if self.after:
            pieces.append("after=True")
        if self.attributes_to_set:
            pieces.append(f"attributes_to_set={self.attributes_to_set}")
        if self.styles_to_set:
            pieces.append(f"styles_to_set={self.styles_to_set}")
        if self.class_toggles:
            pieces.append(f"class_toggles={self.class_toggles}")
        if self.fallback:
            pieces.append(f"fallback={self.fallback}")

        return f"Target({', '.join(pieces)})"

    def to_selector(self) -> str:
        """Convert this Target to a CSS selector string.

        The selector is built up from the available fields and will combine
        tag, id, class(es), attributes, and data attributes where possible.
        If `selector` is provided and contains combinators, it will be used
        as the base verbatim; otherwise it's combined with the other parts.

        Returns:
            CSS selector string that can be used with querySelectorAll.
        """
        # If the user supplied an explicit selector string, treat it as a base.
        base = self.selector.strip() if self.selector else ""

        # Build components from explicit fields
        tag = self.tag or ""
        id_part = f"#{self.id}" if self.id else ""
        class_part = ""
        if self.class_name:
            # support multiple classes separated by whitespace
            classes = [c for c in self.class_name.split() if c]
            class_part = "".join(f".{c}" for c in classes)

        attr_parts = []
        if self.attribute:
            for k, v in self.attribute.items():
                attr_parts.append(f"[{k}='{v}']")
        if self.data_attribute:
            # data_attribute may be provided as "data-x" or "data-x='val'"
            da = self.data_attribute.strip()
            if "=" in da:
                key, val = da.split("=", 1)
                attr_parts.append(f"[{key.strip()}={val.strip()}]")
            else:
                attr_parts.append(f"[{da}]")

        # Decide how to combine with selector
        if base:
            # If selector contains combinators or commas, treat as complex and use as-is
            import re

            if re.search(r"[\s>+~,]", base):
                selector = base
            else:
                # Simple base (like "div" or ".class") — append other parts
                selector = base
                if tag and not base.startswith(tag):
                    selector = tag + selector
                if id_part and id_part not in selector:
                    selector += id_part
                if class_part:
                    selector += class_part
                for ap in attr_parts:
                    selector += ap
        else:
            # No explicit selector — compose from tag/id/classes/attributes
            selector = ""
            if tag:
                selector += tag
            if id_part:
                selector += id_part
            if class_part:
                selector += class_part
            for ap in attr_parts:
                selector += ap

        # Fallback to body if nothing specified
        if not selector:
            selector = f"#{DRAFTER_TAG_IDS['BODY']}"

        # Handle nth_child appended at the end
        if self.nth_child is not None:
            selector += f":nth-child({self.nth_child})"

        return selector


DEFAULT_BODY_TARGET = Target(
    id=DRAFTER_TAG_IDS["BODY"], replace=False, is_page_load=True
)
"""The Target used by full `Page` responses.

Matches Drafter's body element by its id, marks the response as a full
page load, and replaces the body's contents rather than the element
itself.
"""
