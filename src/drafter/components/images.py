from dataclasses import dataclass
import base64
import io
from typing import Optional
from drafter.image_support import HAS_PILLOW, PILImage
from drafter.components.page_content import Component
from drafter.components.links import LinkContent

BASE_IMAGE_FOLDER = "/__images"


@dataclass
class Image(Component, LinkContent):
    url: str
    width: Optional[int]
    height: Optional[int]

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

    def render(self, current_state, configuration):
        self.base_image_folder = configuration.deploy_image_path
        return super().render(current_state, configuration)

    def _handle_pil_image(self, image):
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def __str__(self) -> str:
        extra_settings = {}
        if self.width is not None:
            extra_settings["width"] = self.width
        if self.height is not None:
            extra_settings["height"] = self.height
        was_pil, url = self._handle_pil_image(self.url)
        if was_pil:
            return f"<img src='{url}' {self.parse_extra_settings(**extra_settings)}>"
        url, external = self._handle_url(self.url)
        if not external:
            url = self.base_image_folder + url
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<img src='{url}' {parsed_settings}>"


Picture = Image
