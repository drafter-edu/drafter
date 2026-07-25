"""Tests for stylesheet <link> reuse across editor-driven restarts.

Re-running an embedded demo rebuilds the site DOM; recreating the theme
<link> elements forced the browser to refetch every stylesheet on each run.
Under `mkdocs serve` that refetch can stall for up to a minute: the dev
server sends no cache headers, and its livereload long-polls occupy all six
of the browser's connections to the host on pages with several demo
iframes. These tests pin the fix: links whose hrefs still match stay
connected — the same element objects, never detached — while the site
content around them is replaced.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.dom import reuse_theme_link_prefix
from drafter.bridge.site_renderer import SiteRenderer
from drafter.site.headers import CSSLink
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import DRAFTER_TAG_CLASSES, DRAFTER_TAG_IDS

SHADOW_HOST_ID = DRAFTER_TAG_IDS["SHADOW_HOST"]
THEME_CLASS = DRAFTER_TAG_CLASSES["THEME"]
ROOT_ID = "drafter-root-test"


### Minimal fake DOM


class FakeClassList:
    def __init__(self, element):
        self._element = element

    def contains(self, name):
        return name in (self._element.getAttribute("class") or "").split()


def _parse_html(document, html):
    """Stand-in for HTML parsing: the shadow-host template materializes as
    the host div (setup() re-queries it by id); anything else becomes a
    single opaque content div carrying the raw markup."""
    if not html:
        return []
    if f'id="{SHADOW_HOST_ID}"' in html:
        host = FakeElement(document, "div")
        host.setAttribute("id", SHADOW_HOST_ID)
        return [host]
    content = FakeElement(document, "div")
    content.setAttribute("data-fake-html", html)
    return [content]


class FakeNodeContainer:
    """Shared child-list behavior for elements, fragments, and shadow roots."""

    def __init__(self, document):
        self.ownerDocument = document
        self._children = []
        self._inner_html = ""

    @property
    def children(self):
        return list(self._children)

    def appendChild(self, node):
        return self.insertBefore(node, None)

    def insertBefore(self, node, anchor):
        nodes = node._children[:] if isinstance(node, FakeFragment) else [node]
        for child in nodes:
            child._detach()
            child.parentNode = self
        if anchor is None:
            self._children.extend(nodes)
        else:
            index = self._children.index(anchor)
            self._children[index:index] = nodes
        return node

    def _walk(self):
        for child in self._children:
            yield child
            yield from child._walk()

    def querySelector(self, selector):
        matches = self.querySelectorAll(selector)
        return matches[0] if matches else None

    def querySelectorAll(self, selector):
        return [node for node in self._walk() if node._matches(selector)]

    @property
    def innerHTML(self):
        return self._inner_html

    @innerHTML.setter
    def innerHTML(self, html):
        self._inner_html = html
        target = getattr(self, "content", None) or self
        for child in list(target._children):
            child._detach()
        for child in _parse_html(self.ownerDocument, html):
            target.appendChild(child)


class FakeFragment(FakeNodeContainer):
    def _matches(self, selector):
        return False

    def _detach(self):
        pass


class FakeShadowRoot(FakeNodeContainer):
    def _matches(self, selector):
        return False


class FakeElement(FakeNodeContainer):
    def __init__(self, document, tag):
        super().__init__(document)
        self.tagName = tag.upper()
        self.parentNode = None
        self.shadowRoot = None
        self.detach_count = 0
        self.textContent = ""
        self._attributes = {}
        self.classList = FakeClassList(self)
        if self.tagName == "TEMPLATE":
            self.content = FakeFragment(document)

    def getAttribute(self, name):
        return self._attributes.get(name)

    def setAttribute(self, name, value):
        self._attributes[name] = value

    def hasAttribute(self, name):
        return name in self._attributes

    def _matches(self, selector):
        if selector.startswith("#"):
            return self._attributes.get("id") == selector[1:]
        tag, _, class_name = selector.partition(".")
        if tag and self.tagName != tag.upper():
            return False
        return not class_name or self.classList.contains(class_name)

    def _detach(self):
        if self.parentNode is not None:
            self.parentNode._children.remove(self)
            self.parentNode = None
            self.detach_count += 1

    def remove(self):
        self._detach()

    def removeChild(self, child):
        child._detach()
        return child

    def attachShadow(self, options):
        if self.shadowRoot is not None:
            raise RuntimeError("attachShadow called twice on the same host")
        self.shadowRoot = FakeShadowRoot(self.ownerDocument)
        return self.shadowRoot


class FakeDocument:
    def __init__(self):
        self.created_links = []
        self.head = FakeElement(self, "head")
        self.body = FakeElement(self, "body")
        self.documentElement = FakeElement(self, "html")
        self.documentElement.appendChild(self.head)
        self.documentElement.appendChild(self.body)

    def createElement(self, tag):
        element = FakeElement(self, tag)
        if tag.lower() == "link":
            self.created_links.append(element)
        return element

    def getElementById(self, element_id):
        return self.documentElement.querySelector("#" + element_id)

    def getElementsByTagName(self, tag):
        if tag.lower() == "head":
            return [self.head]
        return [
            node
            for node in self.documentElement._walk()
            if getattr(node, "tagName", None) == tag.upper()
        ]

    def querySelector(self, selector):
        return self.documentElement.querySelector(selector)

    def querySelectorAll(self, selector):
        return self.documentElement.querySelectorAll(selector)


### Helpers


def make_document_with_root():
    document = FakeDocument()
    root = FakeElement(document, "div")
    root.setAttribute("id", ROOT_ID)
    document.body.appendChild(root)
    return document


def make_renderer(document):
    runtime = SimpleNamespace(context=SimpleNamespace(document=document))
    return SiteRenderer(runtime, ROOT_ID, ROOT_ID)


def make_site_data(
    css_urls=("../_shared/css/drafter_debug.css", "../_shared/css/diff2html.min.css"),
    use_shadow_dom=True,
    body="<div>site</div>",
):
    return InitialSiteData(
        site_html=body,
        site_title="Demo",
        additional_css=[CSSLink(url=url) for url in css_urls],
        additional_style=["body { color: red; }"],
        use_shadow_dom=use_shadow_dom,
    )


def get_shadow_root(document):
    host = document.getElementById(ROOT_ID).querySelector("#" + SHADOW_HOST_ID)
    return host.shadowRoot if host else None


def theme_links(scope):
    return scope.querySelectorAll(f"link.{THEME_CLASS}")


def hrefs(links):
    return [link.getAttribute("href") for link in links]


### reuse_theme_link_prefix unit tests


def make_link(document, href):
    link = document.createElement("link")
    link.setAttribute("href", href)
    link.setAttribute("class", "old-class")
    document.head.appendChild(link)
    return link


class TestReuseThemeLinkPrefix:
    def test_full_match_reuses_everything_and_refreshes_classes(self):
        document = FakeDocument()
        links = [make_link(document, url) for url in ("a.css", "b.css")]
        wanted = [("a.css", "theme x"), ("b.css", "theme")]

        assert reuse_theme_link_prefix(links, wanted) == 2
        assert all(link.parentNode is document.head for link in links)
        assert all(link.detach_count == 0 for link in links)
        assert links[0].getAttribute("class") == "theme x"
        assert links[1].getAttribute("class") == "theme"

    def test_mismatch_removes_tail_even_if_later_urls_match(self):
        document = FakeDocument()
        links = [make_link(document, url) for url in ("a.css", "b.css", "c.css")]
        wanted = [("a.css", "theme"), ("x.css", "theme"), ("c.css", "theme")]

        assert reuse_theme_link_prefix(links, wanted) == 1
        assert links[0].parentNode is document.head
        assert links[1].parentNode is None
        assert links[2].parentNode is None

    def test_more_wanted_than_existing(self):
        document = FakeDocument()
        links = [make_link(document, "a.css")]
        wanted = [("a.css", "theme"), ("b.css", "theme")]

        assert reuse_theme_link_prefix(links, wanted) == 1

    def test_no_existing_links(self):
        assert reuse_theme_link_prefix([], [("a.css", "theme")]) == 0


### SiteRenderer.setup() shadow-DOM branch


class TestShadowLinkReuse:
    def test_first_setup_creates_links_after_content(self):
        document = make_document_with_root()
        renderer = make_renderer(document)
        renderer.setup(make_site_data())

        shadow = get_shadow_root(document)
        assert renderer.scope is shadow
        assert hrefs(theme_links(shadow)) == [
            "../_shared/css/drafter_debug.css",
            "../_shared/css/diff2html.min.css",
        ]
        assert [child.tagName for child in shadow.children] == [
            "DIV",
            "LINK",
            "LINK",
            "STYLE",
        ]

    def test_restart_reuses_the_same_link_elements(self):
        document = make_document_with_root()
        make_renderer(document).setup(make_site_data())
        shadow = get_shadow_root(document)
        first_links = theme_links(shadow)
        first_content = shadow.querySelector("div")

        # Each run builds a fresh SiteRenderer over the same DOM.
        second = make_renderer(document)
        second.setup(make_site_data())

        assert get_shadow_root(document) is shadow
        assert second.scope is shadow
        second_links = theme_links(shadow)
        assert [id(link) for link in second_links] == [id(link) for link in first_links]
        # Never detached = the browser never refetches their stylesheets.
        assert all(link.detach_count == 0 for link in second_links)
        assert len(document.created_links) == 2

        # The site content itself was replaced, and order is preserved:
        # content first, then the links, then the injected styles.
        new_content = shadow.querySelector("div")
        assert new_content is not first_content
        assert first_content.parentNode is None
        assert [child.tagName for child in shadow.children] == [
            "DIV",
            "LINK",
            "LINK",
            "STYLE",
        ]

    def test_changed_stylesheets_rebuild_only_the_stale_tail(self):
        document = make_document_with_root()
        make_renderer(document).setup(
            make_site_data(css_urls=("a.css", "b.css", "c.css"))
        )
        shadow = get_shadow_root(document)
        first_links = theme_links(shadow)

        make_renderer(document).setup(
            make_site_data(css_urls=("a.css", "x.css", "c.css"))
        )

        second_links = theme_links(shadow)
        assert hrefs(second_links) == ["a.css", "x.css", "c.css"]
        # The unchanged prefix is the same connected element...
        assert second_links[0] is first_links[0]
        assert first_links[0].detach_count == 0
        # ...while the stale tail was removed and recreated.
        assert first_links[1].parentNode is None
        assert first_links[2].parentNode is None

    def test_error_site_then_normal_setup_rebuilds_from_scratch(self):
        document = make_document_with_root()
        make_renderer(document).setup(
            InitialSiteData(site_html="broken", site_title="err", error=True)
        )

        make_renderer(document).setup(make_site_data())

        shadow = get_shadow_root(document)
        assert shadow is not None
        assert len(theme_links(shadow)) == 2


### SiteRenderer.setup() non-shadow branch


class TestHeadLinkReuse:
    def test_restart_reuses_head_links(self):
        document = make_document_with_root()
        make_renderer(document).setup(make_site_data(use_shadow_dom=False))
        first_links = theme_links(document.head)
        assert len(first_links) == 2

        make_renderer(document).setup(make_site_data(use_shadow_dom=False))

        second_links = theme_links(document.head)
        assert [id(link) for link in second_links] == [id(link) for link in first_links]
        assert all(link.detach_count == 0 for link in second_links)
        assert len(document.created_links) == 2

    def test_switching_to_shadow_dom_clears_head_links(self):
        document = make_document_with_root()
        make_renderer(document).setup(make_site_data(use_shadow_dom=False))
        assert len(theme_links(document.head)) == 2

        make_renderer(document).setup(make_site_data(use_shadow_dom=True))

        assert theme_links(document.head) == []
        assert len(theme_links(get_shadow_root(document))) == 2
