/* Drafter docs slide mode.
 *
 * Adds a "Present" button to the header of every page. Pressing it turns the
 * page into a slide deck: the opening block (badges, title) is the first
 * slide, and every top-level "## heading" starts a new one.
 *
 * How it works:
 *
 * - Nothing is moved. Each block of the article is tagged, and CSS decides
 *   which blocks show (see drafter-slides.css). Demo iframes are therefore
 *   never re-parented, which would reload them and restart their Python.
 * - A section that does not fit on one screen continues on further slides.
 *   Long tables and lists continue row by row and item by item.
 * - A slide that is slightly too tall is scaled down, but never below
 *   MIN_FIT. Past that, programs and demos scroll inside their own boxes,
 *   and as a last resort the slide itself scrolls. The Next key pages
 *   through a hidden part of a program or slide before moving on, so
 *   nothing is out of reach.
 * - The deck is laid out again whenever the window changes size, which
 *   covers browser zoom and full screen.
 * - The short sections that open a page (OPENING_SECTIONS) join the title
 *   slide instead of making slides of their own.
 * - Sections that are for reading rather than presenting (CLOSING_SECTIONS)
 *   are left out.
 * - Each page is its own deck. An end card links to the next page, and
 *   following it reopens slide mode there.
 */
(function () {
  "use strict";

  /* Sections that say in a sentence or two what a page is for and what the
   * reader needs first. Each would be a nearly empty slide, so while nothing
   * else has started a slide their text joins the title slide and their
   * headings are left out. tests/test_docs_slides.py checks this list
   * against the headings the pages use. */
  var OPENING_SECTIONS = ["Goal", "In one sentence", "Before you start"];

  /* Sections that are for reading, not for presenting. Sections that tell an
   * audience what to do next ("Next steps", "Go deeper") are deliberately
   * not here.
   *
   * Most are cross-reference lists, links that do nothing on a projector.
   * The first four are the four-link block, FOUR_LINKS in
   * tools/docs_lint.py. "Understand" is its counterpart on error pages, and
   * the next three close the reference pages. "In more depth" is where a
   * page keeps the detail a presenter would skip; everything under it, down
   * to the next "##" heading, stays out of the deck.
   * tests/test_docs_slides.py checks this list against the linter and the
   * pages. */
  var CLOSING_SECTIONS = [
    "Understand it",
    "See another example",
    "Look it up",
    "Fix a problem",
    "Understand",
    "Related",
    "Related components",
    "External links",
    "In more depth",
  ];

  /* Top-level children of the article that are never slide content. */
  var SKIPPED =
    "script, style, link, template, noscript, .drafter-zone-banner, " +
    ".md-content__button, .md-source-file, .md-feedback";

  /* Containers that are always one block, even if they contain headings. */
  var OPAQUE =
    ".admonition, .tabbed-set, .highlight, .drafter-demo, .grid, " +
    ".md-typeset__scrollwrap";

  /* Smallest scale a slide may be shrunk to. */
  var MIN_FIT = 0.65;
  /* A section is split across slides once it would need less than this. */
  var SPLIT_FIT = 0.85;
  /* Scale used when a slide has to scroll anyway. */
  var SCROLL_FIT = 0.85;
  var FIT_STEP = 0.05;
  /* Shortest a scrolling program or demo box may get, in CSS pixels. */
  var MIN_BOX_HEIGHT = 96;
  /* Fraction of the visible height that one Next press scrolls. */
  var PAGE_STEP = 0.8;

  var RESUME_KEY = "drafter-slides-resume";

  var BLOCK = "drafter-slides__block";
  var BLOCK_ON = "drafter-slides__block--on";
  var FLAT = "drafter-slides__flat";
  var HEAD = "drafter-slides__head";
  var SRC = "drafter-slides__src";
  var DEMO = "drafter-slides__demo";
  var ITEM_OFF = "drafter-slides__item--off";
  var PART = "data-drafter-slides-part";

  var root = document.documentElement;
  var bar = null; // built on first use
  var ui = {};
  var deck = null; // non-null while presenting

  /* ------------------------------------------------------------------ */
  /* Reading the page                                                    */
  /* ------------------------------------------------------------------ */

  function headingText(el) {
    return el.textContent.replace(/¶/g, "").trim();
  }

  /* Gather the article's blocks in document order. A plain wrapper that
   * contains headings is made transparent and its children are used
   * instead, so pages built from nested containers still split. */
  function collect(container, blocks, flats) {
    for (var i = 0; i < container.children.length; i++) {
      var el = container.children[i];
      if (el.matches(SKIPPED)) {
        continue;
      }
      var isWrapper =
        (el.tagName === "DIV" || el.tagName === "SECTION") &&
        !el.matches(OPAQUE) &&
        el !== deck.endCard &&
        el.querySelector("h2, h3, h4");
      if (isWrapper) {
        flats.push(el);
        collect(el, blocks, flats);
      } else {
        blocks.push(el);
      }
    }
  }

  /* The rows of a table or items of a list, when the block can continue
   * across slides one at a time. */
  function splitItems(block) {
    if (block.tagName === "UL" || block.tagName === "OL") {
      var items = [];
      for (var i = 0; i < block.children.length; i++) {
        if (block.children[i].tagName !== "LI") {
          return null;
        }
        items.push(block.children[i]);
      }
      return items.length > 1 ? items : null;
    }
    var table = null;
    if (block.tagName === "TABLE") {
      table = block;
    } else if (block.matches(".md-typeset__scrollwrap")) {
      table = block.querySelector("table");
    }
    if (
      table &&
      table.tBodies.length === 1 &&
      table.tBodies[0].rows.length > 3 &&
      !table.querySelector("[rowspan]")
    ) {
      return Array.prototype.slice.call(table.tBodies[0].rows);
    }
    return null;
  }

  function clearTags() {
    var tagged = deck.stage.querySelectorAll(
      "." + BLOCK + ", ." + FLAT + ", ." + ITEM_OFF + ", [" + PART + "]",
    );
    for (var i = 0; i < tagged.length; i++) {
      tagged[i].classList.remove(BLOCK, BLOCK_ON, FLAT, HEAD, SRC, DEMO, ITEM_OFF);
      if (tagged[i].classList.length === 0) {
        tagged[i].removeAttribute("class");
      }
      tagged[i].removeAttribute(PART);
    }
    deck.starts.forEach(function (start, list) {
      if (start === null) {
        list.removeAttribute("start");
      } else {
        list.setAttribute("start", start);
      }
    });
    deck.starts = new Map();
    deck.items.forEach(function (items) {
      items.forEach(function (item) {
        item.classList.remove(ITEM_OFF);
        if (item.classList.length === 0) {
          item.removeAttribute("class");
        }
      });
    });
    releaseBoxes();
  }

  /* Tag the article and group its blocks into slides. Safe to repeat. */
  function readPage() {
    clearTags();
    var all = [];
    var flats = [];
    collect(deck.stage, all, flats);
    flats.forEach(function (el) {
      el.classList.add(FLAT);
    });

    var slides = [{ head: [], blocks: [], title: "" }];
    var blocks = [];
    var folded = [];
    var skipping = false;
    all.forEach(function (el) {
      if (el === deck.endCard) {
        slides.push({ head: [], blocks: [el], title: "End of page", end: true });
      } else if (el.tagName === "H2") {
        var title = headingText(el);
        skipping = CLOSING_SECTIONS.indexOf(title) !== -1;
        if (skipping) {
          return;
        }
        if (slides.length === 1 && OPENING_SECTIONS.indexOf(title) !== -1) {
          // The heading is left untagged, which hides it; the blocks under
          // it land on the title slide like any others.
          folded.push(el);
          return;
        }
        slides.push({ head: [el], blocks: [], title: title });
      } else if (skipping) {
        return;
      } else {
        var slide = slides[slides.length - 1];
        var opening =
          slides.length === 1 &&
          slide.blocks.length === 0 &&
          (el.tagName === "H1" || el.matches(".drafter-page-meta"));
        if (opening) {
          slide.head.push(el);
          if (el.tagName === "H1") {
            slide.title = headingText(el);
          }
        } else {
          slide.blocks.push(el);
        }
      }
      blocks.push(el);
    });
    if (slides[0].head.length === 0 && slides[0].blocks.length === 0) {
      slides.shift();
    } else if (!slides[0].title) {
      slides[0].title = document.title;
    }

    deck.items = new Map();
    slides.forEach(function (slide) {
      slide.head.forEach(function (el) {
        el.classList.add(HEAD);
      });
      slide.atoms = [];
      slide.blocks.forEach(function (block, index) {
        var before = slide.blocks[index - 1];
        if (block.matches(".drafter-demo") && before && before.matches("div.highlight")) {
          before.classList.add(SRC);
          block.classList.add(DEMO);
        }
        var items = splitItems(block);
        if (items) {
          deck.items.set(block, items);
          items.forEach(function (item, k) {
            slide.atoms.push({ block: block, item: item, k: k });
          });
        } else {
          slide.atoms.push({ block: block, item: null, k: 0 });
        }
      });
    });
    blocks.forEach(function (el) {
      el.classList.add(BLOCK);
    });
    deck.blocks = blocks;
    deck.folded = folded;
    deck.slides = slides;
  }

  /* ------------------------------------------------------------------ */
  /* Layout                                                              */
  /* ------------------------------------------------------------------ */

  function setFit(fit) {
    deck.fit = fit;
    deck.stage.style.setProperty("--drafter-slides-zoom", String(deck.base * fit));
  }

  function overflows() {
    return deck.stage.scrollHeight > deck.stage.clientHeight + 1;
  }

  /* Show atoms [from, to) of a slide, plus its heading. */
  function reveal(slide, from, to) {
    var on = slide.head.slice();
    var ranges = new Map();
    for (var i = from; i < to; i++) {
      var atom = slide.atoms[i];
      if (on.indexOf(atom.block) === -1) {
        on.push(atom.block);
      }
      if (atom.item) {
        var range = ranges.get(atom.block);
        if (range) {
          range[1] = atom.k;
        } else {
          ranges.set(atom.block, [atom.k, atom.k]);
        }
      }
    }
    deck.blocks.forEach(function (el) {
      el.classList.toggle(BLOCK_ON, on.indexOf(el) !== -1);
    });
    ranges.forEach(function (range, block) {
      deck.items.get(block).forEach(function (item, k) {
        item.classList.toggle(ITEM_OFF, k < range[0] || k > range[1]);
      });
      if (block.tagName === "OL") {
        // Hidden items do not count, so a continued list is told where to
        // resume its numbering.
        if (!deck.starts.has(block)) {
          deck.starts.set(block, block.getAttribute("start"));
        }
        var first = Number(deck.starts.get(block)) || 1;
        block.setAttribute("start", first + range[0]);
      }
    });
  }

  /* True when atom i must stay on the same slide as the atom before it. */
  function glued(atoms, i) {
    var atom = atoms[i];
    var before = atoms[i - 1];
    if (atom.block === before.block) {
      return false; // rows and list items may part
    }
    if (/^H[3-6]$/.test(before.block.tagName)) {
      return true; // a sub-heading stays with what it introduces
    }
    if (before.block.tagName === "P" && /:\s*$/.test(before.block.textContent)) {
      return true; // so does a lead-in sentence
    }
    // And a demo with its program, while the two sit side by side. Stacked
    // on a narrow window they are too tall to insist on.
    return deck.wide && atom.block.classList.contains(DEMO);
  }

  /* Split a slide's atoms into the parts that each fill one screen. */
  function paginate(slide) {
    var atoms = slide.atoms;
    var parts = [];
    var start = 0;
    if (atoms.length === 0) {
      return [[0, 0]];
    }
    while (start < atoms.length) {
      var end = start;
      while (end < atoms.length) {
        reveal(slide, start, end + 1);
        if (overflows()) {
          break;
        }
        end++;
      }
      if (end < atoms.length) {
        // Back up to the nearest place a break is allowed.
        var cut = end;
        while (cut > start && glued(atoms, cut)) {
          cut--;
        }
        if (cut === start) {
          // Nothing that fits may be separated: take the smallest group
          // anyway and let the fit step deal with it.
          cut = Math.max(end, start + 1);
          while (cut < atoms.length && glued(atoms, cut)) {
            cut++;
          }
        }
        end = cut;
      }
      parts.push([start, end]);
      start = end;
    }
    return parts;
  }

  /* Undo capBoxes, restoring each box's style attribute exactly. */
  function releaseBoxes() {
    deck.capped.forEach(function (box) {
      var style = deck.boxStyles.get(box);
      if (style === null) {
        box.removeAttribute("style");
      } else {
        box.setAttribute("style", style);
      }
    });
    deck.capped = [];
    deck.boxStyles = new Map();
  }

  function limitBoxes(boxes, height) {
    boxes.forEach(function (box) {
      if (box.tagName === "IFRAME") {
        // A demo is sized by an inline min-height; it scrolls inside its
        // own frame when given less.
        box.style.minHeight = "min(" + deck.frameHeights.get(box) + ", " + height + "px)";
      } else {
        box.style.maxHeight = height + "px";
      }
    });
  }

  /* Give the programs and demos on the slide one shared height limit, the
   * largest that makes the slide fit, and let them scroll inside their own
   * boxes. Returns false if even the minimum is not enough. */
  function capBoxes() {
    var found = deck.stage.querySelectorAll(
      "." + BLOCK_ON + " pre > code, ." + BLOCK_ON + ".drafter-demo iframe",
    );
    var boxes = [];
    var high = 0;
    for (var i = 0; i < found.length; i++) {
      var box = found[i];
      if (box.tagName === "IFRAME") {
        if (!box.style.minHeight) {
          continue;
        }
        deck.frameHeights.set(box, box.style.minHeight);
      }
      deck.boxStyles.set(box, box.getAttribute("style"));
      boxes.push(box);
      high = Math.max(high, box.clientHeight);
    }
    deck.capped = boxes;
    var low = MIN_BOX_HEIGHT;
    limitBoxes(boxes, low);
    if (boxes.length === 0 || high <= low || overflows()) {
      releaseBoxes();
      return false;
    }
    for (var step = 0; step < 10; step++) {
      var middle = (low + high) / 2;
      limitBoxes(boxes, middle);
      if (overflows()) {
        high = middle;
      } else {
        low = middle;
      }
    }
    limitBoxes(boxes, Math.floor(low));
    boxes.forEach(function (capped) {
      capped.scrollTop = 0;
    });
    return true;
  }

  /* The capped programs that still have lines out of sight. */
  function boxWithMore(below) {
    for (var i = 0; i < deck.capped.length; i++) {
      var box = deck.capped[below ? i : deck.capped.length - 1 - i];
      if (box.tagName !== "IFRAME" && (below ? hiddenBelow(box) : box.scrollTop > 2)) {
        return box;
      }
    }
    return null;
  }

  /* Choose the scale for the slide on screen. */
  function fit() {
    releaseBoxes();
    var scale = 1;
    setFit(scale);
    while (overflows() && scale - FIT_STEP >= MIN_FIT - 0.001) {
      scale = Math.round((scale - FIT_STEP) * 100) / 100;
      setFit(scale);
    }
    if (overflows()) {
      // Shrinking further would make the slide unreadable. Go back to a
      // comfortable size and scroll instead.
      setFit(SCROLL_FIT);
      capBoxes();
    }
    deck.stage.scrollTop = 0;
    updateMore();
  }

  function buildViews() {
    deck.base = parseFloat(getComputedStyle(deck.stage).getPropertyValue("--drafter-slides-base")) || 1;
    // Matches the two-column breakpoint in drafter-slides.css.
    deck.wide = window.matchMedia("screen and (min-width: 60em)").matches;
    releaseBoxes();
    setFit(SPLIT_FIT);
    deck.views = [];
    deck.slides.forEach(function (slide, s) {
      var parts = paginate(slide);
      parts.forEach(function (part, p) {
        deck.views.push({ slide: s, from: part[0], to: part[1], part: p, parts: parts.length });
      });
    });
  }

  /* The view that shows a given atom of a given slide. */
  function viewFor(slideIndex, atomIndex) {
    var fallback = 0;
    for (var i = 0; i < deck.views.length; i++) {
      var view = deck.views[i];
      if (view.slide !== slideIndex) {
        continue;
      }
      if (view.part === 0) {
        fallback = i;
      }
      if (atomIndex >= view.from && atomIndex < view.to) {
        return i;
      }
    }
    return fallback;
  }

  /* The view that shows a given element of the page. */
  function viewOf(element) {
    var block = element.closest ? element.closest("." + BLOCK) : null;
    if (!block && deck.folded.indexOf(element) !== -1) {
      // A folded opening heading stands for the text that follows it.
      block = element.nextElementSibling;
      while (block && !block.classList.contains(BLOCK)) {
        block = block.nextElementSibling;
      }
      element = block;
    }
    if (!block) {
      return -1;
    }
    for (var s = 0; s < deck.slides.length; s++) {
      var slide = deck.slides[s];
      if (slide.head.indexOf(block) !== -1) {
        return viewFor(s, 0);
      }
      for (var a = 0; a < slide.atoms.length; a++) {
        var atom = slide.atoms[a];
        if (atom.block === block && (!atom.item || element === block || atom.item.contains(element))) {
          return viewFor(s, a);
        }
      }
      if (slide.blocks.indexOf(block) !== -1) {
        return viewFor(s, 0);
      }
    }
    return -1;
  }

  function show(index) {
    deck.index = Math.max(0, Math.min(deck.views.length - 1, index));
    var view = deck.views[deck.index];
    var slide = deck.slides[view.slide];
    reveal(slide, view.from, view.to);
    deck.slides.forEach(function (other) {
      other.head.forEach(function (el) {
        if (other === slide && view.parts > 1) {
          el.setAttribute(PART, view.part + 1 + "/" + view.parts);
        } else {
          el.removeAttribute(PART);
        }
      });
    });
    fit();
    updateBar();
  }

  /* Lay the deck out again, staying on the content currently shown. */
  function relayout() {
    if (!deck) {
      return;
    }
    var view = deck.views[deck.index];
    var keepSlide = view ? view.slide : 0;
    var keepAtom = view ? view.from : 0;
    readPage();
    buildViews();
    show(viewFor(Math.min(keepSlide, deck.slides.length - 1), keepAtom));
  }

  /* ------------------------------------------------------------------ */
  /* Moving through the deck                                             */
  /* ------------------------------------------------------------------ */

  function hiddenBelow(el) {
    return el.scrollHeight - el.clientHeight - el.scrollTop > 2;
  }

  function next() {
    var scroller = boxWithMore(true);
    if (!scroller && hiddenBelow(deck.stage)) {
      scroller = deck.stage;
    }
    if (scroller) {
      scroller.scrollTop += scroller.clientHeight * PAGE_STEP;
      updateMore();
    } else if (deck.index < deck.views.length - 1) {
      show(deck.index + 1);
    } else if (deck.nextPage) {
      openPage(deck.nextPage.href);
    }
  }

  function previous() {
    var scroller = deck.stage.scrollTop > 2 ? deck.stage : boxWithMore(false);
    if (scroller) {
      scroller.scrollTop -= scroller.clientHeight * PAGE_STEP;
      updateMore();
    } else if (deck.index > 0) {
      show(deck.index - 1);
    }
  }

  function rememberResume() {
    try {
      sessionStorage.setItem(RESUME_KEY, "1");
    } catch (error) {
      // Storage can be unavailable; the next page then opens normally.
    }
  }

  function openPage(href) {
    rememberResume();
    window.location.assign(href);
  }

  /* ------------------------------------------------------------------ */
  /* Control bar                                                         */
  /* ------------------------------------------------------------------ */

  function buildBar() {
    bar = document.createElement("div");
    bar.className = "drafter-slides__bar";
    bar.setAttribute("role", "toolbar");
    bar.setAttribute("aria-label", "Slide controls");
    bar.hidden = true;
    bar.innerHTML =
      '<div class="drafter-slides__progress"><span></span></div>' +
      '<button type="button" class="drafter-slides__button" data-act="exit" title="Leave slide mode (Esc)">Exit</button>' +
      '<span class="drafter-slides__page"></span>' +
      '<div class="drafter-slides__nav">' +
      '<button type="button" class="drafter-slides__button" data-act="previous" aria-label="Previous slide">‹</button>' +
      '<button type="button" class="drafter-slides__button drafter-slides__count" data-act="outline" aria-haspopup="true" aria-expanded="false" title="Slide list (O)"></button>' +
      '<button type="button" class="drafter-slides__button" data-act="next" aria-label="Next slide">›</button>' +
      '<span class="drafter-slides__more" hidden>more below</span>' +
      '<div class="drafter-slides__outline" hidden></div>' +
      "</div>" +
      '<button type="button" class="drafter-slides__button" data-act="fullscreen" title="Full screen (F)">Full screen</button>';
    document.body.appendChild(bar);
    ui.progress = bar.querySelector(".drafter-slides__progress span");
    ui.page = bar.querySelector(".drafter-slides__page");
    ui.count = bar.querySelector(".drafter-slides__count");
    ui.more = bar.querySelector(".drafter-slides__more");
    ui.outline = bar.querySelector(".drafter-slides__outline");
    ui.fullscreen = bar.querySelector('[data-act="fullscreen"]');
    ui.fullscreen.hidden = !root.requestFullscreen;
    var actions = {
      exit: exit,
      previous: previous,
      next: next,
      outline: function () {
        toggleOutline();
      },
      fullscreen: toggleFullscreen,
    };
    bar.addEventListener("click", function (event) {
      var button = event.target.closest("[data-act]");
      if (button && deck) {
        actions[button.getAttribute("data-act")]();
      }
    });
  }

  function outlineEntry(tag, mark, text) {
    var entry = document.createElement(tag);
    var number = document.createElement("span");
    number.className = "drafter-slides__outline-number";
    number.textContent = mark;
    entry.appendChild(number);
    entry.appendChild(document.createTextNode(text));
    return entry;
  }

  function buildOutline() {
    ui.outline.textContent = "";
    deck.slides.forEach(function (slide, s) {
      if (slide.end) {
        return;
      }
      var entry = outlineEntry("button", String(s + 1), slide.title);
      entry.type = "button";
      entry.setAttribute("data-slide", s);
      entry.addEventListener("click", function (event) {
        event.stopPropagation();
        toggleOutline(false);
        show(viewFor(s, 0));
      });
      ui.outline.appendChild(entry);
    });
    var pages = [
      [deck.previousPage, "←", "Previous page: "],
      [deck.nextPage, "→", "Next page: "],
    ];
    var ruled = false;
    pages.forEach(function (page) {
      if (!page[0]) {
        return;
      }
      if (!ruled) {
        ui.outline.appendChild(document.createElement("hr"));
        ruled = true;
      }
      var link = outlineEntry("a", page[1], page[2] + page[0].title);
      link.href = page[0].href;
      link.addEventListener("click", rememberResume);
      ui.outline.appendChild(link);
    });
  }

  function toggleOutline(open) {
    if (open === undefined) {
      open = ui.outline.hidden;
    }
    ui.outline.hidden = !open;
    ui.count.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function updateMore() {
    if (!deck) {
      return;
    }
    ui.more.hidden = !(hiddenBelow(deck.stage) || boxWithMore(true));
  }

  function updateBar() {
    var view = deck.views[deck.index];
    var slide = deck.slides[view.slide];
    var total = deck.slides.length - 1; // the end card is not counted
    var label = slide.end ? "End of page" : "Slide " + (view.slide + 1) + " of " + total;
    if (view.parts > 1) {
      label += " (" + (view.part + 1) + "/" + view.parts + ")";
    }
    ui.count.textContent = label;
    var done = deck.views.length > 1 ? deck.index / (deck.views.length - 1) : 1;
    ui.progress.style.width = done * 100 + "%";
    var entries = ui.outline.querySelectorAll("[data-slide]");
    for (var i = 0; i < entries.length; i++) {
      var here = Number(entries[i].getAttribute("data-slide")) === view.slide;
      entries[i].setAttribute("aria-current", here ? "true" : "false");
    }
  }

  function toggleFullscreen() {
    var request;
    if (document.fullscreenElement) {
      request = document.exitFullscreen();
    } else if (root.requestFullscreen) {
      request = root.requestFullscreen();
      deck.ownsFullscreen = true;
    }
    if (request && request.catch) {
      request.catch(function () {});
    }
  }

  /* ------------------------------------------------------------------ */
  /* Entering and leaving                                                */
  /* ------------------------------------------------------------------ */

  function neighbour(selector) {
    var link = document.querySelector(selector);
    if (!link || !link.getAttribute("href")) {
      return null;
    }
    var title = (link.getAttribute("aria-label") || "").replace(/^[^:]*:\s*/, "");
    if (!title) {
      var text = link.querySelector(".md-ellipsis");
      title = text ? text.textContent.trim() : link.href;
    }
    return { href: link.href, title: title };
  }

  function buildEndCard() {
    var card = document.createElement("div");
    card.className = "drafter-slides__end";
    var label = document.createElement("p");
    label.className = "drafter-slides__end-label";
    label.textContent = "End of this page";
    var title = document.createElement("p");
    title.className = "drafter-slides__end-title";
    var heading = deck.stage.querySelector("h1");
    title.textContent = heading ? headingText(heading) : document.title;
    var actions = document.createElement("div");
    actions.className = "drafter-slides__end-actions";
    if (deck.nextPage) {
      var onward = document.createElement("a");
      onward.className = "md-button md-button--primary";
      onward.href = deck.nextPage.href;
      onward.textContent = "Next: " + deck.nextPage.title;
      onward.addEventListener("click", rememberResume);
      actions.appendChild(onward);
    }
    if (deck.previousPage) {
      var back = document.createElement("a");
      back.className = "md-button";
      back.href = deck.previousPage.href;
      back.textContent = "Previous: " + deck.previousPage.title;
      back.addEventListener("click", rememberResume);
      actions.appendChild(back);
    }
    var restart = document.createElement("button");
    restart.type = "button";
    restart.className = "md-button";
    restart.textContent = "Back to the first slide";
    restart.addEventListener("click", function () {
      show(0);
    });
    actions.appendChild(restart);
    card.appendChild(label);
    card.appendChild(title);
    card.appendChild(actions);
    return card;
  }

  /* The block the reader is looking at, so the deck can open there. */
  function readingPosition(stage) {
    if (window.scrollY < 40) {
      return null;
    }
    var header = document.querySelector(".md-header");
    var top = (header ? header.getBoundingClientRect().bottom : 0) + 48;
    var candidates = stage.querySelectorAll(
      ":scope > h1, :scope > h2, :scope > p, :scope > ul, :scope > ol, :scope > div, :scope > table, :scope > details, :scope > blockquote",
    );
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i].getBoundingClientRect().bottom > top) {
        return candidates[i];
      }
    }
    return null;
  }

  function enter() {
    if (deck) {
      return;
    }
    var stage = document.querySelector("article.md-content__inner");
    if (!stage) {
      return;
    }
    if (!bar) {
      buildBar();
    }
    var reading = readingPosition(stage);
    deck = {
      stage: stage,
      opener: document.activeElement,
      scrollY: window.scrollY,
      starts: new Map(),
      items: new Map(),
      blocks: [],
      folded: [],
      slides: [],
      views: [],
      index: 0,
      base: 1,
      fit: 1,
      capped: [],
      boxStyles: new Map(),
      frameHeights: new Map(),
      endCard: null,
      ownsFullscreen: false,
      previousPage: neighbour(".md-footer__link--prev"),
      nextPage: neighbour(".md-footer__link--next"),
    };
    deck.endCard = buildEndCard();
    stage.appendChild(deck.endCard);

    root.classList.add("drafter-slides");
    stage.classList.add("drafter-slides__stage");
    stage.setAttribute("tabindex", "-1");
    bar.hidden = false;
    ui.page.textContent = deck.endCard.querySelector(".drafter-slides__end-title").textContent;

    readPage();
    buildViews();
    buildOutline();
    var start = reading ? viewOf(reading) : 0;
    deck.startSlide = deck.views[Math.max(0, start)].slide;
    show(Math.max(0, start));
    stage.focus({ preventScroll: true });
  }

  function exit() {
    if (!deck) {
      return;
    }
    var stage = deck.stage;
    var slideIndex = deck.views[deck.index].slide;
    if (deck.slides[slideIndex].end && slideIndex > 0) {
      slideIndex--;
    }
    var landing = deck.slides[slideIndex].head[0] || deck.slides[slideIndex].blocks[0];
    var moved = slideIndex !== deck.startSlide;
    var leaving = deck;

    toggleOutline(false);
    if (leaving.ownsFullscreen && document.fullscreenElement) {
      var request = document.exitFullscreen();
      if (request && request.catch) {
        request.catch(function () {});
      }
    }
    clearTags();
    leaving.endCard.remove();
    stage.classList.remove("drafter-slides__stage");
    stage.style.removeProperty("--drafter-slides-zoom");
    if (!stage.getAttribute("style")) {
      stage.removeAttribute("style");
    }
    stage.removeAttribute("tabindex");
    stage.scrollTop = 0;
    root.classList.remove("drafter-slides");
    bar.hidden = true;
    deck = null;

    // Put the reader back in the page where the deck stopped.
    if (moved && landing && landing.isConnected) {
      landing.scrollIntoView({ block: "start" });
    } else {
      window.scrollTo(0, leaving.scrollY);
    }
    if (leaving.opener && leaving.opener.focus) {
      leaving.opener.focus({ preventScroll: true });
    }
  }

  /* ------------------------------------------------------------------ */
  /* Events                                                              */
  /* ------------------------------------------------------------------ */

  function onKeydown(event) {
    if (!deck || event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }
    var target = event.target;
    var within = function (selector) {
      return target && target.closest ? target.closest(selector) : null;
    };
    // Typing in a demo's editor or any other field is left entirely alone.
    if (within("input, textarea, select, [contenteditable='true']")) {
      return;
    }
    var key = event.key;
    var handled = true;
    if (key === "Escape") {
      if (ui.outline.hidden) {
        exit();
      } else {
        toggleOutline(false);
      }
    } else if (key === "ArrowRight" || key === "PageDown") {
      next();
    } else if (key === "ArrowLeft" || key === "PageUp") {
      previous();
    } else if (key === " " && !within("button, a, summary, label")) {
      if (event.shiftKey) {
        previous();
      } else {
        next();
      }
    } else if (key === "Home") {
      show(0);
    } else if (key === "End") {
      show(deck.views.length - 1);
    } else if (key === "o" || key === "O") {
      toggleOutline();
    } else if (key === "f" || key === "F") {
      toggleFullscreen();
    } else {
      handled = false;
    }
    if (handled) {
      event.preventDefault();
    }
    // The theme binds single keys to search and page navigation. Keep them
    // from firing behind the slides.
    if (handled || key.length === 1) {
      event.stopPropagation();
    }
  }

  var relayoutTimer = 0;
  function scheduleRelayout() {
    if (!deck) {
      return;
    }
    clearTimeout(relayoutTimer);
    relayoutTimer = setTimeout(relayout, 120);
  }

  /* Content that changes height after the slide is shown: a picture or demo
   * finishing loading, a collapsed block being opened, a tab switch. */
  var refitFrame = 0;
  function scheduleRefit(event) {
    if (!deck || !deck.stage.contains(event.target)) {
      return;
    }
    cancelAnimationFrame(refitFrame);
    refitFrame = requestAnimationFrame(function () {
      if (deck) {
        fit();
      }
    });
  }

  function onHashChange() {
    if (!deck) {
      return;
    }
    var id = decodeURIComponent(window.location.hash.slice(1));
    var target = id ? document.getElementById(id) : null;
    var index = target ? viewOf(target) : -1;
    if (index !== -1) {
      show(index);
    }
  }

  function addHeaderButton() {
    var header = document.querySelector(".md-header__inner");
    if (!header || header.querySelector(".drafter-slides-open") || !document.querySelector("article.md-content__inner")) {
      return;
    }
    var button = document.createElement("button");
    button.type = "button";
    button.className = "md-header__button md-icon drafter-slides-open";
    button.title = "Present this page as slides";
    button.setAttribute("aria-label", "Present this page as slides");
    button.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M3 4h18v12H3z M5 6v8h14V6z M11 16h2v3h3v2H8v-2h3z"/></svg>';
    button.addEventListener("click", enter);
    var before =
      header.querySelector(".md-header__option") ||
      header.querySelector('label[for="__search"]');
    if (before && before.parentNode === header) {
      header.insertBefore(button, before);
    } else {
      header.appendChild(button);
    }
  }

  function setup() {
    addHeaderButton();
    document.addEventListener("keydown", onKeydown, true);
    window.addEventListener("resize", scheduleRelayout);
    document.addEventListener("fullscreenchange", function () {
      if (ui.fullscreen) {
        ui.fullscreen.textContent = document.fullscreenElement ? "Exit full screen" : "Full screen";
      }
      scheduleRelayout();
    });
    // Tables are wrapped by the theme's own script, which may finish after
    // a resumed deck has opened.
    window.addEventListener("load", scheduleRelayout);
    window.addEventListener("hashchange", onHashChange);
    document.addEventListener("load", scheduleRefit, true);
    document.addEventListener("toggle", scheduleRefit, true);
    document.addEventListener("change", scheduleRefit, true);
    document.addEventListener("scroll", updateMore, true);

    var resume = false;
    try {
      resume = sessionStorage.getItem(RESUME_KEY) === "1";
      sessionStorage.removeItem(RESUME_KEY);
    } catch (error) {
      resume = false;
    }
    if (resume) {
      // After the theme's own startup work for this page.
      setTimeout(enter, 0);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
