"""
Tests for new V2 infrastructure components.
"""

import pytest
from drafter import (
    Site,
    Fragment,
    Redirect,
    Download,
    Progress,
    Update,
    Channels,
)
from drafter.history.state import SiteState
from drafter.config.client_server import ClientServerConfiguration


class TestSite:
    """Tests for the Site class."""

    def test_site_creation(self):
        """Test creating a Site with metadata."""
        site = Site(
            title="Test Site",
            description="A test site",
            author="Test Author",
            language="en",
        )
        assert site.title == "Test Site"
        assert site.description == "A test site"
        assert site.author == "Test Author"
        assert site.language == "en"

    def test_site_add_route(self):
        """Test adding a route to a Site."""
        site = Site()

        def test_route():
            return "test"

        site.add_route("/test", test_route)
        assert site.get_route("/test") == test_route

    def test_site_get_all_routes(self):
        """Test getting all routes from a Site."""
        site = Site()

        def route1():
            return "route1"

        def route2():
            return "route2"

        site.add_route("/route1", route1)
        site.add_route("/route2", route2)

        routes = site.get_all_routes()
        assert len(routes) == 2
        assert routes["/route1"] == route1
        assert routes["/route2"] == route2


class TestFragmentPayload:
    """Tests for the Fragment payload."""

    def test_fragment_render(self):
        """Test rendering a Fragment."""
        state = SiteState()
        config = ClientServerConfiguration()
        fragment = Fragment(content="<p>Test content</p>", target_id="test-id")

        rendered = fragment.render(state, config)
        assert "<p>Test content</p>" in rendered


class TestRedirectPayload:
    """Tests for the Redirect payload."""

    def test_redirect_render(self):
        """Test rendering a Redirect."""
        state = SiteState()
        config = ClientServerConfiguration()
        redirect = Redirect(url="/target-page")

        rendered = redirect.render(state, config)
        assert "/target-page" in rendered
        assert "meta" in rendered.lower()


class TestProgressPayload:
    """Tests for the Progress payload."""

    def test_progress_with_percentage(self):
        """Test Progress with percentage."""
        state = SiteState()
        config = ClientServerConfiguration()
        progress = Progress(message="Loading...", percentage=50.0)

        rendered = progress.render(state, config)
        assert "Loading..." in rendered
        assert "50" in rendered
        assert "progress" in rendered.lower()

    def test_progress_with_steps(self):
        """Test Progress with current/total steps."""
        state = SiteState()
        config = ClientServerConfiguration()
        progress = Progress(message="Processing...", current=5, total=10)

        rendered = progress.render(state, config)
        assert "Processing..." in rendered
        assert "5" in rendered
        assert "10" in rendered


class TestDownloadPayload:
    """Tests for the Download payload."""

    def test_download_render(self):
        """Test rendering a Download."""
        state = SiteState()
        config = ClientServerConfiguration()
        download = Download(
            content="test data", filename="test.txt", mime_type="text/plain"
        )

        rendered = download.render(state, config)
        assert "test.txt" in rendered


class TestUpdatePayload:
    """Tests for the Update payload."""

    def test_update_render(self):
        """Test rendering an Update."""
        state = SiteState()
        config = ClientServerConfiguration()
        update = Update(updates={"element1": "<p>New content</p>"})

        rendered = update.render(state, config)
        assert "element1" in rendered
        assert "New content" in rendered


class TestChannels:
    """Tests for the Channels utility class."""

    def test_create_empty(self):
        """Test creating empty channels."""
        channels = Channels.create_empty()
        assert isinstance(channels, dict)
        assert len(channels) == 0

    def test_add_before_script(self):
        """Test adding a before script."""
        channels = Channels.create_empty()
        Channels.add_before_script(channels, "console.log('before');")

        assert Channels.BEFORE in channels
        assert "console.log('before');" in channels[Channels.BEFORE]

    def test_add_after_script(self):
        """Test adding an after script."""
        channels = Channels.create_empty()
        Channels.add_after_script(channels, "console.log('after');")

        assert Channels.AFTER in channels
        assert "console.log('after');" in channels[Channels.AFTER]

    def test_add_audio_message(self):
        """Test adding an audio message."""
        channels = Channels.create_empty()
        message = {"action": "play", "src": "audio.mp3"}
        Channels.add_audio_message(channels, message)

        assert Channels.AUDIO in channels
        assert message in channels[Channels.AUDIO]

    def test_add_custom(self):
        """Test adding custom channel data."""
        channels = Channels.create_empty()
        Channels.add_custom(channels, "my_channel", {"key": "value"})

        assert "my_channel" in channels
        assert channels["my_channel"]["key"] == "value"

    def test_get_channel(self):
        """Test getting channel data."""
        channels = {"test": "value"}
        value = Channels.get_channel(channels, "test")
        assert value == "value"

        default_value = Channels.get_channel(channels, "nonexistent", "default")
        assert default_value == "default"

    def test_merge_channels(self):
        """Test merging two channel dictionaries."""
        channels1 = {"before": ["script1"], "custom": "value1"}
        channels2 = {"before": ["script2"], "after": ["script3"]}

        merged = Channels.merge_channels(channels1, channels2)

        assert "script1" in merged["before"]
        assert "script2" in merged["before"]
        assert "script3" in merged["after"]
        assert merged["custom"] == "value1"
