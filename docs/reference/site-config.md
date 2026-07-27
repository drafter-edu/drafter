---
page_type: reference
title: Site configuration functions
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - set_website_title
  - set_website_favicon
  - set_website_framed
  - set_website_style
  - set_page_transition
  - set_error_page
  - set_button_spinners
  - add_website_header
  - add_website_css
  - set_site_information
  - get_site_information
  - hide_debug_information
  - show_debug_information
  - deploy_site
outcome: Look up every set_ and add_ configuration helper.
---

# Site configuration functions

These functions configure the whole site rather than one page. They
all follow the same placement rule: call them at the top level of your
program, after the imports and before `start_server(...)`. None of
them belong inside a route.

```python drafter height=220
from drafter import *

set_website_title("Fortune Teller")
set_website_style("water")


@route
def index() -> Page:
    return Page([
        "The site title and theme were set before the server started.\n",
        Button("Consult the orb", "index")
    ])


start_server()
```

## Appearance

### set_website_title

```python
set_website_title("My Amazing App")
```

Sets the title shown in the browser tab.

### set_website_favicon

```python
set_website_favicon("icon.png")
```

Sets the small browser-tab icon. Give the name of an image file (svg,
png, ico, ...) next to your Python file, or a full URL to an image.
When deploying, remember the file must travel with your site; see
[Image works locally but not deployed](../help/errors/missing-asset-on-deploy.md).

### set_website_style

```python
set_website_style("terminal")
```

Applies a [theme](themes.md) by name. `set_website_style("none")`
removes all styling for a blank slate. A misspelled name produces an
error listing every valid theme. The how-to is
[Use a theme](../add/change-appearance/themes.md).

### set_website_framed

```python
set_website_framed(False)
```

Controls whether your app sits inside Drafter's window frame. The
frame is helpful during development; deployed sites usually turn it
off so the app fills the page.

### set_page_transition

```python
set_page_transition("fade")
set_page_transition("black", 0.3)
```

Plays a visual transition whenever the visitor moves between pages.
`"fade"` fades the new page in from transparent; a CSS color such as
`"black"` or `"#004488"` fades in from a solid veil of that color;
`"none"` turns transitions off again. The second argument is the
duration in seconds (0.5 by default).

### set_button_spinners

```python
set_button_spinners(True)
```

When spinners are turned on, a pressed button shows a small spinner
and is temporarily disabled while its request is being processed.
This is helpful when a route does slow work and a visitor might
otherwise click twice.

## Adding raw content

### add_website_header

```python
add_website_header("<meta name='author' content='Ada'>")
```

Adds raw content to the site's HTML head: meta tags, script tags, or
anything else that belongs there. The text is not wrapped or escaped.

### add_website_css

```python
add_website_css("h1 { color: darkslateblue; }")
add_website_css("h1", "color: darkslateblue;")
```

Adds CSS to every page. With one argument, the text is raw CSS. With
two, the first is a selector and the second is the rule body to wrap
in braces. The how-to, including the selectors you need, is
[Custom CSS](../add/change-appearance/custom-css.md).

## Site information

### set_site_information

```python
set_site_information(
    "Ada Lovelace",
    "An app for tracking my corgi's snacks.",
    "Icons from openmoji.org",
    "See planning.pdf in the repository.",
    ["https://github.com/ada/snack-tracker"]
)
```

Records who made the site and how, shown on the site's built-in
`--about` page.
All five arguments are required, in order: `author`, `description`,
`sources`, `planning`, and `links` (a list). Use empty strings, or an
empty list for `links`, for anything that does not apply. Deployment
expects this to be filled in; see
[Prepare for release](../your-project/deploy/prepare.md).

### get_site_information

```python
get_site_information()
```

Returns the information previously set, mostly useful for checking it
in tests.

## Debugging and release

### hide_debug_information

```python
hide_debug_information()
```

Turns off the debug panel. This is the standard step before
[deploying](../your-project/deploy/prepare.md), so visitors see your
app rather than your debugger.

### show_debug_information

```python
show_debug_information()
```

Turns the debug panel back on. The panel is on by default during
development.

### set_error_page

```python
set_error_page("Oh no!", "Something broke. Try the home page.", False)
```

Customizes the built-in error page. The three arguments set the
heading, the friendly message shown to visitors, and whether technical
details (the error message and traceback) are shown. Deployed sites
often pass `False` so visitors never see a traceback.

### deploy_site

```python
deploy_site()
```

Prepares the site for deployment. Currently it turns off debug
information, the same as `hide_debug_information()`; the
`image_folder` argument is accepted for compatibility but not yet
used.

## Related

- [start_server](start-server.md): several of these settings also
  exist as keyword arguments there; the functions above are the
  clearer form.
- [Change the appearance](../add/change-appearance/index.md): the
  styling tiers, presented as how-to guides.
- [Prepare for release](../your-project/deploy/prepare.md): which of
  these to call before you deploy.
