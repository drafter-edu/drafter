---
page_type: concept
title: How the web works
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Understand URLs, browsers, and servers well enough to place Drafter.
---

# How the web works

## In one sentence

The web is browsers asking servers for pages by address, and Drafter
is unusual because after the first load, your app answers those
requests from inside the browser itself.

## The idea

The web has three main participants, each with its own job:

- **The browser** (Chrome, Firefox, Safari) is a program on your
  device that asks for pages, receives them as HTML, and draws them.
- **A server** is a program on someone else's computer that answers
  those requests, sending back pages or data.
- **A URL** is the address that connects them: which server to ask,
  and for what.

When you visit a typical website, the conversation repeats: the
browser requests a page, the server responds, the browser renders
the result, and each click starts another request. In that
arrangement, the server is the application and the browser is its
display.

### Reading a URL

```text
https://ada.github.io/snack-tracker/?page=history
\___/  \____________/\_____________/\___________/
scheme     host           path         query
```

- The **scheme** (`https://`) is the protocol, with the `s` meaning
  the connection is encrypted.
- The **host** (`ada.github.io`) names which server to ask.
- The **path** (`/snack-tracker/`) names what to ask it for.
- The **query** (`?page=history`) carries extra values.

### Where Drafter fits

A deployed Drafter app changes this arrangement. The server (GitHub
Pages) hands over one package: the page, the Python runtime, and your
program. After that, the "server" your buttons talk to is your own
program, running inside the browser tab. Clicking a button does not
send a request across the internet; it calls your route function
right there in the tab.

That is why these docs keep saying there is no backend: after
loading, there is no distant computer running your code. Everything
the app knows and does lives in the visitor's tab.

## See it

The diagram below shows the same click handled both ways:

```text
A classic web app:                 A Drafter app, deployed:

browser ──request──▶ server        browser tab
   ◀──new page────                ┌──────────────────────────┐
(the internet, every click)        │  your page               │
                                   │     │ click              │
                                   │     ▼                    │
                                   │  your Python routes      │
                                   │     │ new page           │
                                   │     ▼                    │
                                   │  your page, updated      │
                                   └──────────────────────────┘
                                   (no internet after loading)
```

You can watch this yourself: load your deployed app, turn off your
device's network, and keep clicking. The app keeps working, because
nothing it needs is remote anymore. (Reloading, though, needs the
network again: the package comes from the server.)

## What this means for your code

- **`localhost` addresses are private and temporary.** While you
  develop, your app's address looks like `http://localhost:8080`.
  `localhost` always means "this same device", so the address is
  meaningless to anyone else, and it stops working when your program
  stops. To share your app, [deploy it](../your-project/deploy/index.md),
  which gives it a real host name.
- **Each visitor gets their own app.** With no shared server, two
  people using your deployed app are running two separate copies;
  nothing one does is visible to the other. A shared high-score
  board needs a real backend, which is
  [beyond Drafter on purpose](../teach/why-drafter.md).
- **Reload starts over.** State lives in the tab's memory, so
  reloading starts a fresh copy of the app. See
  [State](state.md).
- **Nothing in your app is secret.** The whole program ships to
  every visitor's browser, where anyone can read it. Never put a
  password or a private key in your code; see
  [Security honestly](../extend/security.md).

## Where people get confused

- **"My site is running, here is the localhost link."** That link
  reaches your device only, and only while the program runs. To share
  the app, deploy it.
- **"The server saves my data."** There is no server after loading;
  nothing is saved anywhere unless you build saving into the app.
- **"HTTPS means my login page is secure."** HTTPS encrypts the
  connection. It says nothing about your app's logic; a simulated
  login is still a simulation, delivered securely.
- **"If I hide the code, visitors can't see it."** Delivering the
  app means delivering the code, and making the code harder to read
  does not make it secret.

## Go deeper

- [How Drafter works](../start/how-drafter-works.md) explains the
  same runtime model from the programmer's point of view.
- [Deploy and submit](../your-project/deploy/index.md) shows how to
  turn a localhost address into a real one.
- [Python in the browser](../extend/pyodide.md) describes how a
  browser can run Python at all.
