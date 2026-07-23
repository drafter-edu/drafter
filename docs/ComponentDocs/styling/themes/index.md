# Themes

Themes change the overall look of a page. Use `set_website_style` to switch between built-in theme presets.

## Syntax

```python
set_website_style(style)
```

## Themes

### `skeleton`

```python drafter
from drafter import *

set_website_style("skeleton")

@route
def index():
	return Page([
		Header("Skeleton Theme", 2),
		"This is the default theme.",
		Button("Try It", index)
	])


start_server()
```

### `sakura`

```python drafter
from drafter import *

set_website_style("sakura")

@route
def index():
	return Page([
		Header("Sakura Theme", 2),
		"This page uses the Sakura theme.",
		Button("Try It", index)
	])


start_server()
```

### `bootstrap`

```python drafter
from drafter import *

set_website_style("bootstrap")

@route
def index():
	return Page([
		Header("Bootstrap Theme", 2),
		"This page uses the Bootstrap theme.",
		Button("Try It", index)
	])


start_server()
```

Use these themes when you want a ready-made visual style instead of building one from scratch.
