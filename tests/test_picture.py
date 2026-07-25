"""Tests for the Picture value type and shared image encoding helpers."""

import copy
import io

import pytest
from PIL import Image as PILImage

from drafter.data.images import (
    Picture,
    bytes_to_data_url,
    decode_data_url,
    encode_image,
    pil_to_data_url,
    sniff_image_mime,
    thumbnail_data_url,
)


def make_pil(color="red", size=(4, 3), mode="RGB"):
    return PILImage.new(mode, size, color)


def png_bytes(color="red", size=(4, 3)):
    output = io.BytesIO()
    make_pil(color, size).save(output, format="PNG")
    return output.getvalue()


# ============================================================================
# Helpers
# ============================================================================


class TestHelpers:
    def test_sniff_png(self):
        assert sniff_image_mime(png_bytes()) == "image/png"

    def test_sniff_jpeg(self):
        data = encode_image(make_pil(), "JPEG")
        assert sniff_image_mime(data) == "image/jpeg"

    def test_sniff_gif(self):
        data = encode_image(make_pil(mode="P"), "GIF")
        assert sniff_image_mime(data) == "image/gif"

    def test_sniff_unknown(self):
        assert sniff_image_mime(b"hello world") is None
        assert sniff_image_mime(b"") is None

    def test_encode_image_jpeg_from_rgba(self):
        # JPEG cannot store alpha; the encoder converts instead of failing.
        data = encode_image(make_pil(mode="RGBA", color=(255, 0, 0, 128)), "JPEG")
        assert sniff_image_mime(data) == "image/jpeg"

    def test_bytes_to_data_url_round_trip(self):
        data = png_bytes()
        url = bytes_to_data_url(data, "image/png")
        assert url.startswith("data:image/png;base64,")
        decoded, mime = decode_data_url(url)
        assert decoded == data
        assert mime == "image/png"

    def test_pil_to_data_url(self):
        url = pil_to_data_url(make_pil())
        data, mime = decode_data_url(url)
        assert mime == "image/png"
        assert sniff_image_mime(data) == "image/png"

    def test_decode_data_url_rejects_non_data_url(self):
        with pytest.raises(ValueError):
            decode_data_url("https://example.com/dog.png")

    def test_decode_percent_encoded_data_url(self):
        data, mime = decode_data_url("data:text/plain,hello%20world")
        assert data == b"hello world"
        assert mime == "text/plain"

    def test_thumbnail_caps_size(self):
        big = PILImage.new("RGB", (512, 256), "blue")
        url = thumbnail_data_url(big, max_edge=128)
        data, _ = decode_data_url(url)
        thumb = PILImage.open(io.BytesIO(data))
        assert max(thumb.size) <= 128

    def test_thumbnail_accepts_picture(self):
        url = thumbnail_data_url(Picture(png_bytes()), max_edge=128)
        assert url.startswith("data:image/png;base64,")


# ============================================================================
# Construction and round-trips
# ============================================================================


class TestConstruction:
    def test_from_bytes_round_trips_exactly(self):
        data = png_bytes()
        picture = Picture.from_bytes(data, filename="dog.png")
        assert picture.to_bytes() == data
        assert picture.filename == "dog.png"
        assert picture.mime_type == "image/png"
        assert picture.width == 4 and picture.height == 3

    def test_constructor_accepts_bytes(self):
        picture = Picture(png_bytes())
        assert picture.width == 4

    def test_from_data_url(self):
        url = bytes_to_data_url(png_bytes(), "image/png")
        picture = Picture.from_data_url(url)
        assert picture.mime_type == "image/png"
        assert picture.to_data_url() == url

    def test_constructor_accepts_data_url(self):
        url = bytes_to_data_url(png_bytes(), "image/png")
        assert Picture(url).width == 4

    def test_from_pil(self):
        picture = Picture.from_pil(make_pil())
        assert picture.width == 4
        assert picture.mime_type == "image/png"

    def test_constructor_copies_picture(self):
        original = Picture(png_bytes(), filename="dog.png")
        duplicate = Picture(original)
        assert duplicate == original
        assert duplicate.filename == "dog.png"
        assert duplicate is not original

    def test_from_file(self, tmp_path):
        path = tmp_path / "dog.png"
        path.write_bytes(png_bytes())
        picture = Picture(str(path))
        assert picture.width == 4
        assert picture.filename == "dog.png"
        assert picture.mime_type == "image/png"

    def test_from_binary_file(self):
        from drafter.data.files import DrafterBinaryFile

        data = png_bytes()
        upload = DrafterBinaryFile("dog.png", data, "image/png", len(data))
        picture = Picture(upload)
        assert picture.filename == "dog.png"
        assert picture.to_bytes() == data

    def test_from_photo(self):
        from drafter.components.data.photo import Photo

        photo = Photo(
            status="granted",
            data_url=bytes_to_data_url(png_bytes(), "image/png"),
            width=4,
            height=3,
        )
        picture = Picture(photo)
        assert picture.width == 4

    def test_from_photo_without_data_fails_with_status(self):
        from drafter.components.data.photo import Photo

        photo = Photo(status="denied", message="Camera access denied")
        with pytest.raises(ValueError) as exc_info:
            Picture(photo)
        assert "denied" in str(exc_info.value)

    def test_bad_bytes_fail_helpfully(self):
        with pytest.raises(ValueError) as exc_info:
            Picture.from_bytes(b"not an image", filename="notes.txt")
        assert "notes.txt" in str(exc_info.value)

    def test_unsupported_source_fails_helpfully(self):
        with pytest.raises(ValueError) as exc_info:
            Picture(12345)
        assert "int" in str(exc_info.value)

    def test_new(self):
        picture = Picture.new(5, 4, "red")
        assert (picture.width, picture.height) == (5, 4)
        assert picture.get_pixel(0, 0) == (255, 0, 0)

    def test_new_rejects_bad_dimensions(self):
        with pytest.raises(ValueError):
            Picture.new(0, 5)
        with pytest.raises(ValueError):
            Picture.new(5, -1)

    def test_to_pil_returns_copy(self):
        picture = Picture(png_bytes())
        pil = picture.to_pil()
        pil.putpixel((0, 0), (0, 255, 0))
        assert picture.get_pixel(0, 0) == (255, 0, 0)

    def test_to_bytes_reencodes_on_format_change(self):
        picture = Picture(png_bytes())
        jpeg = picture.to_bytes("JPEG")
        assert sniff_image_mime(jpeg) == "image/jpeg"
        assert picture.to_data_url("JPEG").startswith("data:image/jpeg;base64,")

    def test_save(self, tmp_path):
        picture = Picture(png_bytes())
        target = tmp_path / "out.png"
        picture.save(str(target))
        assert sniff_image_mime(target.read_bytes()) == "image/png"

    def test_save_infers_jpeg_from_extension(self, tmp_path):
        picture = Picture(png_bytes())
        target = tmp_path / "out.jpg"
        picture.save(str(target))
        assert sniff_image_mime(target.read_bytes()) == "image/jpeg"


# ============================================================================
# Lazy URLs
# ============================================================================


class TestLazyUrl:
    URL = "https://example.com/images/dog.png"

    def test_url_construction_does_not_fetch(self, monkeypatch):
        def explode(path):
            raise AssertionError("should not fetch at construction")

        monkeypatch.setattr(Picture, "_read_path", staticmethod(explode))
        picture = Picture(self.URL)
        assert not picture.is_loaded()
        assert picture.url == self.URL
        assert picture.filename == "dog.png"
        assert "not loaded yet" in repr(picture)

    def test_pixel_access_triggers_fetch(self, monkeypatch):
        monkeypatch.setattr(
            Picture, "_read_path", staticmethod(lambda path: png_bytes())
        )
        picture = Picture(self.URL)
        assert picture.width == 4
        assert picture.is_loaded()

    def test_failed_fetch_names_url(self, monkeypatch):
        def fail(path):
            raise OSError("connection refused")

        monkeypatch.setattr(Picture, "_read_path", staticmethod(fail))
        picture = Picture(self.URL)
        with pytest.raises(ValueError) as exc_info:
            picture.width
        assert self.URL in str(exc_info.value)

    def test_deepcopy_keeps_descriptor_without_fetch(self, monkeypatch):
        def explode(path):
            raise AssertionError("should not fetch during deepcopy")

        monkeypatch.setattr(Picture, "_read_path", staticmethod(explode))
        picture = Picture(self.URL)
        duplicate = copy.deepcopy(picture)
        assert duplicate.url == self.URL
        assert not duplicate.is_loaded()


# ============================================================================
# Value semantics
# ============================================================================


class TestValueSemantics:
    def test_equal_pixels_are_equal(self):
        assert Picture(png_bytes()) == Picture(png_bytes())

    def test_metadata_does_not_affect_equality(self):
        left = Picture(png_bytes(), filename="a.png")
        right = Picture(png_bytes(), filename="b.png")
        assert left == right

    def test_different_pixels_not_equal(self):
        assert Picture(png_bytes("red")) != Picture(png_bytes("blue"))

    def test_equality_with_pil_image(self):
        assert Picture(make_pil()) == make_pil()

    def test_equality_with_other_types(self):
        assert Picture(png_bytes()) != "dog.png"

    def test_unhashable(self):
        with pytest.raises(TypeError):
            hash(Picture(png_bytes()))

    def test_repr_is_short(self):
        picture = Picture(png_bytes(), filename="dog.png")
        assert repr(picture) == "Picture('dog.png', 4x3, PNG)"
        assert len(repr(Picture(png_bytes((0, 0, 255), (640, 480))))) < 80

    def test_deepcopy_is_independent(self):
        picture = Picture(png_bytes())
        duplicate = copy.deepcopy(picture)
        duplicate.set_pixel(0, 0, "blue")
        assert picture.get_pixel(0, 0) == (255, 0, 0)
        assert duplicate.get_pixel(0, 0) == (0, 0, 255)

    def test_deepcopy_inside_structures(self):
        state = {"photo": Picture(png_bytes()), "count": 3}
        duplicate = copy.deepcopy(state)
        assert duplicate["photo"] == state["photo"]


# ============================================================================
# Manipulation and pixels
# ============================================================================


class TestManipulation:
    def test_resize(self):
        resized = Picture(png_bytes()).resize(8, 6)
        assert (resized.width, resized.height) == (8, 6)

    def test_resize_rejects_bad_dimensions(self):
        with pytest.raises(ValueError):
            Picture(png_bytes()).resize(0, 5)

    def test_scale(self):
        scaled = Picture(png_bytes("red", (4, 4))).scale(0.5)
        assert (scaled.width, scaled.height) == (2, 2)

    def test_rotate_expands(self):
        rotated = Picture(png_bytes("red", (4, 2))).rotate(90)
        assert (rotated.width, rotated.height) == (2, 4)

    def test_crop(self):
        cropped = Picture(png_bytes("red", (4, 4))).crop(1, 1, 3, 4)
        assert (cropped.width, cropped.height) == (2, 3)

    def test_crop_rejects_out_of_bounds(self):
        with pytest.raises(ValueError):
            Picture(png_bytes()).crop(0, 0, 100, 100)

    def test_flips(self):
        picture = Picture.new(2, 1, "red")
        picture.set_pixel(1, 0, "blue")
        assert picture.flip_horizontal().get_pixel(0, 0) == (0, 0, 255)
        tall = Picture.new(1, 2, "red")
        tall.set_pixel(0, 1, "blue")
        assert tall.flip_vertical().get_pixel(0, 0) == (0, 0, 255)

    def test_grayscale(self):
        gray = Picture.new(1, 1, (100, 150, 200)).grayscale()
        red, green, blue = gray.get_pixel(0, 0)
        assert red == green == blue

    def test_manipulation_returns_new_picture(self):
        original = Picture(png_bytes(), filename="dog.png")
        resized = original.resize(2, 2)
        assert resized is not original
        assert resized.filename == "dog.png"
        assert original.width == 4

    def test_manipulated_defaults_to_png(self):
        jpeg = Picture(encode_image(make_pil(), "JPEG"))
        assert jpeg.mime_type == "image/jpeg"
        assert jpeg.resize(2, 2).mime_type == "image/png"

    def test_get_pixel_bounds_check(self):
        with pytest.raises(IndexError):
            Picture(png_bytes()).get_pixel(99, 0)

    def test_set_pixel_invalidates_cached_bytes(self):
        data = png_bytes()
        picture = Picture(data)
        picture.set_pixel(0, 0, (0, 255, 0))
        assert picture.get_pixel(0, 0) == (0, 255, 0)
        # Re-encoded bytes must reflect the change, not the cached original.
        reloaded = Picture(picture.to_bytes())
        assert reloaded.get_pixel(0, 0) == (0, 255, 0)

    def test_get_pixel_on_palette_image(self):
        palette = Picture(make_pil(mode="P"))
        assert len(palette.get_pixel(0, 0)) == 3
