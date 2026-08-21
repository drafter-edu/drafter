---
page_type: how-to
title: Deploy and submit
level: L2
audience: S
priority: P0
prereqs: [your-project/build-one-path]
symbols: []
outcome: Understand what deployment is and see the three steps.
---

# Deploy and submit

## Goal

Your app works on your computer. Now you want a real link that works on
anyone's phone or laptop, whether or not your own computer is turned on.

## Before you start

You need a working app and a GitHub account. Expect the whole process to
take about half an hour the first time, most of it waiting and checking.

Two ideas are worth understanding before you start, so that nothing
later comes as a surprise:

- **Deploying means compiling.** Drafter turns your program into a
  static website: a set of files that any web server can serve. Your Python
  still runs in each visitor's browser, exactly as it does now. There is
  still no backend, and state still resets on reload.
- **`localhost` links are not shareable.** The address your app has
  while you develop (something like `http://localhost:8000`) only exists
  on your own computer while your program runs. That is why deployment
  exists.

## The three steps

1. **[Prepare for release](prepare.md)**: add the finishing settings to
   your code (site title, site information, hiding the debugger) and
   test locally.
2. **[Publish on GitHub Pages](github-pages.md)**: create a repository
   from Drafter's template, put your code in it, and run the deploy
   workflow.
3. **Verify**: open your new link on a different device and click
   through the whole app. If something went wrong,
   [fix the failed deployment](troubleshooting.md).

When it works, you will have a URL like
`https://your-username.github.io/your-repository/` that you can put on a
resume, send to a friend, or submit.

## Submitting for a course

Courses often add their own requirements around deployment: specific
repository links, videos, documents to include, or a place to submit
your URL. Those live in your course's own instructions, not here.
Follow this guide for the deployment itself, then your course's
checklist for the rest.

## Common problems

- **You submitted or shared a `localhost` link**: that link only works
  on your machine. Share the deployed `github.io` URL, and test it from
  another device first.
- **You shared the repository link instead**: the code lives at
  `github.com/...`, while the running site lives at `...github.io/...`.
  Share the site link, not the code link.
- **The deployment failed**: go to
  [Fix a failed deployment](troubleshooting.md). The error log almost
  always names the problem.

## Understand it

[How Drafter works](../../start/how-drafter-works.md) and
[How the web works](../../concepts/how-the-web-works.md) explain why
there is no server to rent and nothing to install.

## See another example

Every app in the [project gallery](../gallery/index.md) was deployed
exactly this way.

## Look it up

See [Site configuration](../../reference/site-config.md) for every
`set_...` function used in preparation.

## Fix a problem

[Fix a failed deployment](troubleshooting.md) and
[missing assets on deploy](../../help/errors/missing-asset-on-deploy.md).

## Next steps

This page was the overview. The work starts with the first step below.

<div class="grid cards" markdown>

- **Step 1 of 3: Prepare for release**

    ---

    Titles, the about page, hiding the debugger. A few lines of code and
    a local test.

    [Prepare for release](prepare.md)

</div>
