"""Tests for image components speaking the Picture value type."""

import pytest
from PIL import Image as PILImage

from drafter import Div, Download, Image, Page, Picture
from drafter.payloads.renderer import render


def make_picture(filename=None):
    picture = Picture.new(4, 3, "red")
    picture.filename = filename
    return picture


class TestImageComponent:
    def test_picture_renders_as_data_url(self):
        html = render(Image(make_picture())).flatten()
        assert 'src="data:image/png;base64,' in html

    def test_picture_filename_becomes_default_alt(self):
        html = render(Image(make_picture("dog.png"))).flatten()
        assert 'alt="dog.png"' in html

    def test_explicit_alt_wins(self):
        html = render(Image(make_picture("dog.png"), alt="A dog")).flatten()
        assert 'alt="A dog"' in html
        assert 'alt="dog.png"' not in html

    def test_unloaded_url_picture_renders_url(self, monkeypatch):
        def explode(path):
            raise AssertionError("rendering must not fetch the URL")

        monkeypatch.setattr(Picture, "_read_path", staticmethod(explode))
        picture = Picture("https://example.com/dog.png")
        html = render(Image(picture)).flatten()
        assert 'src="https://example.com/dog.png"' in html

    def test_pil_image_renders_as_data_url(self):
        html = render(Image(PILImage.new("RGB", (2, 2), "blue"))).flatten()
        assert 'src="data:image/png;base64,' in html

    def test_bytes_render_as_data_url(self):
        data = make_picture().to_bytes()
        html = render(Image(data)).flatten()
        assert 'src="data:image/png;base64,' in html

    def test_jpeg_bytes_keep_their_mime(self):
        data = make_picture().to_bytes("JPEG")
        html = render(Image(data)).flatten()
        assert 'src="data:image/jpeg;base64,' in html

    def test_plain_strings_still_render_as_urls(self):
        html = render(Image("photo.jpg")).flatten()
        assert 'src="/photo.jpg"' in html

    def test_open_and_new_are_deprecated(self, tmp_path):
        with pytest.warns(DeprecationWarning):
            Image("x").new("RGB", (2, 2))
        path = tmp_path / "dog.png"
        make_picture().save(str(path))
        with pytest.warns(DeprecationWarning):
            Image("x").open(str(path))


class TestDownloadComponent:
    def test_picture_content(self):
        html = render(Download("Save", "dog.png", make_picture())).flatten()
        assert 'href="data:image/png;base64,' in html
        assert 'download="dog.png"' in html

    def test_pil_content(self):
        content = PILImage.new("RGB", (2, 2), "blue")
        html = render(Download("Save", "dog.png", content)).flatten()
        assert 'href="data:image/png;base64,' in html

    def test_image_bytes_content(self):
        data = make_picture().to_bytes()
        html = render(Download("Save", "dog.png", data)).flatten()
        assert 'href="data:image/png;base64,' in html

    def test_string_content_unchanged(self):
        html = render(Download("Save", "notes.txt", "hello")).flatten()
        assert 'href="data:text/plain,hello"' in html


class TestPictureInPageContent:
    def test_picture_in_content_list_wraps_in_image(self):
        page = Page(None, ["Here is your photo:", make_picture()])
        assert isinstance(page.content[1], Image)
        assert isinstance(page.content[1].url, Picture)

    def test_single_picture_content_wraps(self):
        page = Page(None, make_picture())
        assert isinstance(page.content[0], Image)

    def test_nested_picture_renders_via_image(self):
        html = render(Div(make_picture())).flatten()
        assert 'src="data:image/png;base64,' in html

    def test_pages_with_equal_pictures_are_equal(self):
        # The testing story: assert_equal on pages/states holding images
        # is deterministic because Picture compares by pixels.
        left = Page(None, ["photo", Picture.new(4, 3, "red")])
        right = Page(None, ["photo", Picture.new(4, 3, "red")])
        different = Page(None, ["photo", Picture.new(4, 3, "blue")])
        assert left == right
        assert left != different

    def test_download_payload_accepts_picture(self):
        from drafter.payloads.kinds.download import Download as DownloadPayload

        payload = DownloadPayload("", "", "", make_picture("dog.png"))
        assert isinstance(payload.content, bytes)
        assert payload.mime_type == "image/png"
        assert payload.file_name == "dog.png"
