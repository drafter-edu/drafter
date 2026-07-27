---
page_type: how-to
title: Get feedback on your design
level: L2
audience: S
priority: P1
prereqs: [your-project/deploy/github-pages]
symbols: []
outcome: Learn how real users experience your app and what to change.
---

# Get feedback on your design

## Goal

Your app is live and you have a link. Now you want to know the thing you
cannot know alone: what it is like for someone who is not you to use it,
and what to improve.

## Before you start

You need your deployed URL and one willing person: a friend, a roommate,
a family member, a classmate. Someone who has never seen the app is
worth more than someone who watched you build it. You do not need many:
watching just three to five people will surface most of the problems
worth fixing.

## Watch, do not guide

The single most useful thing you can do is **watch someone use your app
without helping them**. Hand over the link, give them a real task in
plain words ("order a snack for a dog", "take the quiz and find your
score"), and then be quiet.

- **Do not touch, point, or hint.** The moment you say "click the blue
  button", you have hidden a problem your app has.
- **Let silence and confusion happen.** Where they hesitate, squint, or
  click the wrong thing, your app is unclear. That is exactly the
  information you came for.
- **If they get truly stuck**, note where, then rescue them. The stuck
  point goes to the top of your fix list.

It will be uncomfortable. Watching someone struggle with a thing you
made always is. The discomfort is the feedback working.

## Ask questions that do not lead

After the task, ask open questions and let them talk:

- "What did you expect to happen when you clicked that?"
- "What was confusing?"
- "What would you change first?"
- "In one sentence, what does this app do?"

Avoid questions that beg for kindness: "Do you like it?" and "It's
good, right?" produce polite noise, not information. If their one
sentence about what the app does is not what you intended, that is a
finding, and probably about your front page's text.

## Take notes, then look for patterns

Write down what happened while it happens, in their words, not yours:
"clicked the title expecting to go home", "did not see the Save
button", "asked what the number meant". After a few testers, patterns
appear. One person missing a button is a person; three people missing
it is a design problem.

Sort what you saw into three piles:

1. **Blockers**: someone could not finish the task. Fix these first.
2. **Confusions**: they finished, but hesitated or went the wrong way
   first. Fix what repeats.
3. **Wishes**: "it would be nice if...". Save these for
   [adding features](add-features.md), one at a time; do not chase
   every wish.

## Fix, redeploy, and close the loop

Make the top fixes, [redeploy](deploy/github-pages.md#updating-a-deployed-site),
and, when you can, show the fix to the person who hit the problem. It
verifies the fix actually works, and testers who see their feedback
mattered will gladly test for you again.

Finally, **thank your testers**. If your course has a place for credits,
your app's about page from
[Prepare for release](deploy/prepare.md) is a fitting spot to mention
them.

## Common problems

- **Everyone just says it is nice**: you asked yes/no questions, or they
  watched you demo it instead of driving. Give them the link, a task,
  and silence.
- **One tester wants to redesign everything**: one strong opinion is a
  data point, not a mandate. Wait for patterns.
- **Feedback contradicts itself**: it will. Prefer what you *watched
  people do* over what they *said*, and blockers over wishes.
- **You feel defensive**: normal. Write the note anyway; you are
  collecting facts about the app, not verdicts about you. Designing things requires
  you to put your heart into something that will be judged. That is the point of design: to make something that works for other people, not just you. Try not to take it personally, and remember that the feedback is about the app, not you. If necessary, take a break, eat your favorite snack (I recommend m&ms), and come back to the notes later with fresh eyes.

## Understand it

[Improve the design](improve-the-design.md): turning findings into a
usability and styling pass.

## See another example

The [project gallery](gallery/index.md) entries each note what makes
them pleasant to use; compare their choices against your findings.

## Look it up

[Add features one at a time](add-features.md) for working through the
wish list, and [Test as you go](test-as-you-go.md) so fixes stay fixed.

## Fix a problem

If a tester hits an actual error, the
[error index](../help/errors/index.md) explains it; ask them for a
screenshot of the exact message.
