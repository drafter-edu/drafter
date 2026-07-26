"""Tests for the default About page (router/defaults/about.py).

The About page renders the student's SiteInformation (author, description,
sources, planning, links), converting URLs into links and lists into
bulleted lists, plus any configured external pages.
"""

from types import SimpleNamespace

from drafter.components import BulletedList, Header, Link
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.site_information import SiteInformation
from drafter.payloads.kinds.page import Page
from drafter.router.defaults.about import default_about, render_information_value


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
