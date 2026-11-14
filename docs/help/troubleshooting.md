---
page_type: troubleshooting
title: Troubleshooting
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Diagnose problems by symptom.
---

# Troubleshooting

This page is organized by what you can see on the screen. If you
are looking at an error page, the [error index](errors/index.md)
is a faster place to look.

## The page is blank

A page that is completely blank usually came from a route that
returned a page with nothing in it.

- Check the content list of the page that the route returns. A route
  that ends with `return Page(state, [])` shows an empty page.
  Drafter does not treat an empty page as a mistake, so no warning
  appears.
- Check which route ran. The debug panel's Current tab names the
  route that produced the page you are looking at, and that route
  may not be the one you expected.
- A route that forgets its `return` statement does not give a blank
  page. Drafter shows an error page titled "Route Did Not Return a
  Page" instead, and
  [the entry for that error](errors/route-did-not-return-a-page.md)
  explains the fix.

## A button does nothing

- Open the debug panel's History tab and click the button again. A
  new line at the top of the list means that the route ran. Check
  what the route returned and whether it changed the state.
- If the site has only now opened, wait for the "Loading, please
  wait..." message to disappear. Buttons do not respond until the
  browser has finished starting Python.
- If the click produced an error page instead, read it. The two most
  common are a
  [missing parameter](errors/missing-parameter.md) and a
  [conversion failure](errors/type-conversion-int.md). A route that
  ends without a `return` statement produces
  [Route Did Not Return a Page](errors/route-did-not-return-a-page.md).
- Make sure the route stores its result in the state. The line
  `state.score + 1` computes a new number and never saves it. The
  line `state.score = state.score + 1` saves it.
- Make sure the page that the route returns shows the value that
  changed. If the route updates `state.score` and the page never
  displays the score, the page looks the same after every click.
  Most routes end with `return index(state)` so that the visitor
  sees the updated page.

## My changes are not appearing

While your program is running, Drafter watches your file. Each time
you save, the site in the browser reloads by itself within about a
second, and the state goes back to its starting value. You do not
need to run the program again. If a change does not show up, work
through these checks in order.

1. Check that the program is still running. If it has ended, or you
   stopped it, nothing is watching your file. Run the program again.
2. Save the file. A change that you have not saved never runs.
3. Check that you are editing the file that is running, and that you
   are looking at the browser tab that belongs to this run. When a
   program starts, the terminal prints the address of its site in a
   line such as `Drafter ready at http://localhost:8000`. A tab left
   open from an earlier run, or from another program, does not
   reload when you save. Reload that tab, and see
   [The browser shows an old or different app](#the-browser-shows-an-old-or-different-app).
4. Look for a box titled "Syntax Error" on top of your site. When
   the saved file is not valid Python, Drafter keeps showing the
   last working version of the site, and the box names the line to
   fix. Fix that line and save again.
5. If the file you changed is not your main program, check whether
   the terminal printed "Drafter noticed that ... is in a large or
   broad folder" when the program started. That message means live
   reload is in safe mode. In safe mode, Drafter reloads for your
   main program and for files the site has already used, and it
   ignores the other files in the folder. Move the project into its
   own small folder, or see
   [live reload](../reference/live-reload.md).
6. As a last resort, stop the program, run it again, and open the
   address that the terminal prints.

## Reloading the tab does not go back to the first page

After each click, the address bar ends with the name of the route
that produced the current page, such as `?route=add_one`. When you
reload the tab, Drafter starts the site again with the state at its
starting value and then runs that same route, with no form values.
Two results of this behavior can be surprising.

- If the route changes the state, the change is applied once to the
  starting state. A counter that starts at 0 and was showing 4 shows
  1 after a reload when the address ends in `?route=add_one`.
- If the route needs a value from a form, the reload has no value to
  give it. Drafter shows an error page titled "Problem With the
  Route's Arguments", which the
  [missing parameter](errors/missing-parameter.md) entry describes.

To return to the first page, click **Return to Index Page** on the
error page, or open the site's address without the `?route=...`
part.

## The browser shows an old or different app

Every running Drafter program serves its site at an address that
ends in a port number, normally `http://localhost:8000`. Only one
program can use a port at a time. Each time a program starts,
Drafter checks whether the port is free, and the terminal reports
what Drafter did.

**You ran the same file again while its earlier run was still
going.** Drafter stops the earlier run and reuses its address. The
terminal prints these two lines.

```text
An earlier run of main.py is still using port 8000. Stopping it so this run can take over...
Stopped the earlier run.
```

A browser tab that the earlier run opened does not follow the new
run. That tab keeps showing the old version of your site, and it no
longer reloads when you save. Reload that tab, or use the tab that
the new run opened.

**A different program is using the port.** Drafter moves your
program to the next free port and prints the new address. When the
other program is also a Drafter site, a second line says how to stop
it.

```text
Port 8000 is in use by another Drafter program (quiz.py), so this run will use port 8001 instead: http://localhost:8001/
To stop the other program, open http://localhost:8000/--stop-server in your browser or press Ctrl+C in its terminal.
```

A tab that is still open at `localhost:8000` keeps showing the
other program, which is how an old app ends up on the screen. Open
the address that the terminal printed for the program you want.

**You chose the port yourself, and a different program is using
it.** A port is your own choice when you pass `--port` on the
command line or `port=` to `start_server`. Drafter does not move to
another port in this case. The program stops with a message titled
"Port already in use", which says what is using the port and lists
three ways forward. You can stop the other program, choose a
different port, or remove the port setting so that Drafter can pick
a free port for you.

## The site will not start

- Read the message in the terminal. A syntax error names the file
  and the line. Fix that line and run the program again.
- If the terminal shows a message titled "Port already in use", see
  [The browser shows an old or different app](#the-browser-shows-an-old-or-different-app).
- If `import drafter` itself fails, the installation is the problem.
  See [Get Drafter running](../start/install.md).
- If the program ends right away without starting a site, the
  `DRAFTER_SKIP` environment variable may be set in your terminal. It
  tells `start_server` to do nothing, which is meant for
  [test runners](../add/use-pytest-or-unittest.md). Open a new
  terminal, or unset the variable.

## The loading screen never finishes

When a site opens, the browser first downloads and starts Python.
Until that work is done, the first page appears faded behind a
spinner and the words "Loading, please wait...", and buttons do not
respond. The message disappears when the site is ready.

- Check the internet connection. The browser downloads Python from
  `cdn.jsdelivr.net` and Python libraries from `pypi.org`, even when
  the site itself runs from your own computer.
- If the download fails, the loading screen is replaced by a box
  titled "Something Went Wrong" that begins "Drafter could not
  download the files it needs to run Python in your browser." Follow
  the steps in the box. Reload with a hard refresh
  (++ctrl+shift+r++, or ++cmd+shift+r++ on a Mac), and if that does
  not help, try a different network, because some school and work
  networks block these downloads.
- A program that imports large libraries takes longer to load,
  because the browser downloads each library before your code runs.
  If a library cannot be loaded at all, see
  [A library import fails in the browser](errors/package-import-error.md).
- If the screen still does not change, open the browser's developer
  tools with ++f12++ and read the Console tab. Copy any red message
  there when you ask for help.

## Everything appears on one line

Drafter puts the items of a page's content list one after another
on the same line. It does not start a new line between items. To
end a line, put `"\n"` at the end of a string.

```python
return Page(state, [
    "Name: Ada\n",
    "Species: corgi\n",
    Button("Feed", "feed")
])
```

Each `"\n"` becomes a line break on the page, and two of them in a
row leave an empty line. A `Header` already starts on a line of its
own.

## A picture shows as a broken image

A small broken-picture icon in place of your image means that the
browser asked for the file and did not get it. Drafter does not show
an error page or a warning for a missing picture, so the icon is the
only sign on the page.

- Compare the filename in your code, such as `Image("ada.png")`,
  with the name of the real file, including the ending.
- Check that the file sits next to your program.
- While the program runs on your computer, the terminal prints a
  line ending in `404 Not Found` for each file that the browser
  asked for and did not get. That line shows the exact name that was
  requested.
- If the picture works on your computer and is broken only on the
  deployed site, see
  [Image or file works locally but 404s when deployed](errors/missing-asset-on-deploy.md).

[Use pictures](../add/pictures.md) has more on images that come from
a web address and on uploaded pictures.

## It works on my computer but not on the deployed site

The deployed site is built from the files in your repository, and
it usually has no debug panel, so problems look different there.

- A red X next to the deployment means that the build failed and the
  site was not updated. See
  [GitHub Actions build failed](errors/deploy-build-failed.md).
- A picture or data file that is missing only on the deployed site
  was not uploaded or not declared. See
  [Image or file works locally but 404s when deployed](errors/missing-asset-on-deploy.md).
- A library that works on your computer may not work in the browser.
  See
  [A library import fails in the browser](errors/package-import-error.md).
- A site that still shows an old version was not deployed again
  after your last change, or the browser kept an old copy.
  [Fix a failed deployment](../your-project/deploy/troubleshooting.md)
  explains how to run the deployment again and how to read its log.
- Error pages look the same on a deployed site as on your computer,
  so read them the same way. If your program calls
  `hide_debug_information()`, the debug panel and the Console box
  are hidden, and `print()` output appears only in the browser's
  developer tools (++f12++, then the Console tab).

## The page looks plain or unstyled

When a stylesheet cannot be loaded, a notice appears at the top of
your site that starts "Some of this page's styling did not load" and
names the file. The debug panel lists the same problem as a warning.
Your Python code is not the cause, and the rest of the app keeps
working.

- Reload the page first. A brief network hiccup is the usual reason.
- If the file is one you added with
  [`add_website_css_file`](../reference/site-config.md#add_website_css_file),
  check its spelling and that it sits next to your program.
- On a deployed site, check that the file was uploaded with the rest
  of the site.
- If the file belongs to Drafter (its address contains `assets/`) and
  reloading does not help, that is worth a
  [bug report](bug-reports.md).

## My code after start_server never runs

This behavior is
[by design](errors/nothing-after-start-server.md). The call to
`start_server(...)` takes over the program. Configuration and tests
go before it, and behavior goes in routes.

## The first load is slow

The browser downloads and starts a complete copy of Python before
your site can respond, so expect a delay of several seconds on the
first visit. During that time the first page is visible but faded,
behind the words "Loading, please wait...". If the message stays,
see
[The loading screen never finishes](#the-loading-screen-never-finishes).
If the browser reports that it cannot reach the site at all, check
that the terminal printed a line starting with `Drafter ready at`
and that the program is still running.

## Tests pass but the app misbehaves

Tests only exercise the routes you wrote them for, so the
misbehavior is probably on a path that has no test yet. Reproduce
the bad behavior by hand,
note which route ran, and write a failing assertion for it before
fixing it. See [Test a feature](../add/test-a-feature.md).

## Still stuck?

- [The debug panel in depth](debug-panel.md) shows your app's state
  and history while you interact with it.
- [Print and the console](printing-and-console.md) is the fastest way
  to see what a route actually received.
- If you believe Drafter itself misbehaved, see
  [Report a Drafter bug](bug-reports.md).
