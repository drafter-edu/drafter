from dataclasses import dataclass

DRAFTER_TAG_IDS = {
    "ROOT": "drafter-root--",
    "SITE": "drafter-site--",
    "FRAME": "drafter-frame--",
    "HEADER": "drafter-header--",
    "BODY": "drafter-body--",
    "FOOTER": "drafter-footer--",
    "FORM": "drafter-form--",
    "DEBUG": "drafter-debug--",
}

SITE_HTML_TEMPLATE = f"""
<div id="{DRAFTER_TAG_IDS["SITE"]}">
  <div id="{DRAFTER_TAG_IDS["FRAME"]}">
    <div id="{DRAFTER_TAG_IDS["HEADER"]}"></div>
    <div id="{DRAFTER_TAG_IDS["BODY"]}">
      <form id="{DRAFTER_TAG_IDS["FORM"]}">Loading</form>
    </div>
    <div id="{DRAFTER_TAG_IDS["FOOTER"]}"></div>
  </div>
  <div id="{DRAFTER_TAG_IDS["DEBUG"]}"></div>
</div>
"""


@dataclass
class Site:
    def render(self) -> str:
        return SITE_HTML_TEMPLATE
