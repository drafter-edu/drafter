---
page_type: how-to
title: Deploy with GitHub Actions
level: L4
audience: S
priority: P2
prereqs: [your-project/deploy/github-pages]
symbols: []
outcome: Set up a repository that rebuilds and deploys your site on every push.
---

# Deploy with GitHub Actions

## Goal

Build a repository, from nothing, that compiles and publishes
your Drafter app automatically every time you push a change. No
template, no course-provided setup: you will write the workflow
file yourself and understand every line of it.

## Before you start

The [standard deploy guide](../your-project/deploy/github-pages.md)
assumes a repository where this machinery already exists, which
is the right starting point the first time. This page is for
when you want to own the machinery: a personal project, a
portfolio, or plain curiosity about what that magic workflow
actually does.

You need a GitHub account and basic comfort with repositories
(creating one, adding files, committing). Everything here works
through GitHub's web editor, though git on your own machine
makes iteration pleasanter.

The idea in one paragraph: GitHub Pages can serve whatever a
GitHub Actions workflow builds. A workflow is a recipe file in
your repository; on every push, GitHub starts a fresh Linux
machine, follows the recipe (install Drafter, compile your app
to static files, hand them to Pages), and your site updates
itself. Your repository becomes the single source of truth, and
"deploying" becomes something that happens to you rather than
something you do.

## Step 1: The repository

Create a new repository (public, or private with Pages enabled
on your plan) containing:

```text
your-repo/
├── .github/
│   └── workflows/
│       └── deploy.yml    <- the recipe, written in step 2
├── main.py               <- your Drafter program
└── pets.csv              <- any data files your app opens
```

The `.github/workflows/` location is a GitHub convention: any
`.yml` file in that folder is a workflow. The program file can
have any name as long as the workflow uses the same one; this
guide assumes `main.py`.

## Step 2: The workflow file

Create `.github/workflows/deploy.yml` with exactly this content
(adjusting `main.py` if your file is named differently):

```yaml
name: Deploy Drafter site to Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Set up uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Build the site
        run: |
          uvx drafter main.py --compile --output-directory _site --production
          touch _site/.nojekyll

      - uses: actions/upload-pages-artifact@main
        with:
          path: ./_site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

Block by block, top to bottom:

- **`on:`** — when the recipe runs: every push to the `main`
  branch, plus `workflow_dispatch`, which adds a manual "Run
  workflow" button in the Actions tab. That button is worth
  having on day one, for re-deploying without inventing a
  commit.
- **`permissions:`** — workflows start powerless, and this block
  grants exactly what deployment needs: read the code, write to
  Pages, and mint the identity token Pages uses to trust the
  upload. Leaving this block out is the classic
  mysterious-failure.
- **`concurrency:`** — if you push twice quickly, the second
  run cancels the first instead of the two racing to deploy in
  whichever order they finish.
- **The `build` job** — the recipe proper, on a fresh Ubuntu
  machine: `checkout` copies your repository onto it, the two
  `uv` steps install a fast Python toolchain and Python 3.12,
  and then one line does the real work. `uvx drafter ...`
  installs the latest Drafter from PyPI into a throwaway
  environment and runs it; `--compile` builds the static site
  into `_site`, and `--production` hides the debug panel, the
  same as the [prepare step](../your-project/deploy/prepare.md)
  taught. The `.nojekyll` file tells Pages to serve the output
  as-is rather than running its own site generator over it.
  Finally, `upload-pages-artifact` zips `_site` and hands it
  off.
- **The `deploy` job** — waits for the build (`needs: build`),
  then publishes the artifact to Pages. The `environment` block
  is what makes the run's summary page show your live URL.

## Step 3: Turn on Pages

One setting, and forgetting it is the most common failure on
this page: in the repository, go to **Settings → Pages**, and
under **Build and deployment**, set **Source** to **GitHub
Actions**. Without this, your workflow builds happily and Pages
ignores everything it produces.

## Step 4: Push and watch

Commit the workflow file (that push is itself a push to `main`,
so the first run starts immediately). The **Actions** tab shows
the run: two jobs, `build` then `deploy`, each expandable to
live logs. Green checks all the way down means the deploy job's
summary shows your URL, which will be:

```text
https://YOUR-USERNAME.github.io/YOUR-REPO/
```

From now on, editing `main.py` and committing is the entire
deployment process. The first successful deploy can take a
minute or two to become reachable; later ones are faster.

## Variations

- **Your app opens data files.** Bundle them into the build by
  extending the compile line:

    ```console
    uvx drafter main.py --compile --output-directory _site --production --additional-paths pets.csv --additional-paths words.txt
    ```

- **Your app imports third-party packages.** The throwaway
  environment needs them at compile time too:

    ```console
    uvx --with matplotlib drafter main.py --compile --output-directory _site --production
    ```

- **Several apps in one repository.** Put each app in its own
  folder and replace the build step with a loop that compiles
  each into a subfolder of `_site`, writing an `index.html`
  of links as it goes:

    ```yaml
    - name: Build every site
      run: |
        mkdir -p _site
        echo "<html><body><h1>My Drafter apps</h1><ul>" > _site/index.html
        for dir in ./apps/*; do
          if [ -d "$dir" ]; then
            site_name=$(basename "$dir")
            cd "$dir"
            uvx drafter main.py --compile --output-directory "../../_site/$site_name" --production
            cd ../..
            echo "<li><a href=\"$site_name/\">$site_name</a></li>" >> _site/index.html
          fi
        done
        echo "</ul></body></html>" >> _site/index.html
        touch _site/.nojekyll
    ```

    Each app lands at `.../YOUR-REPO/app-name/`, with the index
    page linking them all: a one-repository portfolio.

## Common problems

- **The build job fails.** Open its log; the red step tells you
  where. A Python syntax error in `main.py` surfaces here, which
  means a broken push never replaces your working site: the
  deploy job simply does not run.
- **Everything is green but the site is a 404.** Almost always
  step 3: the Pages source is still "Deploy from a branch"
  instead of "GitHub Actions". Second suspect: the first deploy
  needs a minute or two.
- **`main.py` not found.** The filename in the build step must
  match the file in the repository exactly, and the file must be
  at the repository root (or the step needs a `cd` first).
- **Works on your machine, deployed site missing images or
  data.** The runner only bundles what `--additional-paths`
  names; see the
  [missing asset entry](../help/errors/missing-asset-on-deploy.md).
- **A permissions error mentioning tokens or `id-token`.** The
  `permissions:` block is missing or incomplete; copy it exactly
  as shown.
- **The workflow never runs.** The file must live at
  `.github/workflows/deploy.yml` (both dots matter), and pushes
  must be to the branch named in `on:` — a repository whose
  default branch is `master` needs the workflow to say so.

## Related

- [Publish on GitHub Pages](../your-project/deploy/github-pages.md):
  the template-based version of this journey.
- [Fix a failed deployment](../your-project/deploy/troubleshooting.md):
  reading Actions logs in more detail.
- [GitHub's own Actions documentation](https://docs.github.com/en/actions):
  the full workflow language, far beyond deployment.
