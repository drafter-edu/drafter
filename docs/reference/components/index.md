---
page_type: reference
title: All components
audience: S
priority: P0
prereqs: []
symbols: []
outcome: See every component, organized coherently.
---

# All components

Components are the things you put in a page's content list. This is
every one of them, grouped by purpose. Within each group, the
components you are most likely to need come first.

Strings are not on this list, but remember that they are the most
common page content of all: any string in a content list renders as
text.

## If you want to...

| You want to | Reach for |
| ----------- | --------- |
| Let the visitor do something | [Button](actions/button.md) |
| Let the visitor go somewhere | [Link](actions/link.md) |
| Ask for text or a number | [TextBox](input/textbox.md), [TextArea](input/textarea.md) |
| Ask for a choice | [CheckBox](input/checkbox.md), [SelectBox](input/selectbox.md), [RadioButtonGroup](input/radiobuttongroup.md) |
| Show a list from your state | [BulletedList](lists/bulletedlist.md), [NumberedList](lists/numberedlist.md), [Table](data/table.md) |
| Organize a page visually | [Header](text/header.md), [HorizontalRule](layout/horizontalrule.md), [Div](layout/div.md), [Row](layout/row.md) |
| Show a picture | [Image](media/image.md) |
| Move files in or out | [FileUpload](input/fileupload.md), [Download](input/download.md) |

## Actions

Clickable controls that run a route.

| Component | One line |
| --------- | -------- |
| [Button](actions/button.md) | Trigger a route, optionally passing Arguments. |
| [Link](actions/link.md) | Navigate by text link, including external URLs. |
| [Argument](actions/argument.md) | Pass extra values to a route. |

## Input

Form fields. Each one's `name` becomes a parameter of the route its
button submits to; see
[Forms and input](../../concepts/forms-and-input.md).

| Component | One line |
| --------- | -------- |
| [TextBox](input/textbox.md) | Collect a line of text or a number. |
| [TextArea](input/textarea.md) | Collect multi-line text. |
| [CheckBox](input/checkbox.md) | Collect a yes/no. |
| [SelectBox](input/selectbox.md) | Choose one option from a list. |
| [RadioButtonGroup](input/radiobuttongroup.md) | Choose one option with all options visible. |
| [RelatedCheckBox](input/relatedcheckbox.md) | Choose many options, received as a list parameter. |
| [DateInput](input/dateinput.md) | Collect a date. |
| [TimeInput](input/timeinput.md) | Collect a time. |
| [DateTimeInput](input/datetimeinput.md) | Collect a date and time. |
| [Label](input/label.md) | Caption an input accessibly. |
| [Output](input/output.md) | Show a computed result region. |
| [FileUpload](input/fileupload.md) | Receive a file from the user. |
| [Download](input/download.md) | Let the user save a file. |

## Text

Words, from headings to quotations.

| Component | One line |
| --------- | -------- |
| [Header](text/header.md) | Add section headings, levels 1-6. |
| [Text](text/text.md) | Use the explicit text component. |
| [Paragraph](text/paragraph.md) | Use real paragraphs instead of strings. |
| [PreformattedText](text/pre.md) | Preserve spacing and newlines. |
| [InlineCode](text/inlinecode.md) | Mark code in text. |
| [BlockQuote](text/blockquote.md) | Quote a passage. |
| [Inline text semantics](text/inline-styles.md) | Strong, Emphasis, MarkedText, and the other inline markers, on one page. |

## Layout

Structure and spacing.

| Component | One line |
| --------- | -------- |
| [LineBreak](layout/linebreak.md) | Force a new line. |
| [HorizontalRule](layout/horizontalrule.md) | Add a divider line. |
| [Div (Box)](layout/div.md) | Group content for styling. |
| [Span](layout/span.md) | Group content inline. |
| [Row](layout/row.md) | Lay content out side by side. |
| [Details](layout/details.md) | Make collapsible sections and accordions. |
| [Page regions](layout/page-regions.md) | Section, Article, Nav, and the other semantic regions, on one page. |

## Lists

| Component | One line |
| --------- | -------- |
| [BulletedList](lists/bulletedlist.md) | Show an unordered list from a Python list. |
| [NumberedList](lists/numberedlist.md) | Show an ordered list. |
| [DefinitionList](lists/definitionlist.md) | Show term/definition pairs, including from dataclasses. |

## Data display

| Component | One line |
| --------- | -------- |
| [Table](data/table.md) | Show rows of lists or dataclasses. |
| [ProgressBar](data/progressbar.md) | Show progress. |
| [Meter](data/meter.md) | Show a gauge value. |
| [TimeOutput](data/timeoutput.md) | Show semantic timestamps. |

## Media

| Component | One line |
| --------- | -------- |
| [Image](media/image.md) | Show images from a URL, file, Picture, or bytes. |
| [MatPlotLibPlot](media/matplotlibplot.md) | Show a matplotlib figure. |
| [Audio](media/audio.md) | Play sound files, including across pages. |
| [Video](media/video.md) | Play video files. |
| [SVG](media/svg.md) | Show inline vector graphics. |
| [Canvas](media/canvas.md) | Draw on a canvas surface (with JavaScript). |
| [RawHTML and HtmlTag](media/rawhtml.md) | Use the escape hatch to raw HTML safely. |

## Time

Components that trigger actions on a schedule.

| Component | One line |
| --------- | -------- |
| [Timer](time/timer.md) | Run a countdown that fires a route. |
| [Clock](time/clock.md) | Run a repeating tick route. |
| [RemovePersistent](time/removepersistent.md) | Evict a persistent component. |

## Place

| Component | One line |
| --------- | -------- |
| [Map](place/map.md) | Show an interactive map with markers. |
| [CurrentLocation](place/currentlocation.md) | Ask for the user's location. |

## Capture

| Component | One line |
| --------- | -------- |
| [Camera](capture/camera.md) | Take a photo into the app. |

## Sound

| Component | One line |
| --------- | -------- |
| [Tone](sound/tone.md) | Play a single note. |
| [Melody](sound/melody.md) | Play a note sequence. |
| [Sound](sound/sound.md) | Play files through effects. |
| [Microphone](sound/microphone.md) | React to sound levels. |
| [AudioRecorder](sound/audiorecorder.md) | Record audio clips. |
| [Audio effects](sound/effects.md) | Echo, Reverb, and the other effects, on one page. |

## Related

- [Keywords every component accepts](../keyword-attributes.md):
  `style_*`, `classes`, `id`, and events work on all of these.
- [Styling functions](../styling-functions.md): wrap any component to
  restyle it.
- [Add to Your App](../../add/index.md): task pages that show how
  these components are used in complete applications.
