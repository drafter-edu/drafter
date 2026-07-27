---
page_type: error
title: GitHub Actions build failed
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Diagnose a failed GitHub Actions build.
error_text: "Process completed with exit code 1"
---

# GitHub Actions build failed

## The error

A red X appears next to your deployment in the repository's
**Actions** tab, and GitHub sends you an email about a failed
workflow run. The log of the failed step typically ends with:

```text
Error: Process completed with exit code 1.
```

The useful message is the lines just above that one.

## What it means

The deployment is a program GitHub runs for you: it takes your
repository, builds your Drafter app into a static site, and
publishes it. One of those steps failed, so your site was not
updated. Your previous deployed version, if any, is still up.

## Where to look

In the Actions tab, open the failed run (the one with the red X),
then the failing job, and expand the failing step. Read the last
several lines of the log; the real error is named there, and it is
often a Python message you already know how to read. Only the newest
run matters; older failed runs are records of past attempts and do
not affect the current site.

## Check

Compare the last lines of the log against these common causes:

- **Pages or permissions complaints** → GitHub Pages is not enabled
  as the source; enable it under Settings → Pages → Source →
  GitHub Actions.
- **A Python traceback** → your code has an error; if it does not run
  on your computer, it will not deploy.
- **A missing file** → see
  [works locally, 404s deployed](missing-asset-on-deploy.md);
  a file the build needs was never uploaded.
- **Nothing found to build** → the workflow expects your program to
  be in a file named `main.py`, with exactly that name.

## Fix

Fix the named cause locally, run the app on your own computer to
prove it works, then commit the change and run the workflow again
(the Actions tab has a Re-run option, and any new commit also
triggers it).

## Confirm

The newest run shows a green checkmark, and the live site reflects
your change. Check it in a private browser window or from a second
device so that you are not looking at a cached copy.

## Prevent

Deploy only what already runs locally, and deploy small changes
often. When a failure follows a small change, you can be confident
about which change caused it.

## Understand

[Fix a failed deployment](../../your-project/deploy/troubleshooting.md)
is the full walkthrough with screenshots, including the deployment
dashboard; [What deploying means](../../your-project/deploy/index.md)
explains the pipeline this error interrupts.
