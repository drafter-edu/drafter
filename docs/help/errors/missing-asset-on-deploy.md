---
page_type: error
title: Image or file works locally but 404s when deployed
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix assets that work locally but 404 when deployed.
error_text: "404 (Not Found)"
---

# Image or file works locally but 404s when deployed

## The error

On the deployed site, an image shows as a broken icon, or a file the
app opens fails to load. The browser's developer console (open it
with ++f12++, Console or Network tab) shows a request ending in:

```text
404 (Not Found)
```

On your own computer, the same app works perfectly.

## What it means

Your program refers to a file by name, such as `Image("ada.png")` or
`open("pets.txt")`. Locally, that file sits next to your program, so
everything works. The deployed site only contains what you uploaded
to the repository; the file is not there, so the browser gets a "no
such file" answer.

## Where to look

Look at the repository on GitHub. Compare the files listed there
against every filename your program mentions.

## Check

- **The file was never uploaded**: it exists on your computer but not
  in the repository listing.
- **The name differs**: `Ada.PNG` uploaded, `ada.png` in the code.
  Deployed sites treat filenames as case-sensitive even if your own
  computer does not.
- **The path differs**: the code says `images/ada.png`, but the file
  was uploaded to the repository root (or the reverse).

## Fix

Upload the file to the repository, next to `main.py` (or in the
folder your code names), with exactly the spelling the code uses.
Then run the deploy workflow again; the dashboard and Actions tab
show it finishing.

## Confirm

Reload the deployed site with a hard refresh (++ctrl+shift+r++), and
check from a second device if you can; the image or file should
appear.

## Prevent

Keep every asset in the same folder as your program from the start,
use lowercase filenames with no spaces, and after any deploy, click
through the pages that show images or open files.

## Understand

[What deploying means](../../your-project/deploy/index.md) explains
that the deployed site contains exactly what is in the repository
and nothing more.
[Fix a failed deployment](../../your-project/deploy/troubleshooting.md)
covers the broader set of deployment failures.
