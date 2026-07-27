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
every one of them, grouped by purpose. Levels tell you when you are
likely to need one: **L2** components appear in almost every app,
**L3** in many, and **L4** in specialized projects.

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

Clickable things that run a route.

| Component | Level | One line |
| --------- | ----- | -------- |
| [Button](actions/button.md) | L2 | Trigger a route, optionally passing Arguments. |
| [Link](actions/link.md) | L2 | Navigate by text link, including external URLs. |
| [Argument](actions/argument.md) | L3 | Pass extra values to a route. |

## Input

Form fields. Each one's `name` becomes a parameter of the route its
button submits to; see
[Forms and input](../../concepts/forms-and-input.md).

| Component | Level | One line |
| --------- | ----- | -------- |
| [TextBox](input/textbox.md) | L2 | Collect a line of text or a number. |
| [TextArea](input/textarea.md) | L2 | Collect multi-line text. |
| [CheckBox](input/checkbox.md) | L2 | Collect a yes/no. |
| [SelectBox](input/selectbox.md) | L3 | Choose one option from a list. |
| [RadioButtonGroup](input/radiobuttongroup.md) | L3 | Choose one option with all options visible. |
| [RelatedCheckBox](input/relatedcheckbox.md) | L3 | Choose many options, received as a list parameter. |
| [DateInput](input/dateinput.md) | L3 | Collect a date. |
| [TimeInput](input/timeinput.md) | L3 | Collect a time. |
| [DateTimeInput](input/datetimeinput.md) | L3 | Collect a date and time. |
| [Label](input/label.md) | L3 | Caption an input accessibly. |
| [Output](input/output.md) | L3 | Show a computed result region. |
| [FileUpload](input/fileupload.md) | L3 | Receive a file from the user. |
| [Download](input/download.md) | L3 | Let the user save a file. |

## Text

Words, from headings to quotations.

| Component | Level | One line |
| --------- | ----- | -------- |
| [Header](text/header.md) | L2 | Add section headings, levels 1-6. |
| [Text](text/text.md) | L2 | Use the explicit text component. |
| [Paragraph](text/paragraph.md) | L3 | Use real paragraphs instead of strings. |
| [PreformattedText](text/pre.md) | L3 | Preserve spacing and newlines. |
| [InlineCode](text/inlinecode.md) | L3 | Mark code in text. |
| [BlockQuote](text/blockquote.md) | L3 | Quote a passage. |
| [Inline text semantics](text/inline-styles.md) | L3 | Strong, Emphasis, MarkedText, and the other inline markers, on one page. |

## Layout

Structure and spacing.

| Component | Level | One line |
| --------- | ----- | -------- |
| [LineBreak](layout/linebreak.md) | L2 | Force a new line. |
| [HorizontalRule](layout/horizontalrule.md) | L2 | Add a divider line. |
| [Div (Box)](layout/div.md) | L3 | Group content for styling. |
| [Span](layout/span.md) | L3 | Group content inline. |
| [Row](layout/row.md) | L3 | Lay content out side by side. |
| [Details](layout/details.md) | L3 | Make collapsible sections and accordions. |
| [Page regions](layout/page-regions.md) | L4 | Section, Article, Nav, and the other semantic regions, on one page. |

## Lists

| Component | Level | One line |
| --------- | ----- | -------- |
| [BulletedList](lists/bulletedlist.md) | L2 | Show an unordered list from a Python list. |
| [NumberedList](lists/numberedlist.md) | L2 | Show an ordered list. |
| [DefinitionList](lists/definitionlist.md) | L3 | Show term/definition pairs, including from dataclasses. |

## Data display

| Component | Level | One line |
| --------- | ----- | -------- |
| [Table](data/table.md) | L3 | Show rows of lists or dataclasses. |
| [ProgressBar](data/progressbar.md) | L3 | Show progress. |
| [Meter](data/meter.md) | L3 | Show a gauge value. |
| [TimeOutput](data/timeoutput.md) | L4 | Show semantic timestamps. |

## Media

| Component | Level | One line |
| --------- | ----- | -------- |
| [Image](media/image.md) | L3 | Show images from a URL, file, Picture, or bytes. |
| [MatPlotLibPlot](media/matplotlibplot.md) | L4 | Show a matplotlib figure. |
| [Audio](media/audio.md) | L4 | Play sound files, including across pages. |
| [Video](media/video.md) | L4 | Play video files. |
| [SVG](media/svg.md) | L4 | Show inline vector graphics. |
| [Canvas](media/canvas.md) | L4 | Draw on a canvas surface (with JavaScript). |
| [RawHTML and HtmlTag](media/rawhtml.md) | L3 | Use the escape hatch to raw HTML safely. |

## Time

Components that make things happen on a schedule.

| Component | Level | One line |
| --------- | ----- | -------- |
| [Timer](time/timer.md) | L4 | Run a countdown that fires a route. |
| [Clock](time/clock.md) | L4 | Run a repeating tick route. |
| [RemovePersistent](time/removepersistent.md) | L4 | Evict a persistent component. |

## Place

| Component | Level | One line |
| --------- | ----- | -------- |
| [Map](place/map.md) | L4 | Show an interactive map with markers. |
| [CurrentLocation](place/currentlocation.md) | L4 | Ask for the user's location. |

## Capture

| Component | Level | One line |
| --------- | ----- | -------- |
| [Camera](capture/camera.md) | L4 | Take a photo into the app. |

## Sound

| Component | Level | One line |
| --------- | ----- | -------- |
| [Tone](sound/tone.md) | L4 | Play a single note. |
| [Melody](sound/melody.md) | L4 | Play a note sequence. |
| [Sound](sound/sound.md) | L4 | Play files through effects. |
| [Microphone](sound/microphone.md) | L4 | React to sound levels. |
| [AudioRecorder](sound/audiorecorder.md) | L4 | Record audio clips. |
| [Audio effects](sound/effects.md) | L4 | Echo, Reverb, and the other effects, on one page. |

## Related

- [Keywords every component accepts](../keyword-attributes.md):
  `style_*`, `classes`, `id`, and events work on all of these.
- [Styling functions](../styling-functions.md): wrap any component to
  restyle it.
- [Add to Your App](../../add/index.md): task pages that show these
  components doing real work.
