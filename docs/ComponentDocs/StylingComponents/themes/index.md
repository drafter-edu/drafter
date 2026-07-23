# Themes

Drafter themes change the overall look of your page. This page shows the same simple layout in several different themes so you can see how a header, some text, and a button look together.

## Common Theme Names

- `skeleton`
- `mvp`
- `sakura`
- `simple`
- `tacit`
- `98`
- `XP`
- `7`
- `bootstrap`
- `none`

## Examples

### Example 1: skeleton

```python drafter
from drafter import *

set_website_style("skeleton")

@route
def index():
	return Page([
		Header("Skeleton Theme", 2),
		"This page uses the default skeleton theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 2: mvp

```python drafter
from drafter import *

set_website_style("mvp")

@route
def index():
	return Page([
		Header("MVP Theme", 2),
		"This page uses the MVP theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 3: sakura

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

### Example 4: simple

```python drafter
from drafter import *

set_website_style("simple")

@route
def index():
	return Page([
		Header("Simple Theme", 2),
		"This page uses the Simple theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 5: tacit

```python drafter
from drafter import *

set_website_style("tacit")

@route
def index():
	return Page([
		Header("Tacit Theme", 2),
		"This page uses the Tacit theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 6: 98

```python drafter
from drafter import *

set_website_style("98")

@route
def index():
	return Page([
		Header("98 Theme", 2),
		"This page uses the 98 theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 7: XP

```python drafter
from drafter import *

set_website_style("XP")

@route
def index():
	return Page([
		Header("XP Theme", 2),
		"This page uses the XP theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 8: 7

```python drafter
from drafter import *

set_website_style("7")

@route
def index():
	return Page([
		Header("7 Theme", 2),
		"This page uses the 7 theme.",
		Button("Try It", index)
	])

start_server()
```

### Example 9: bootstrap

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

### Example 10: none

```python drafter
from drafter import *

set_website_style("none")

@route
def index():
	return Page([
		Header("No Theme", 2),
		"This page disables the default theme.",
		Button("Try It", index)
	])

start_server()
```

When you want full control over the styling, use `none` and add your own CSS.
