from dataclasses import dataclass
import base64
import io
from typing import Optional
from drafter.components.utilities.image_support import HAS_PILLOW, PILImage
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.links import LinkContent, UrlOrFunction
from drafter.components.planning.render_plan import RenderPlan
from drafter.helpers.urls import check_invalid_external_url, friendly_urls

BASE_IMAGE_FOLDER = "/__images"


@dataclass(repr=False)
class Image(Component):
    url: str
    width: Optional[int]
    height: Optional[int]

    tag = "img"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["src", "width", "height", "alt"]
    RENAME_ATTRS = {"url": "src"}

    ARGUMENTS = [
        ComponentArgument("url"),
        ComponentArgument("width", kind="keyword", default_value=None),
        ComponentArgument("height", kind="keyword", default_value=None),
    ]

    def __init__(self, url: str, width=None, height=None, **kwargs):
        self.url = url
        self.width = width
        self.height = height
        self.extra_settings = kwargs
        self.base_image_folder = BASE_IMAGE_FOLDER

    def open(self, *args, **kwargs):
        if not HAS_PILLOW:
            raise ImportError(
                "Pillow is not installed. Please install it to use this feature."
            )
        return PILImage.open(*args, **kwargs)

    def new(self, *args, **kwargs):
        if not HAS_PILLOW:
            raise ImportError(
                "Pillow is not installed. Please install it to use this feature."
            )
        return PILImage.new(*args, **kwargs)

    def _handle_pil_image(self, image):
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        # print("Handling PIL image.", image)
        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
        # figure = base64.b64encode(image["content"])
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def _handle_url(self, url: UrlOrFunction, external=None) -> tuple[str, bool]:
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        url = url if external else friendly_urls(url)
        return url, external

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)

        try:
            was_pil, url = self._handle_pil_image(self.url)
        except Exception as e:
            # Return an error message
            if "alt" not in attributes:
                attributes["alt"] = "Error loading image: " + str(e)
            return attributes

        if was_pil:
            attributes["src"] = url
        else:
            url_processed, external = self._handle_url(self.url)
            if not external:
                # Ensure we have a leading slash
                if not url_processed.startswith("/"):
                    url_processed = "/" + url_processed
                url_processed = self.base_image_folder + url_processed
            attributes["src"] = url_processed

        return attributes


Picture = Image
