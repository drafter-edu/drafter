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
| `--no-reloader` | on | Stop watching the file for changes. |

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
| `--additional-paths LIST` | none | Bundle extra files your code `open()`s, separated by semicolons: `--additional-paths "pets.csv;words.txt"`. Forgetting this is the classic works-locally, [404s-deployed](../help/errors/missing-asset-on-deploy.md) mistake. |
| `--zip-output` | off | Zip the built site, convenient for uploading. |

## Libraries

| Flag | Default | What it does |
| ---- | ------- | ------------ |
| `--project-packages LIST` | none | Name third-party packages your app needs when automatic detection misses them, separated by semicolons. [Third-party libraries](../extend/packages.md) explains when. |

## Related

- The full flag reference, including development and internal
  options, lives in the repository README; contributors should
  start at the [developer docs](../dev/index.md).
- Most of what these flags do is also available in code through
  [site configuration](site-config.md), which travels with your
  file and is usually the better home.
