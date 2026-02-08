from drafter.site.site import DRAFTER_TAG_IDS
from dataclasses import dataclass
from typing import Optional


@dataclass
class Target:
    # Selectors
    id: Optional[str] = None
    tag: Optional[str] = None
    class_name: Optional[str] = None
    selector: Optional[str] = None
    data_attribute: Optional[str] = None
    attribute: Optional[dict[str, str]] = None
    nth_child: Optional[int] = None
    #: Find the nearest ancestor matching the selector
    closest: bool = False
    #: Constrain the search to elements within the target element
    within: "Optional[Target]" = None

    #: Whether to modify all matching elements or just the first
    all: bool = False

    # Actions
    #: Replace the entire node, not just its children
    replace: bool = False
    #: Only remove the matching element
    remove: bool = False
    #: Set the innerHTML
    html: bool = False
    #: Add content to the end of the element (inside)
    append: bool = False
    #: Add content to the beginning of the element (inside)
    prepend: bool = False
    #: Insert content before the element (as a sibling)
    before: bool = False
    #: Insert content after the element (as a sibling)
    after: bool = False

    #: Additional HTML attributes to update (must be strings)
    attributes_to_set: Optional[dict[str, str]] = None
    #: Additional CSS styles to update (must be strings)
    styles_to_set: Optional[dict[str, str]] = None
    #: Class toggles to apply (class name -> whether to add/remove)
    class_toggles: Optional[dict[str, bool]] = None

    #: If this target fails to find any elements, use the fallback instead
    fallback: "Optional[Target]" = None
    
    def __repr__(self) -> str:
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
        parts = []

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


DEFAULT_BODY_TARGET = Target(id=DRAFTER_TAG_IDS["BODY"], replace=False)
