# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

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