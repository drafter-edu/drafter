---
page_type: error
title: Image or file works locally but 404s when deployed
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix assets that work locally but 404 when deployed.
error_text: "the server responded with a status of 404"
---

# Image or file works locally but 404s when deployed

## The error

On your own computer the app works. On the deployed site, an image
or a file is missing, and what you see depends on how your program
uses the file.

A missing image does not produce a Drafter error page. The page
appears with a broken-image icon where the picture belongs. The
browser's developer console (open it with ++f12++, Console or Network
tab) shows a line that begins:

```text
Failed to load resource: the server responded with a status of 404
```

If the deployed site still shows the debug panel, the panel lists a
warning for each image that failed. The warning begins "The browser
could not load one of the images on this site", and its Details name
the image:

```text
The image 'ada.png' could not be loaded.
```

A missing file that your code reads with `open(...)` produces an
error page with this title:

```text
File Not Found
```

The sentence under the title reads "Your code tried to open a file
that Python could not find." The technical message names the file:

```text
request.route_execution_failed: Error while processing request for URL 'index':
File not found: pets.txt
```

## What it means

Your program refers to a file by name, such as `Image("ada.png")` or
`open("pets.txt")`. On your computer, that file sits next to your
program, so the name leads to it. The deployed site contains only the
files that the build placed there. The file is either absent from the
site, or present under a different name or in a different folder, so
the browser's request for it is answered with 404, the web's code for
"no such file".

## Where to look

Look at the repository on GitHub. Compare the files listed there
against every filename your program mentions, including the folder
and the capital letters.

## Check

- **The file was never uploaded**: it exists on your computer but not
  in the repository listing.
- **The folder differs**: the code says `images/ada.png`, but the
  file was uploaded to the top of the repository, or the reverse.
  The build keeps every file in the folder where it found it.
- **The capital letters differ**: `Ada.PNG` was uploaded and the
  code says `ada.png`. Deployed sites treat `Ada.PNG` and `ada.png`
  as two different names, even if your own computer does not.
- **The site was not rebuilt after the upload**: the Actions tab
  shows no run newer than the upload, or the newest run failed.
- **The build was never told about the file**: this cause applies
  when you build the site yourself with `--compile`, or when your
  repository does not use Drafter's deployment template. The Fix
  section explains the difference.

## Fix

What is needed depends on how the site is built.

If you deploy with
[Drafter's deployment template](../../your-project/deploy/github-pages.md),
the build copies the files and folders at the top of your repository
into the site. Upload the file to the repository, next to `main.py`
or in the folder your code names, with exactly the spelling and
capital letters the code uses. Then run the deploy workflow again
and wait for the Actions tab to show it finishing.

If you build the site yourself with `--compile`, or with a workflow
of your own, the build copies only your program. An image or a data
file that your code names is not picked up automatically. Declare
each file in your program, above the routes:

```python
add_website_file("ada.png")
add_website_file("images/cat.png")
```

The build then copies each declared file into the site, in the same
folder it has next to your program. To declare every file in a folder
at once, name the folder, as in `add_website_file("images")`. The
`--additional-paths` command line flag does the same job from outside
the code.

## Confirm

Reload the deployed site with a hard refresh (++ctrl+shift+r++), and
check from a second device if you can. The image appears, or the
page that reads the file is displayed.

## Prevent

Keep every asset in the same folder as your program from the start,
use lowercase filenames with no spaces, and after any deploy, click
through the pages that show images or open files.

Declaring files with
[`add_website_file`](../../reference/site-config.md#add_website_file)
also helps while you develop, whichever way you deploy. Drafter
checks that each declared file exists as soon as the program starts.
A misspelled or missing name stops the program with a message in the
terminal titled "Website File Not Found", which names the file and
suggests files with similar names. A name whose
capital letters differ from the file's, such as `ada.png` for
`Ada.PNG`, stops the program with a message titled "Website File Name
Has Different Capital Letters". Both happen on your own computer, long
before anyone visits the deployed site. Stylesheets and scripts added with
`add_website_css_file` and `add_website_js_file` are declared
automatically.

## Understand

[What deploying means](../../your-project/deploy/index.md) explains
that the deployed site contains exactly what is in the repository
and nothing more.
[Fix a failed deployment](../../your-project/deploy/troubleshooting.md)
covers the broader set of deployment failures.
