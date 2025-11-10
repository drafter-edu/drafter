# Styling System Changes

## Overview

This document describes the changes made to the Drafter styling system to make it easier for students to override default styles with their own CSS.

## Problem

Previously, Drafter used high-specificity ID selectors for styling, such as:
```css
#drafter-root-- #drafter-body-- {
    background-color: white;
    /* ... */
}
```

This made it very difficult for students to override styles because:
1. ID selectors have high specificity (200 points)
2. Nested ID selectors have even higher specificity (400 points)
3. Students would need to use `!important` or equally specific selectors to override

## Solution

We've refactored the CSS to use class selectors instead:

### HTML Structure Changes

Added class attributes to all Drafter structural elements:
```html
<div id="drafter-site" class="drafter-site">
  <form id="drafter-form" class="drafter-form">
    <div id="drafter-frame" class="drafter-frame">
      <div id="drafter-header" class="drafter-header"></div>
      <div id="drafter-body" class="drafter-body">
        <!-- Content here -->
      </div>
      <div id="drafter-footer" class="drafter-footer"></div>
    </div>
  </form>
</div>
```

- IDs are kept for JavaScript targeting and backwards compatibility
- Classes are added for styling purposes

### CSS Specificity Changes

Changed from:
```css
#drafter-root-- {
    #drafter-body-- {
        background-color: white;
    }
}
```

To:
```css
.drafter-body {
    background-color: white;
}
```

Specificity comparison:
- Old: `#drafter-root-- #drafter-body--` = 200 points (ID) × 2 = **400 points**
- New: `.drafter-body` = 10 points (class) = **10 points**
- Student CSS: `body { ... }` or `.my-class { ... }` = 1-10 points

This allows students to easily override with simple selectors!

### Removed !important Flags

Removed `!important` flags from CSS rules, allowing natural CSS cascade to work:

```css
/* Old - hard to override */
h1 {
    font-size: 4rem !important;
}

/* New - easy to override */
.drafter-body h1 {
    font-size: 4rem;
}
```

## New Themes

Ported 7 themes from the `libs/` directory and created 2 new themes for the new theme system:

1. **mvp** - MVP.css minimal theme
2. **sakura** - Sakura classless theme
3. **tacit** - Tacit classless theme
4. **skeleton** - Skeleton responsive framework
5. **7** - Windows 7 retro theme
6. **98** - Windows 98 retro theme
7. **XP** - Windows XP retro theme
8. **dark-mode** - Modern dark theme with good contrast and accessibility
9. **water** - Classless CSS theme inspired by water.css principles

### Using Themes

```python
from drafter import *

# Set a theme
set_website_style("mvp")

# Or use none for no default styling
set_website_style("none")
```

### Available Themes

- `default` - Default Drafter theme
- `none` - No theme (blank slate)
- `mvp` - MVP.css minimal theme
- `sakura` - Sakura classless theme
- `tacit` - Tacit classless theme
- `skeleton` - Skeleton responsive framework
- `7` - Windows 7 retro theme
- `98` - Windows 98 retro theme
- `XP` - Windows XP retro theme
- `dark-mode` - Modern dark theme with excellent contrast
- `water` - Clean, classless theme inspired by water.css

## Student CSS Override Examples

Students can now easily override styles:

```python
from drafter import *

# Override body styles
add_website_css("""
body {
    background-color: lightblue;
    font-size: 20px;
}

h1 {
    color: darkblue;
    font-size: 3rem;
}

button {
    background-color: green;
    color: white;
    padding: 10px 20px;
}
""")
```

## File Locations

- **CSS Source Files**: `js/src/css/`
  - `default.css` - Default theme
  - `drafter_base.css` - Base Drafter styles
  - `drafter_debug.css` - Debug mode styles
  - `drafter_deploy.css` - Production mode styles
  - `themes/` - Theme CSS files

- **Built CSS Files**: `src/drafter/assets/js/css/`
  - Automatically built from source files
  - Includes minified versions and source maps

- **Theme Registration**: `src/drafter/styling/themes.py`
  - Theme definitions and registration

- **Site Structure**: `src/drafter/site/site.py`
  - HTML template with class attributes

## Build Process

Themes are automatically included in the build:

```bash
cd js
npm run build
```

The `tsup.config.ts` automatically discovers and builds all CSS files in:
- `js/src/css/*.css`
- `js/src/css/themes/*.css`

## Testing

New test suite in `tests/test_styling.py` verifies:
- All themes are registered
- Theme CSS files exist
- CSS uses class selectors (not high-specificity IDs)
- HTML structure includes class attributes
- Invalid themes raise appropriate errors

Run tests with:
```bash
pytest tests/test_styling.py
```

## Backwards Compatibility

- **IDs preserved**: All element IDs remain unchanged for JavaScript compatibility
- **Class additions**: New classes added don't break existing code
- **Theme API unchanged**: `set_website_style()` works the same way
- **Existing CSS**: Student CSS that worked before will still work

## Migration Guide

For theme authors:

1. **Don't use nested ID selectors**: Use class selectors instead
2. **Avoid !important**: Let CSS cascade work naturally
3. **Keep specificity low**: Use single class selectors when possible
4. **Target .drafter-body descendants**: For content area styling

Example:
```css
/* Good - low specificity */
.drafter-body p {
    line-height: 1.6;
}

/* Bad - high specificity */
#drafter-body-- p {
    line-height: 1.6 !important;
}
```
