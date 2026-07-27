---
page_type: how-to
title: Improve the design
level: L2
audience: S
priority: P2
prereqs: [your-project/add-features]
symbols: []
outcome: Make the app pleasant and usable.
---

# Improve the design

## Goal

The features work; now the app should feel finished. This step is
two passes: a usability pass (can a stranger use it without you
explaining?) and a styling pass (does it look cared for?). In
that order, because a beautiful page that confuses people is
still a failed page.

## Before you start

All required features work and their tests are green. That
matters because design work touches many pages quickly, and the
tests are what tell you a cosmetic change stayed cosmetic.

## The usability pass

Walk your own app pretending to be a first-time visitor, page by
page, asking five questions:

- **Labels**: does every input say what belongs in it, and every
  button say what it will do? "Submit" tells a visitor nothing;
  "Add to log" does.
- **Order**: does each page read top to bottom in the order the
  visitor should look? The main action belongs where the reading
  flow ends, not buried above explanatory text.
- **Empty states**: open every page with a fresh state. A blank
  table with no explanation reads as broken; "No hikes logged
  yet. Add your first one below." reads as working software.
- **Error paths**: type something wrong in every field. Your app
  should respond with a polite page that says what to fix, not
  with silence and not with a raw error.
- **Dead ends**: from every page, can the visitor get back to the
  main page without the browser's back button? Add the missing
  links.

Fix what the walk finds before touching colors. These fixes are
ordinary route edits, and your tests will confirm nothing else
moved. When you can, watch someone else take the same walk; the
[Get feedback](get-feedback.md) step makes that formal, and doing
a small version now catches the worst confusions early.

## The styling pass

Work from big decisions to small ones, and stop while it still
looks calm:

1. **Pick a theme** from the
   [theme catalog](../reference/themes.md) that matches your
   app's mood. One line of code restyles everything, and for many
   apps the right theme is the whole styling pass.
2. **Fix what the theme got wrong** with targeted
   [styling helpers](../add/change-appearance/helpers.md): the
   too-cramped table, the button that should stand out, the
   header that needs air. A handful of targeted changes, each
   with a reason.
3. **Check readability**: dark-enough text on light-enough
   backgrounds, nothing meaningful carried by color alone, and
   text sizes that survive being read on a phone.
   [Design basics](../add/change-appearance/design-basics.md)
   covers the rules of thumb.

Restraint reads as skill. One theme, one accent color, and
consistent spacing beat six fonts every time; when in doubt,
remove a decoration rather than add one.

## Before and after

The difference the two passes make is usually visible in one
screenshot pair: same features, but labels that explain, an empty
state that reassures, and one theme applied consistently. The
[Finishing tutorial](../tutorials/finishing.md) walks a complete
example of exactly this transformation if you want to see the
moves demonstrated.

## Common problems

- **The theme broke my custom styling**: themes carry their own
  opinions. Apply the theme first, then re-add the targeted
  styles that still matter;
  [styling gotchas](../add/change-appearance/gotchas.md) explains
  the interaction.
- **Restyling changed a test result**: loose `assert_has` tests
  ignore styling, but frozen whole-page tests include it.
  Re-freeze the pages you deliberately restyled.
- **It looks fine on my laptop and cramped on a phone**: avoid
  fixed pixel widths on content; let text wrap. Test once in a
  narrow browser window.
- **Endless fiddling**: styling has no natural stopping point.
  Time-box the pass, make the changes you can name a reason for,
  and ship.

## You are ready for the next step when

A person who has never seen the app can complete its main task
without help, every page has a sensible empty state, and the
styling follows one consistent scheme you chose on purpose. Time
to [deploy and submit](deploy/index.md).
