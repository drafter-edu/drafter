---
page_type: reference
title: Command line
level: L3
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Know the student-relevant command-line flags.
---

# Command line

Running your file with Python (`python my_app.py`, or the Run
button in your editor) is the normal way to work, and most
projects never need more. The `drafter` command exists for the
occasions you want to change how the app is served or built.
`python -m drafter` is the same command spelled differently, and
`drafter --help` prints the complete live list; this page keeps
to the flags students actually reach for.

## Running

```console
drafter my_app.py
```

Starts the development server, opens your browser, and reloads
the app whenever you save the file.

| Flag | Default | What it does |
| ---- | ------- | ------------ |
| `--port PORT` | `8000` | Serve on a different port, for when 8000 is taken by another program (or a classmate's app on a shared machine). |
| `--host HOST` | `localhost` | Serve to other devices: `--host 0.0.0.0` lets your phone on the same network open the app. |
| `--no-open-browser` | opens | Do not open a browser tab automatically. |
| `--no-reloader` | on | Stop watching your files for changes. |
| `--skip` | off | Do not start the server or compile anything: `start_server(...)` returns immediately. Lets a test runner import the file without launching the site. |

Drafter normally watches your program's whole folder so that saving
any project file reloads the site, and falls back to watching only
your program and the files your site uses when the folder is large or
broad (like Downloads). The [live reload](live-reload.md) page covers
that behavior and its flags, such as `--watch-path`,
`--ignore-watch-path`, and `--watch-manifest`.

Setting the `DRAFTER_SKIP` environment variable does the same thing
as `--skip`, which is handy when the command being run is not
`drafter` itself; for example, a unit test runner such as `pytest`
importing your file.

## Appearance and production

| Flag | Default | What it does |
| ---- | ------- | ------------ |
| `--theme NAME` | `default` | Start with a theme, same as `set_website_style(...)` in code. The code version wins if both are used; the [theme catalog](themes.md) shows the choices. |
| `--no-frame` | framed | Remove the browser-window frame around the app, same as `set_website_framed(False)`. |
| `--production` | off | Run without the debug panel, the way visitors will see the deployed site. Worth one look before deploying. |

## Building for deployment

```console
drafter my_app.py --compile
```

Compiles the app into static files (in `dist/` by default) ready
for GitHub Pages; the
[deploy guide](../your-project/deploy/index.md) walks the whole
journey.

| Flag | Default | What it does |
| ---- | ------- | ------------ |
| `--output-directory DIR` | `dist` | Build somewhere else. |
| `--additional-paths PATH` | none | Bundle an extra file your code `open()`s; repeat the flag for each file: `--additional-paths pets.csv --additional-paths words.txt`. Forgetting this is the classic works-locally, [404s-deployed](../help/errors/missing-asset-on-deploy.md) mistake. The in-code form is [`add_website_file`](site-config.md#add_website_file). |
| `--additional-files PATH` | none | Same idea as `--additional-paths`, but through the site configuration: the flag version of `add_website_file(...)`. Repeat once per file. |
| `--additional-css-files PATH_OR_URL` | none | Link a stylesheet (a `.css` file next to your program, or a URL) into every page; the flag version of `add_website_css_file(...)`. Repeat once per entry. |
| `--additional-js-files PATH_OR_URL` | none | Load a script (a `.js` file next to your program, or a URL) on every page; the flag version of `add_website_js_file(...)`. Repeat once per entry. |
| `--zip-output` | off | Zip the built site, convenient for uploading. |

## Libraries

| Flag | Default | What it does |
| ---- | ------- | ------------ |
| `--project-packages PKG` | none | Name a third-party package your app needs when automatic detection misses it; repeat the flag for each package. [Third-party libraries](../extend/packages.md) explains when. |

## Related

- The full flag reference, including development and internal
  options, lives in the repository README; contributors should
  start at the [developer docs](../dev/index.md).
- Most of what these flags do is also available in code through
  [site configuration](site-config.md), which travels with your
  file and is usually the better home.
