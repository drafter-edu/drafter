"""Images as a first-class Drafter value: the `Picture` type and helpers.

This module is a *data-layer leaf* (like `drafter.data.files`): the router,
details, and component layers can all import it without cycles. It owns the
one shared image value type (`Picture`) plus the encoding helpers that every
other subsystem uses instead of re-implementing "PIL image to base64 PNG".

A `Picture` is pixels plus optional file metadata (filename, MIME type). It
converts cheaply to and from the four external image forms: raw bytes, data
URLs, files-with-metadata, and URLs. Students can receive one from a route
parameter (file upload or camera), store it in state, manipulate it with the
curated methods, and hand it back to components like `Image` and `Download`.
"""

import base64
import io
import urllib.parse

from PIL import Image as PILImage

from drafter.data.errors import StudentFacingError

__all__ = [
    "Picture",
    "bytes_to_data_url",
    "decode_data_url",
    "encode_image",
    "pil_to_data_url",
    "sniff_image_mime",
    "thumbnail_data_url",
]

DEFAULT_MIME_TYPE = "image/png"
"""MIME type used when an image's format is unknown or freshly synthesized."""

_MIME_TO_FORMAT = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/gif": "GIF",
    "image/webp": "WEBP",
    "image/bmp": "BMP",
    "image/x-icon": "ICO",
    "image/vnd.microsoft.icon": "ICO",
    "image/tiff": "TIFF",
}

_FORMAT_TO_MIME = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "JPG": "image/jpeg",
    "GIF": "image/gif",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
    "ICO": "image/x-icon",
    "TIFF": "image/tiff",
}

_EXTENSION_TO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".ico": "image/x-icon",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}

_SIZE_STEPS = (
    "Use whole numbers greater than zero for the width and height, like "
    "Picture.new(200, 100).",
    "If you calculated the size, print the numbers first to make sure "
    "they are positive integers (not decimals, strings, or zero).",
)
"""Shared "what to try next" steps for bad width/height arguments."""

_DATA_URL_STEPS = (
    "Make sure the text starts with 'data:image/...;base64,' followed by "
    "the encoded image data.",
    "If the text came from a file or website, pass the file path or "
    "web address to Picture(...) instead.",
)
"""Shared "what to try next" steps for malformed data URLs."""

_MAGIC_NUMBERS = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"BM", "image/bmp"),
    (b"\x00\x00\x01\x00", "image/x-icon"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
]


def sniff_image_mime(data: bytes) -> str | None:
    """Guess an image MIME type from a payload's magic numbers.

    Args:
        data: The encoded file bytes to inspect.

    Returns:
        The detected MIME type (e.g. ``"image/png"``), or None when the
        bytes do not start with a recognized image signature.
    """
    if not isinstance(data, (bytes, bytearray)):
        return None
    header = bytes(data[:16])
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    for magic, mime in _MAGIC_NUMBERS:
        if header.startswith(magic):
            return mime
    return None


def _format_for_mime(mime_type: str | None) -> str:
    """PIL save format for a MIME type, defaulting to PNG."""
    if not mime_type:
        return "PNG"
    return _MIME_TO_FORMAT.get(mime_type.lower(), "PNG")


def _mime_for_format(format: str | None) -> str:
    """MIME type for a PIL format name, defaulting to image/png."""
    if not format:
        return DEFAULT_MIME_TYPE
    return _FORMAT_TO_MIME.get(format.upper(), DEFAULT_MIME_TYPE)


def _mime_for_path(path: str) -> str | None:
    """MIME type inferred from a file path's extension, or None."""
    lowered = str(path).lower()
    for extension, mime in _EXTENSION_TO_MIME.items():
        if lowered.endswith(extension):
            return mime
    return None


def encode_image(image: PILImage.Image, format: str = "PNG") -> bytes:
    """Encode a PIL image as file bytes in the given format.

    JPEG cannot store transparency, so images with an alpha channel (or a
    palette) are converted to RGB before a JPEG encode rather than failing.

    Args:
        image: The PIL image to encode.
        format: A PIL format name such as "PNG" or "JPEG".

    Returns:
        The encoded file bytes.
    """
    format = (format or "PNG").upper()
    if format == "JPG":
        format = "JPEG"
    if format == "JPEG" and image.mode not in ("RGB", "L", "CMYK"):
        image = image.convert("RGB")
    output = io.BytesIO()
    image.save(output, format=format)
    return output.getvalue()


def bytes_to_data_url(data: bytes, mime_type: str = DEFAULT_MIME_TYPE) -> str:
    """Wrap encoded file bytes in a base64 data URL.

    Args:
        data: The encoded file bytes.
        mime_type: The MIME type to record in the URL.

    Returns:
        A ``data:<mime>;base64,...`` URL string.
    """
    encoded = base64.b64encode(bytes(data)).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def pil_to_data_url(image: PILImage.Image, format: str = "PNG") -> str:
    """Encode a PIL image directly as a base64 data URL.

    Args:
        image: The PIL image to encode.
        format: A PIL format name such as "PNG" or "JPEG".

    Returns:
        A ``data:<mime>;base64,...`` URL string.
    """
    return bytes_to_data_url(encode_image(image, format), _mime_for_format(format))


def decode_data_url(url: str) -> tuple[bytes, str]:
    """Decode a data URL into its payload bytes and MIME type.

    Args:
        url: A ``data:`` URL, base64-encoded or percent-encoded.

    Returns:
        Tuple of (decoded bytes, MIME type). The MIME type defaults to
        ``image/png`` when the URL does not declare one.

    Raises:
        StudentFacingError: If the string is not a well-formed data URL.
    """
    if not isinstance(url, str) or not url.startswith("data:"):
        raise StudentFacingError(
            f"Not a data URL: {url[:64]!r}",
            friendly=(
                "This text is not a data URL, which is a special kind of "
                "text that starts with 'data:' and contains an image's "
                "encoded data."
            ),
            steps=_DATA_URL_STEPS,
        )
    header, _, payload = url.partition(",")
    if not _:
        raise StudentFacingError(
            "Malformed data URL: missing ',' separator.",
            friendly=(
                "This data URL is incomplete: it is missing the comma that "
                "separates the 'data:image/...' header from the encoded "
                "image data."
            ),
            steps=_DATA_URL_STEPS,
        )
    header = header[len("data:") :]
    is_base64 = header.endswith(";base64")
    if is_base64:
        header = header[: -len(";base64")]
    mime_type = header.split(";")[0] or DEFAULT_MIME_TYPE
    if is_base64:
        data = base64.b64decode(payload)
    else:
        data = urllib.parse.unquote_to_bytes(payload)
    return data, mime_type


def thumbnail_data_url(picture_or_pil, max_edge: int = 128) -> str:
    """Encode a small PNG thumbnail of an image as a data URL.

    Used for debug telemetry so a 12-megapixel photo does not ship megabytes
    of base64 with every state snapshot.

    Args:
        picture_or_pil: A `Picture` or PIL image.
        max_edge: Maximum width/height of the thumbnail in pixels.

    Returns:
        A PNG data URL no larger than ``max_edge`` on either side.
    """
    if isinstance(picture_or_pil, Picture):
        image = picture_or_pil._as_pil()
    else:
        image = picture_or_pil
    if image.width > max_edge or image.height > max_edge:
        image = image.copy()
        image.thumbnail((max_edge, max_edge))
    return pil_to_data_url(image, "PNG")


class Picture:
    """An image value: pixels plus optional file metadata.

    A `Picture` can be built from a path, URL, or data URL string; raw
    bytes; a PIL image; an uploaded file; or a captured `Photo` — and can
    convert back out to bytes, a data URL, a PIL image, or a saved file.
    Manipulation methods (`resize`, `rotate`, `crop`, ...) each return a
    new `Picture`, and two Pictures are `==` when their pixels match, so
    Pictures stored in state work naturally with `assert_equal`.

    URL-backed Pictures are lazy: `Picture("https://.../dog.png")` does not
    fetch anything until the pixels are first needed, so handing one to the
    `Image` component just uses the URL directly.

    Attributes:
        filename: Original upload/file name, if any.
        mime_type: The image's MIME type; sniffed or provided, defaulting
            to ``image/png``.
    """

    filename: str | None
    mime_type: str

    def __init__(
        self, source, filename: str | None = None, mime_type: str | None = None
    ):
        """Build a Picture from any supported image source.

        Args:
            source: A path, URL, or data URL string; ``bytes``/``bytearray``;
                a PIL image; another `Picture` (copied); an uploaded
                `DrafterBinaryFile`; or a captured `Photo`.
            filename: Optional filename to record as metadata.
            mime_type: Optional MIME type override.

        Raises:
            StudentFacingError: If the source is not a supported type, or
                its data cannot be decoded as an image.
        """
        self._pil: PILImage.Image | None = None
        self._encoded: bytes | None = None
        self._url: str | None = None
        self.filename = filename
        self.mime_type = mime_type or DEFAULT_MIME_TYPE

        if isinstance(source, Picture):
            self._init_from_picture(source, filename, mime_type)
        elif isinstance(source, PILImage.Image):
            self._init_from_pil(source, filename, mime_type)
        elif isinstance(source, (bytes, bytearray)):
            self._init_from_bytes(bytes(source), filename, mime_type)
        elif isinstance(source, str):
            self._init_from_string(source, filename, mime_type)
        elif hasattr(source, "content") and hasattr(source, "filename"):
            # An uploaded file (DrafterBinaryFile or compatible).
            content = source.content
            if isinstance(content, str):
                content = content.encode("utf-8")
            self._init_from_bytes(
                bytes(content),
                filename or source.filename,
                mime_type or getattr(source, "content_type", None),
            )
        elif hasattr(source, "status") and hasattr(source, "data_url"):
            # A captured Photo (or compatible camera envelope).
            data_url = source.data_url
            if not data_url:
                status = getattr(source, "status", "unknown")
                message = getattr(source, "message", None)
                detail = f" ({message})" if message else ""
                raise StudentFacingError(
                    f"This Photo has no image data (status: {status}{detail}). "
                    f"Check photo.status before building a Picture from it.",
                    friendly=(
                        "This Photo is empty, so there is no image to turn "
                        "into a Picture; the camera may have failed or been "
                        "denied permission."
                    ),
                    steps=(
                        "Check photo.status before using the photo, and only "
                        "build a Picture when the status is 'captured'.",
                        "Try taking the photo again, and make sure the "
                        "browser has permission to use the camera.",
                    ),
                )
            data, url_mime = decode_data_url(data_url)
            self._init_from_bytes(data, filename, mime_type or url_mime)
        else:
            raise StudentFacingError(
                f"Cannot make a Picture from {type(source).__name__}. Provide "
                f"a filename, URL, bytes, a PIL image, or another Picture.",
                friendly=(
                    f"Picture(...) does not know how to turn a "
                    f"{type(source).__name__} value into an image."
                ),
                steps=(
                    "Pass Picture(...) an image file name, a web address, "
                    "an uploaded file, or another Picture.",
                    "Print the value you are passing in to see what it "
                    "actually is; it may not be the image you expected.",
                ),
            )

    # -- construction helpers --------------------------------------------

    def _init_from_picture(self, source: "Picture", filename, mime_type) -> None:
        self._pil = source._pil.copy() if source._pil is not None else None
        self._encoded = source._encoded
        self._url = source._url
        self.filename = filename or source.filename
        self.mime_type = mime_type or source.mime_type

    def _init_from_pil(self, source: PILImage.Image, filename, mime_type) -> None:
        self._pil = source
        self.filename = filename or getattr(source, "filename", None) or None
        self.mime_type = mime_type or _mime_for_format(getattr(source, "format", None))

    def _init_from_bytes(self, data: bytes, filename, mime_type) -> None:
        try:
            image = PILImage.open(io.BytesIO(data))
            image.load()
        except Exception as error:
            name = f" {filename!r}" if filename else ""
            raise StudentFacingError(
                f"Could not read{name} as an image ({error}). Perhaps the "
                f"data is not an image?",
                friendly=(
                    "Drafter could not understand this data as a picture; "
                    "it may be a different kind of file (like text) or a "
                    "damaged or unsupported image."
                ),
                steps=(
                    "Check that the file really is an image, such as a "
                    ".png, .jpg, or .gif file.",
                    "Try opening the file in another program to make sure "
                    "it is not corrupted.",
                ),
            ) from error
        self._pil = image
        self._encoded = data
        self.filename = filename
        self.mime_type = (
            mime_type
            or sniff_image_mime(data)
            or _mime_for_format(getattr(image, "format", None))
        )

    def _init_from_string(self, source: str, filename, mime_type) -> None:
        if source.startswith("data:"):
            data, url_mime = decode_data_url(source)
            self._init_from_bytes(data, filename, mime_type or url_mime)
        elif source.startswith(("http://", "https://")):
            # Lazy: hold the URL, fetch only when pixels are first needed.
            self._url = source
            tail = urllib.parse.urlparse(source).path.rsplit("/", 1)[-1]
            self.filename = filename or (tail if "." in tail else None)
            self.mime_type = mime_type or _mime_for_path(source) or DEFAULT_MIME_TYPE
        else:
            data = self._read_path(source)
            self._init_from_bytes(
                data,
                filename or str(source).replace("\\", "/").rsplit("/", 1)[-1],
                mime_type or _mime_for_path(source),
            )

    @staticmethod
    def _read_path(path: str) -> bytes:
        # Drafter's environment-aware open: fetches over HTTP in Pyodide and
        # resolves against the configured user directory on desktop.
        from drafter.files.opening import open as drafter_open

        with drafter_open(path, "rb") as file:
            return file.read()

    @classmethod
    def from_bytes(
        cls, data: bytes, filename: str | None = None, mime_type: str | None = None
    ) -> "Picture":
        """Build a Picture from encoded file bytes (a PNG file's bytes, etc.)."""
        return cls(bytes(data), filename=filename, mime_type=mime_type)

    @classmethod
    def from_data_url(cls, url: str) -> "Picture":
        """Build a Picture from a ``data:image/...`` URL."""
        data, mime_type = decode_data_url(url)
        return cls(data, mime_type=mime_type)

    @classmethod
    def from_url(cls, url: str) -> "Picture":
        """Build a lazy Picture from an ``http(s)://`` URL.

        The image is not fetched until its pixels or bytes are first used.
        """
        picture = cls.__new__(cls)
        picture._pil = None
        picture._encoded = None
        picture._url = None
        picture.filename = None
        picture.mime_type = DEFAULT_MIME_TYPE
        picture._init_from_string(url, None, None)
        return picture

    @classmethod
    def from_file(cls, path: str) -> "Picture":
        """Build a Picture by reading an image file from a path."""
        return cls(str(path))

    @classmethod
    def from_pil(cls, image: PILImage.Image, filename: str | None = None) -> "Picture":
        """Wrap an existing PIL image as a Picture."""
        return cls(image, filename=filename)

    @classmethod
    def new(cls, width: int, height: int, color="white") -> "Picture":
        """Create a new blank Picture of the given size and color.

        Args:
            width: Width in pixels (positive).
            height: Height in pixels (positive).
            color: Fill color: a name ("red"), hex string ("#ff0000"), or
                (red, green, blue) tuple. Defaults to white.

        Returns:
            A new Picture filled with the color.
        """
        for label, dimension in (("width", width), ("height", height)):
            if (
                not isinstance(dimension, int)
                or isinstance(dimension, bool)
                or dimension <= 0
            ):
                raise StudentFacingError(
                    f"Picture.new {label} must be a positive whole number of "
                    f"pixels, not {dimension!r}.",
                    friendly=(
                        f"A new Picture's {label} has to be a whole number "
                        f"of pixels greater than zero, and {dimension!r} "
                        f"is not."
                    ),
                    steps=_SIZE_STEPS,
                )
        return cls(PILImage.new("RGB", (width, height), color))

    # -- loading ----------------------------------------------------------

    @property
    def url(self) -> str | None:
        """The backing URL for a URL-sourced Picture, or None.

        Set only while the Picture's pixels are byte-identical to what the
        URL serves (manipulations return new Pictures without it), so it is
        always safe to display the URL instead of the pixels.
        """
        return self._url

    def is_loaded(self) -> bool:
        """Whether the pixel data has been loaded (URL Pictures load lazily)."""
        return self._pil is not None

    def _ensure_loaded(self) -> PILImage.Image:
        if self._pil is None:
            if self._url is None:
                raise StudentFacingError(
                    "This Picture has no image data to load.",
                    friendly=(
                        "This Picture is empty: it has no pixels and no web "
                        "address to fetch them from, so it cannot be used."
                    ),
                    steps=(
                        "Rebuild the Picture from a real source, like an "
                        "image file name, a web address, or an uploaded "
                        "file.",
                    ),
                )
            try:
                data = self._read_path(self._url)
                image = PILImage.open(io.BytesIO(data))
                image.load()
            except Exception as error:
                raise StudentFacingError(
                    f"Could not load the image at {self._url!r} ({error}). "
                    f"Check that the URL is correct and the site allows "
                    f"downloading it.",
                    friendly=(
                        "Drafter tried to download this Picture's image "
                        "from its web address, but the download failed."
                    ),
                    steps=(
                        "Paste the URL into your browser to check that it "
                        "really shows an image.",
                        "Check your internet connection, and watch out for "
                        "typos in the URL.",
                        "Some websites block downloads from other pages; "
                        "try an image from a different site.",
                    ),
                ) from error
            self._pil = image
            self._encoded = data
            sniffed = sniff_image_mime(data)
            if sniffed:
                self.mime_type = sniffed
        return self._pil

    def _as_pil(self) -> PILImage.Image:
        """The underlying PIL image (loaded on demand); internal use only."""
        return self._ensure_loaded()

    # -- the four external forms, back out --------------------------------

    def to_bytes(self, format: str | None = None) -> bytes:
        """The image as encoded file bytes.

        Uploaded or fetched images round-trip their original bytes exactly
        when no re-encode is needed; otherwise the pixels are encoded in
        the requested (or original) format.

        Args:
            format: Optional PIL format name ("PNG", "JPEG", ...). Defaults
                to the image's own format.

        Returns:
            The encoded file bytes.
        """
        image = self._ensure_loaded()
        if format is None:
            if self._encoded is not None:
                return self._encoded
            format = _format_for_mime(self.mime_type)
        elif self._encoded is not None and _mime_for_format(format) == self.mime_type:
            return self._encoded
        return encode_image(image, format)

    def to_data_url(self, format: str | None = None) -> str:
        """The image as a base64 data URL, suitable for an ``img`` src."""
        data = self.to_bytes(format)
        mime_type = _mime_for_format(format) if format else self.mime_type
        return bytes_to_data_url(data, mime_type)

    def to_pil(self) -> PILImage.Image:
        """A copy of the image as a PIL image, for the full PIL API.

        Returns a copy, so changes made through PIL do not silently alter
        this Picture.
        """
        return self._ensure_loaded().copy()

    def save(self, path: str, format: str | None = None) -> None:
        """Save the image to a file.

        Args:
            path: Where to write the file; the extension chooses the format
                (e.g. ``.png``, ``.jpg``) unless `format` is given.
            format: Optional explicit PIL format name.
        """
        if format is None:
            path_mime = _mime_for_path(path)
            if path_mime:
                format = _format_for_mime(path_mime)
        data = self.to_bytes(format)
        from drafter.files.opening import open as drafter_open

        with drafter_open(path, "wb") as file:
            file.write(data)

    # -- metadata ----------------------------------------------------------

    @property
    def width(self) -> int:
        """Width of the image in pixels."""
        return self._ensure_loaded().width

    @property
    def height(self) -> int:
        """Height of the image in pixels."""
        return self._ensure_loaded().height

    # -- curated manipulation (each returns a new Picture) -----------------

    def _derive(self, image: PILImage.Image) -> "Picture":
        """New Picture from manipulated pixels: metadata kept, format PNG."""
        result = Picture(image, filename=self.filename)
        result.mime_type = DEFAULT_MIME_TYPE
        return result

    def resize(self, width: int, height: int) -> "Picture":
        """A new Picture resized to exactly ``width`` by ``height`` pixels."""
        for label, dimension in (("width", width), ("height", height)):
            if (
                not isinstance(dimension, int)
                or isinstance(dimension, bool)
                or dimension <= 0
            ):
                raise StudentFacingError(
                    f"Picture.resize {label} must be a positive whole number "
                    f"of pixels, not {dimension!r}.",
                    friendly=(
                        f"To resize a Picture, the new {label} has to be a "
                        f"whole number of pixels greater than zero, and "
                        f"{dimension!r} is not."
                    ),
                    steps=_SIZE_STEPS,
                )
        return self._derive(self._ensure_loaded().resize((width, height)))

    def scale(self, factor: float) -> "Picture":
        """A new Picture scaled by a factor (0.5 halves, 2 doubles)."""
        if (
            not isinstance(factor, (int, float))
            or isinstance(factor, bool)
            or factor <= 0
        ):
            raise StudentFacingError(
                f"Picture.scale factor must be a positive number, not {factor!r}.",
                friendly=(
                    f"To scale a Picture, the factor has to be a number "
                    f"greater than zero, and {factor!r} is not."
                ),
                steps=(
                    "Use a positive number: 0.5 makes the picture half as "
                    "big, and 2 makes it twice as big.",
                    "If you want an exact size instead, use "
                    "picture.resize(width, height).",
                ),
            )
        image = self._ensure_loaded()
        width = max(1, round(image.width * factor))
        height = max(1, round(image.height * factor))
        return self._derive(image.resize((width, height)))

    def rotate(self, degrees: float) -> "Picture":
        """A new Picture rotated counter-clockwise, growing to fit."""
        return self._derive(self._ensure_loaded().rotate(degrees, expand=True))

    def crop(self, left: int, top: int, right: int, bottom: int) -> "Picture":
        """A new Picture cut down to the box from (left, top) to (right, bottom)."""
        image = self._ensure_loaded()
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise StudentFacingError(
                f"Picture.crop box ({left}, {top}, {right}, {bottom}) must fit "
                f"inside the image (width {image.width}, height {image.height}) "
                f"with left < right and top < bottom.",
                friendly=(
                    f"The crop box does not fit inside this Picture, which "
                    f"is {image.width} pixels wide and {image.height} "
                    f"pixels tall."
                ),
                steps=(
                    "Keep all four numbers between 0 and the picture's "
                    "width or height.",
                    "Make sure left is smaller than right and top is "
                    "smaller than bottom.",
                    "Check the picture's size first with picture.width and "
                    "picture.height.",
                ),
            )
        return self._derive(image.crop((left, top, right, bottom)))

    def flip_horizontal(self) -> "Picture":
        """A new Picture mirrored left-to-right."""
        return self._derive(
            self._ensure_loaded().transpose(PILImage.Transpose.FLIP_LEFT_RIGHT)
        )

    def flip_vertical(self) -> "Picture":
        """A new Picture mirrored top-to-bottom."""
        return self._derive(
            self._ensure_loaded().transpose(PILImage.Transpose.FLIP_TOP_BOTTOM)
        )

    def grayscale(self) -> "Picture":
        """A new Picture with the colors converted to shades of gray."""
        return self._derive(self._ensure_loaded().convert("L").convert("RGB"))

    # -- pixel access (media-computation style) ----------------------------

    def _check_coordinates(self, x: int, y: int) -> None:
        image = self._ensure_loaded()
        if not (
            isinstance(x, int)
            and isinstance(y, int)
            and not isinstance(x, bool)
            and not isinstance(y, bool)
        ):
            raise StudentFacingError(
                f"Pixel coordinates must be whole numbers, not ({x!r}, {y!r}).",
                friendly=(
                    "Pixel positions have to be whole numbers, because a "
                    "picture is a grid of pixels counted from 0."
                ),
                steps=(
                    "Use whole numbers (integers) for x and y, like get_pixel(10, 20).",
                    "If you calculated the position, wrap it in int(...) "
                    "or use // instead of / when dividing.",
                ),
            )
        if not (0 <= x < image.width and 0 <= y < image.height):
            raise IndexError(
                f"Pixel ({x}, {y}) is outside the image (width {image.width}, "
                f"height {image.height})."
            )

    def get_pixel(self, x: int, y: int) -> tuple[int, int, int]:
        """The (red, green, blue) color of the pixel at (x, y)."""
        self._check_coordinates(x, y)
        image = self._ensure_loaded()
        if image.mode != "RGB":
            image = image.convert("RGB")
        # An RGB-mode image always yields a 3-int tuple here.
        pixel = image.getpixel((x, y))
        assert isinstance(pixel, tuple)
        return pixel[:3]  # type: ignore[return-value]

    def set_pixel(self, x: int, y: int, color) -> None:
        """Change the pixel at (x, y) to a color, modifying this Picture.

        Args:
            x: Horizontal position, 0 at the left edge.
            y: Vertical position, 0 at the top edge.
            color: A color name ("red"), hex string ("#ff0000"), or
                (red, green, blue) tuple.
        """
        self._check_coordinates(x, y)
        image = self._ensure_loaded()
        if isinstance(color, str):
            from PIL import ImageColor

            color = ImageColor.getrgb(color)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
            self._pil = image
        image.putpixel((x, y), tuple(color))
        # The pixels no longer match any cached encoding or backing URL.
        self._encoded = None
        self._url = None

    # -- value semantics ----------------------------------------------------

    def __eq__(self, other) -> bool:
        """Compare by pixels (mode, size, and raw data); metadata such as
        the filename is intentionally ignored."""
        if isinstance(other, PILImage.Image):
            other = Picture(other)
        if not isinstance(other, Picture):
            return NotImplemented
        mine, theirs = self._ensure_loaded(), other._ensure_loaded()
        return (
            mine.mode == theirs.mode
            and mine.size == theirs.size
            and mine.tobytes() == theirs.tobytes()
        )

    # Mutable via set_pixel, so Pictures are explicitly unhashable.
    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        """Short form like ``Picture('dog.png', 640x480, PNG)`` — never a
        base64 dump."""
        parts = []
        if self.filename:
            parts.append(repr(self.filename))
        elif self._url:
            parts.append(repr(self._url))
        if self._pil is not None:
            parts.append(f"{self._pil.width}x{self._pil.height}")
            parts.append(_format_for_mime(self.mime_type))
        else:
            parts.append("not loaded yet")
        return f"Picture({', '.join(parts)})"

    def __copy__(self) -> "Picture":
        """Copy the picture (pixels are duplicated, metadata kept)."""
        return Picture(self)

    def __deepcopy__(self, memo) -> "Picture":
        """Deep-copy the picture; unloaded URL sources stay unloaded."""
        result = Picture.__new__(Picture)
        memo[id(self)] = result
        result._pil = self._pil.copy() if self._pil is not None else None
        result._encoded = self._encoded
        result._url = self._url
        result.filename = self.filename
        result.mime_type = self.mime_type
        return result
