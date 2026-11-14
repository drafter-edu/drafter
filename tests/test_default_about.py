"""Tests for the default About page (router/defaults/about.py).

The About page renders the student's SiteInformation (author, description,
sources, planning, links), converting URLs into links and lists into
bulleted lists, plus any configured external pages.
"""

from types import SimpleNamespace

import pytest

from drafter.components import BulletedList, Header, Link, RawHTML
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.site_information import SiteInformation
from drafter.payloads.kinds.page import Page
from drafter.router.defaults.about import (
    default_about,
    parse_external_page,
    render_information_value,
)


def make_server(information=None, external_pages=None, site_title="My Site"):
    configuration = ClientServerConfiguration(
        information=information,
        external_pages=external_pages,
        site_title=site_title,
    )
    return SimpleNamespace(get_current_configuration=lambda: configuration)


def headers_of(page):
    return [item.body for item in page.content if isinstance(item, Header)]


class TestDefaultAbout:
    def test_without_information_shows_setup_hint(self):
        page = default_about("state", make_server())

        assert isinstance(page, Page)
        text = " ".join(str(item) for item in page.content)
        assert "set_site_information" in text

    def test_renders_the_users_information_sections(self):
        information = SiteInformation(
            author="Ada Lovelace",
            description="A site about analytical engines.",
            sources=["https://example.com/refs", "Course notes"],
            planning=[],
            links=[],
        )
        page = default_about("state", make_server(information=information))

        titles = headers_of(page)
        assert "Author" in titles
        assert "Description" in titles
        assert "Sources" in titles
        # Empty sections are omitted entirely.
        assert "Planning" not in titles
        assert "Links" not in titles
        assert "Ada Lovelace" in page.content
        assert "A site about analytical engines." in page.content

    def test_site_title_appears_in_heading(self):
        page = default_about("state", make_server(site_title="Engine Sim"))
        assert headers_of(page)[0] == "About Engine Sim"

    def test_url_strings_become_links(self):
        rendered = render_information_value("https://example.com/me")
        assert len(rendered) == 1
        assert isinstance(rendered[0], Link)
        assert rendered[0].url == "https://example.com/me"

    def test_lists_become_bulleted_lists_with_links(self):
        rendered = render_information_value(["https://example.com", "plain text"])
        assert len(rendered) == 1
        bulleted = rendered[0]
        assert isinstance(bulleted, BulletedList)

    def test_external_pages_have_label_and_url_in_right_order(self):
        information = SiteInformation(author="Ada")
        page = default_about(
            "state",
            make_server(
                information=information,
                external_pages=[("https://example.com/docs", "The Docs")],
            ),
        )

        links = []

        def find_links(items):
            for item in items:
                if isinstance(item, Link):
                    links.append(item)
                elif isinstance(item, BulletedList):
                    find_links(item.items)

        find_links(page.content)
        external = [link for link in links if link.url == "https://example.com/docs"]
        assert external, "expected a link to the external page URL"
        assert external[0].text == "The Docs"


def external_page_items(external_pages):
    """The bulleted items under the About page's External Pages heading."""
    page = default_about(
        "state",
        make_server(
            information=SiteInformation(author="Ada"), external_pages=external_pages
        ),
    )
    if "External Pages" not in headers_of(page):
        return []
    bulleted = [item for item in page.content if isinstance(item, BulletedList)][-1]
    return bulleted.items


class TestExternalPages:
    """`--external-pages "URL Text"` entries arrive as single strings: the
    address, a space, then the link's text. The deployment workflow passes
    `"dashboard/ Dashboard"` and `"https://github.com/user/repo Repository"`.
    """

    def test_url_and_text_string_is_split(self):
        [link] = external_page_items(["https://github.com/ada/snacks Repository"])

        assert isinstance(link, Link)
        assert link.url == "https://github.com/ada/snacks"
        assert link.text == "Repository"

    def test_text_may_contain_spaces(self):
        [link] = external_page_items(["https://example.com/docs  The Course Docs "])

        assert link.url == "https://example.com/docs"
        assert link.text == "The Course Docs"

    def test_bare_url_is_its_own_text(self):
        [link] = external_page_items(["https://example.org"])

        assert isinstance(link, Link)
        assert link.url == "https://example.org"
        assert link.text == "https://example.org"

    def test_page_next_to_the_site_is_a_plain_anchor(self):
        # "dashboard/" is a folder published beside the site, not a route:
        # a Link would send the click to the router and show "page not
        # found". A plain anchor lets the browser open it.
        [anchor] = external_page_items(["dashboard/ Dashboard"])

        assert not isinstance(anchor, Link)
        assert anchor == RawHTML('<a href="dashboard/">Dashboard</a>')

    def test_pair_survives_as_tuple_or_list(self):
        # A (URL, Text) tuple becomes a list when configuration passes
        # through JSON on its way to the browser.
        for pair in (("https://a.example", "A"), ["https://a.example", "A"]):
            [link] = external_page_items([pair])
            assert (link.url, link.text) == ("https://a.example", "A")

    def test_blank_entries_are_skipped(self):
        assert external_page_items(["", "   "]) == []

    def test_address_and_text_are_escaped(self):
        [anchor] = external_page_items(['notes/a"b.html <Notes & More>'])

        assert anchor == RawHTML(
            '<a href="notes/a&quot;b.html">&lt;Notes &amp; More&gt;</a>'
        )

    def test_invalid_entry_raises(self):
        with pytest.raises(ValueError, match="Invalid external page format"):
            external_page_items([("only-one-part",)])

    def test_parse_external_page(self):
        assert parse_external_page("dashboard/ Dashboard") == (
            "dashboard/",
            "Dashboard",
        )
        assert parse_external_page("dashboard/") == ("dashboard/", "dashboard/")
        assert parse_external_page("  ") is None


class TestPlanningFileLinks:
    """Every string in the planning field links to the file of that name, as
    in Drafter 1: `planning=["plan.pdf", "design.pdf"]` names documents
    published with the site."""

    def test_file_name_string_becomes_a_link_to_the_file(self):
        rendered = render_information_value("planning.pdf", link_files=True)

        assert rendered == [RawHTML('<a href="planning.pdf">planning.pdf</a>')]

    def test_file_names_in_a_list_become_links(self):
        [bulleted] = render_information_value(
            ["plan.pdf", "images/sketch.png"], link_files=True
        )

        assert bulleted.items == [
            RawHTML('<a href="plan.pdf">plan.pdf</a>'),
            RawHTML('<a href="images/sketch.png">images/sketch.png</a>'),
        ]

    def test_file_names_may_contain_spaces(self):
        rendered = render_information_value("My Final Plan.pdf", link_files=True)

        assert rendered == [
            RawHTML('<a href="My Final Plan.pdf">My Final Plan.pdf</a>')
        ]

    def test_every_string_is_linked_even_without_an_extension(self):
        # Drafter 1 behavior: the planning field holds file names, so no
        # guessing about which strings "look like" files.
        [bulleted] = render_information_value(["notes", "N/A"], link_files=True)

        assert bulleted.items == [
            RawHTML('<a href="notes">notes</a>'),
            RawHTML('<a href="N/A">N/A</a>'),
        ]

    def test_blank_strings_are_not_linked(self):
        assert render_information_value("", link_files=True) == []
        [bulleted] = render_information_value(["plan.pdf", " "], link_files=True)
        assert bulleted.items == [RawHTML('<a href="plan.pdf">plan.pdf</a>'), " "]

    def test_file_name_is_escaped(self):
        rendered = render_information_value('a&b "draft".pdf', link_files=True)

        assert rendered == [
            RawHTML(
                '<a href="a&amp;b &quot;draft&quot;.pdf">'
                "a&amp;b &quot;draft&quot;.pdf</a>"
            )
        ]

    def test_web_addresses_are_still_route_aware_links(self):
        [link] = render_information_value(
            "https://example.com/plan.pdf", link_files=True
        )
        assert isinstance(link, Link)

    def test_file_names_are_not_linked_by_default(self):
        assert render_information_value("plan.pdf") == ["plan.pdf"]

    def test_only_the_planning_section_links_files(self):
        information = SiteInformation(
            author="Ada",
            description="notes.txt",
            sources=["icons.zip"],
            planning=["plan.pdf"],
            links=[],
        )
        page = default_about("state", make_server(information=information))

        assert "notes.txt" in page.content
        bulleted = [item for item in page.content if isinstance(item, BulletedList)]
        assert [item.items for item in bulleted] == [
            ["icons.zip"],
            [RawHTML('<a href="plan.pdf">plan.pdf</a>')],
        ]
