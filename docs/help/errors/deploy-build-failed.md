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

A red X next to your deployment in the repository's **Actions** tab,
and an email from GitHub about a failed workflow run. The log of the
failed step typically ends with:

```text
Error: Process completed with exit code 1.
```

The useful message is the lines just above that one.

## What it means

The deployment is a program GitHub runs for you: it takes your
repository, builds your Drafter app into a static site, and
publishes it. Some step of that failed, so your site was not updated.
Your previous deployed version, if any, is still up.

## Where to look

Actions tab → the failed run (red X) → the failing job → expand the
failing step. Read the last several lines of the log; the real error
is named there, and it is often a Python message you already know how
to read. Only the newest run matters; older red runs are history.

## Check

Match the log's last lines against the usual suspects:

- **Pages or permissions complaints** → GitHub Pages is not enabled
  as the source; enable it under Settings → Pages → Source →
  GitHub Actions.
- **A Python traceback** → your code has an error; if it does not run
  on your computer, it will not deploy.
- **A missing file** → see
  [works locally, 404s deployed](missing-asset-on-deploy.md);
  a file the build needs was never uploaded.
- **Nothing found to build** → the workflow expects your program in
  `main.py`, exactly that name.

## Fix

Fix the named cause locally, run the app on your own computer to
prove it works, then commit the change and run the workflow again
(the Actions tab has a Re-run option, and any new commit also
triggers it).

## Confirm

The newest run shows a green checkmark, and the live site reflects
your change. Check it in a private browser window or from a second
device to dodge caching.

## Prevent

Deploy only what already runs locally, and deploy small changes
often; a failure right after a small change is easy to blame on the
right thing.

## Understand

[Fix a failed deployment](../../your-project/deploy/troubleshooting.md)
is the full walkthrough with screenshots, including the deployment
dashboard; [What deploying means](../../your-project/deploy/index.md)
explains the pipeline this error interrupts.
