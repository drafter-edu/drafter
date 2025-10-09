# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.5] - 2025-10-09

* Fixed issue where multiple external pages were not being handled correctly on command line

## [1.8.4] - 2025-10-09

* Fixed issue in the page navigation for Skulpt deployments

## [1.8.3] - 2025-10-09

* Skulpt deployments now use Sk.bottle.changeLocation instead of window.location.

## [1.8.2] - 2025-10-09

* 404 redirects were not being processed
* Deployed version should now register the CTRl+I shortcut for the about page.

## [1.8.1] - 2025-10-08

* Minor issue with command line deployment fixed (drafter not runnable as a tool)

## [1.8.0] - 2025-10-06

* Command line compilation of websites
* Deploying through skulpt, the setup code stored in Drafter now
* Script tags are properly escaped when the test deployment is launched.
* About page now shows information using the `set_site_information` function
* Command line flag for passing in external URLs

## [1.7.4] - 2025-08-08

### Added

* Can now pass a single string into `Page`, and it will wrap it in a list automatically.

## [1.7.3] - 2025-04-22

### Fixed

* `Text` components now correctly handle keyword arguments. They also are able to be compared to string literals (one direction only), should be rendered better in tests.

## [1.7.2] - 2025-04-17

### Fixed

* Div, Span, Pre, and Row components now properly handle both explicit keyword arguments and *args

## [1.7.1] - 2025-02-20

### Fixed

* Temporarily disabled the gzip/base64 aspects of theme loading, for Skulpt compatibility

## [1.7.0] - 2025-02-20

### Added

* There are now a bunch more themes available (`sakura`, `tacit`, `XP`, and more).
* The deployment URLs for Skulpt and its associated files can now be overridden
* 
### Fixed

* Deployed sites were not correctly escaping HTML entities for generated tests
* Fixed an issue where the configuration parameters were not being accepted via start_server
* Slightly better error message when the Bakery library is not found, and assert_equal is used
* Theme architecture is more flexible and dynamically based off `libs/manifest.json`


## [1.6.2] - 2024-12-09

### Fixed

* The options for a `SelectBox` are forced into strings, before they are escaped.

## [1.6.1] - 2024-12-08

### Fixed

* Using utcnow() instead of now() (credit to @crsommers)
* Refactored `Div` and `Span` slightly (credit to @crsommers)
* Fixed issue with escaping of tags in `VisitedPage`
* Fixed issue with dropdowns not properly escaping the option
* Fixed issue with non-button related values being passed incorrectly

## [1.6.0] - 2024-12-02

### Added

* Can now test deployments with the `deploy` button, which will open a new tab with the deployed site using Skulpt
* Configuration information is now shown on the debug page at the bottom, along with the deploy button.
* Components that have names will now validate the name to ensure it is a valid Python variable name, and show an error.
* Slightly more information is shown on the error page when parameter conversion fails.

### Fixed

* MatPlotLibPlot now has correct fields
* Arguments for Buttons can now have non-html-safe characters

## [1.5.7] - 2024-11-24

### Fixed

* Circular references in the State now throw an error, instead of just causing an infinite loop.
* Fixed a bug with the `safe_repr` function incorrectly marking objects that show up multiple times as circular, even if they are in sibling structures.

## [1.5.6] - 2024-11-15

### Fixed

* Fixed a few components (`MatPlotLibPlot`, `FileUpload`, and `Text`) not rendering correctly in test cases due to not being dataclasses.
* Fixed an issue with an incorrect import (glob) appearing somehow
* Fixed an issue where `memoryview` was being serialized in the `safe_repr` function

## [1.5.5] - 2024-11-12

### Fixed

* Fixed an error with `Argument` values that had quotes, not being escaped properly. Thanks new unit tests!

## [1.5.4] - 2024-11-12

### Added

* The `set_website_style` now accepts `None` in addition to `"none"` to remove the style
* Provide `get_main_server` and `set_main_server` functions to manipulate the global server (mostly for testing purposes).

### Fixed

* Improved documentation for styling features

## [1.5.3] - 2024-11-7

### Added

* The `add_website_css` function now allows a single string (just the CSS) instead of the selector/CSS pair

## [1.5.2] - 2024-10-29

### Fixed

* Force text boxes, text areas, and other input components to `str` their default value (when provided) and escape it for html

## [1.5.1] - 2024-10-29

### Fixed

* Fixed other input components' values not being properly escaped
* Fixed a bug with `Span` and `Div` components not properly being `repr`ed

## [1.5.0] - 2024-10-24

### Added

* Provide `Picture` class to prevent name collisions with `Image` class and `Pillow` module
* Provide `new` and `open` methods in `Image` that shadow the `Pillow` module's versions.
* Provide `UploadedFile` class to represent uploaded files in unit tests and the State.

### Fixed

* Fixed a bug with `Button`s not properly escaping data (including unicode emojis).

## [1.4.2] - 2024-10-15

### Fixed

* Added a `hacks.py` module to make the `MatPlotLibPlot` component work in Skulpt

## [1.4.1] - 2024-10-10

### Added

* Improved output for very long strings of text, allowing them to be collapsed

## [1.4.0] - 2024-09-14

### Added

* Added a "reset" button in the topright corner to reset the state and clear out the old history
* Can now have Pillow images in State
* Proper file handling support; this changes buttons to now POST requests instead
* Added `Row` component, `Pre`/`PreformattedText` components

### Fixed

* When outputing the current state, properly escape angle brackets
* You can now add styles and attributes to `Div` and `Span` components

## [1.3.1] - 2024-08-05

### Added

* The `Image` component now supports PIL images
* The `Download` component also supports PIL images being provided as the `contents`

### Fixed

* Now passing Mypy checks (although we had to silence Bakery and Bottle)

## [1.3.0] - 2024-08-05

### Added

* New `Download` component to allow for downloading user generated files.

## [1.2.2] - 2024-07-27

### Added

* Declared the package as providing types

## [1.2.1] - 2024-07-14

### Added

* Added a `MatPlotLibPlot` component to display MatPlotLib plots in the browser

## [1.2.0] - 2024-05-05

### Fixed

* Images can now deploy correctly through the CDN

## [1.1.4] - 2024-05-03

### Fixed

* Made error lines much more intelligent

## [1.1.3] - 2024-05-03

### Fixed

* Corrected error line stack trace depth

## [1.1.2] - 2024-05-03

### Added

* You can now run a drafter site from the command line without starting the server (e.g., for just the tests) by setting the DRAFTER_SKIP environment variable

## [1.1.0] - 2024-04-26

### Fixed

* The library has been broken up into multiple files for easier maintenance
* Fixed a bug with `Argument` not handling spaces correctly, or other non-String types

### Added

* Improved deployment options, including optional styles and header
* Allowed frame and title to be configurable
* Create DRAFTER_SKULPT os environment variable

## [1.0.6] - 2024-04-04

### Fixed

* Added copyable button to the combined tests, prevent them from spilling over

## [1.0.5] - 2024-04-01

### Fixed

* Fixed Argument instances with spaces
* Changed button label separator to be more unusual
* Fixed bug with additional Arguments being kept for all buttons

### Added

* Span component to allow for a row of things

## [1.0.4] - 2024-03-30

### Fixed

* Added button to copy all (unique) tests at once

### Removed

* Broke external URLs, will fix in future release!

## [1.0.3] - 2024-03-29

### Fixed

* Local images should now render correctly
* Route tests now show the correct parameter order based on the function call they map to

## [1.0.2] - 2024-03-26

### Fixed

* Fixed emojis not rendering correctly in the history

## [1.0.0] - 2024-03-26

### Added

* Tests are now displayed graphically in the debug information
* Page history is now shown as test cases, can easily copy them to clipboard
* Improved error messages for incorrect types in page content
* Buttons can now take Arguments, and Arguments can be embedded as hidden inputs.

## [0.2.0] - 2023-09-22

### Added

- Current route is displayed in debug information
- Converted parameters are now revealed in current state
- Allow `classes` keyword parameter
- Provide basic styling functions like `float_right` and `bold`

### Fixed

- Reordered the debug information to put current info at top
- Error pages now give a little more information

## [0.1.4] - 2023-09-15

### Added

- Show produced Python pprint of Page in the Debug Information
- Finish quickstart, rough outline of student docs
- Show Header on top of "window" of website

## [0.1.3] - 2023-09-13

### Fixed

- Feels weird to call it fixed, but the message now says "Drafter server starting up"
- Allow an empty `start_server` with no routes

### Added

- Improve PageContent classes to support keyword parameters like `style_*` to change style

## [0.1.2] - 2023-09-12

### Fixed

- SelectBox now has a new line afterwards
- Fixed support for list state

### Added

- hide_debug_information() and show_debug_information() to control the debug information (defaults to visible)

## [0.1.1] - 2023-09-12

### Fixed

- Fix support for primitive state

## [0.1.0] - 2023-09-12

### Added

- New components: TextBox, SelectBox, CheckBox, TextArea
- Debug data at bottom of page
- Ability to restore state from links

## [0.0.2] - 2023-08-30

### Fixed

- Restructured the entire project as a Git org and repo, uploaded to Pypi

## [0.0.1] - 2023-08-24

### Added

- Initial version with Bottle support, basic link and image components, and routing