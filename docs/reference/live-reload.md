---
page_type: reference
title: Live reload
level: L3
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Know what Drafter watches for changes and how to control it.
---

# Live reload

While the development server runs, Drafter watches your files. Save a
change and the site restarts on its own; there is no need to stop the
program and run it again. This page explains exactly what gets watched
and every setting that controls it. Most projects never need any of
this: keep your program and its files in their own small folder and
the defaults do the right thing.

## What Drafter watches

When you run `python my_app.py` (or `drafter my_app.py`), Drafter:

1. Always watches your main Python file.
2. Watches the rest of the file's folder, including subfolders, so
   that editing a helper module, an image, or a data file also
   reloads the site.

Before watching the whole folder, Drafter checks that the folder is
actually a project folder and not something enormous. The folder is
considered too broad when:

- it is a filesystem root (like `C:\` or `/`),
- it is your home directory,
- it is a known broad location such as Desktop, Documents, or
  Downloads, or
- it holds more files, folders, or nesting levels than the configured
  limits (1000 files, 200 folders, 20 levels deep by default).

## Safe mode

If any of those checks fails, Drafter switches to a safe mode and
prints:

```text
Drafter noticed that my_app.py is in a large or broad folder.
For safety, live reload will watch your program and files used by
your site rather than the entire folder.
```

In safe mode, Drafter still watches:

- your main Python file,
- any files you configured explicitly (see below), and
- files your site actually uses: when the server serves `helpers.py`
  or `images/cat.png`, that file joins the watch set from then on.

The site keeps working; the only difference is that a file the site
has never loaded will not trigger a reload when you edit it. The
simplest fix is to move your program into its own folder, for
example `lab3/`, and run it from there.

Files that Drafter generates itself, such as `drafter-debug.log`,
never trigger a reload in any mode.

## Settings

Each setting below can be passed as a keyword to `start_server(...)`,
set in a JSON configuration file (passed with `--config-file`) under
the `app_server` section, or set through an environment variable with
the `DRAFTER_` prefix (for example `DRAFTER_WATCH_MAX_FILES=500`).
The boolean switches also have `--no-...` command-line flags.

| Setting | Default | What it does |
| ------- | ------- | ------------ |
| `use_reloader` | `True` | Master switch. `False` turns file watching off entirely. |
| `watch_adjacent_files` | `True` | `False` watches only the main file and explicitly configured paths, with no automatic folder watching at all. |
| `watch_recursively` | `True` | `False` skips the folder watch and goes straight to safe mode, without printing the notice. |
| `watch_safe_mode` | `True` | `False` skips the safety checks and always watches the folder. For controlled environments like lab machines. |
| `watch_served_files` | `True` | `False` stops safe mode from adding served files to the watch set. |
| `watch_max_files` | `1000` | Safety limit on files in the folder. `None` removes the limit. |
| `watch_max_directories` | `200` | Safety limit on subfolders. `None` removes the limit. |
| `watch_max_depth` | `20` | Safety limit on folder nesting. `None` removes the limit. |
| `watch_broad_locations` | `False` | `True` allows watching Desktop, Documents, and similar folders. Home directories and filesystem roots are still refused. |
| `watch_paths` | `[]` | Files, folders, or glob patterns to always watch, relative to your program's folder. |
| `ignore_watch_paths` | `[]` | Files, folders, or glob patterns whose changes never trigger a reload. |
| `watch_manifest` | `None` | Path to a JSON manifest listing the project's files; see below. |
| `watch_force_recursive` | `False` | `True` watches the folder even when a safety check would refuse it. Use with care. |

For example, to watch a data folder that lives outside the project
and ignore a log file your program writes:

```python
start_server(State(),
             watch_paths=["../shared-data/"],
             ignore_watch_paths=["notes.log"])
```

## The watch manifest

Larger projects can describe their files in a small JSON file and
point Drafter at it with `watch_manifest="drafter-files.json"`. The
simplest form is a list of entries:

```json
[
    "helpers.py",
    "data/*.csv",
    "images/"
]
```

A folder entry such as `images/` is included with all of its
contents; a glob such as `data/*.csv` covers a set of related files.
The longer form separates watched paths from ignored ones:

```json
{
    "watch_paths": ["helpers.py", "data/*.csv", "images/"],
    "ignore_watch_paths": ["output/", "*.log"]
}
```

Relative entries are resolved from the folder the manifest file is
in. Manifest entries are always watched, in both normal and safe
mode. In `ignore_watch_paths`, an entry ending in `/` ignores that
whole folder, and other entries match either the file name or the
path relative to your program's folder.

## Turning it off

Pass `use_reloader=False` to `start_server`, or run with
`drafter my_app.py --no-reloader`. The server still runs; it simply
never restarts the site on its own, and you refresh manually after
stopping and rerunning the program.

## Related

- [Command line](cli.md): the flags for these settings.
- [start_server](start-server.md): all the other server options.
- [My changes are not appearing](../help/troubleshooting.md#my-changes-are-not-appearing):
  the save-and-reload checklist.
