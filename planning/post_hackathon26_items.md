# Showstoppers

- [X] If you run a file without saving, it will run a crashed site. This is what happens basically by default in thonny.
- [X] If you save in the top-level directory, it starts recursively watching all files on your entire hard drive. This also causes an infinite loop. (Watch policy with safety checks + safe mode; see watch_* settings in AppServerConfiguration.)
- [ ] The table example does not work
- [ ] Tables should support numbers
- [ ] Table is weird when there is a button inside. Looks like there might be some empty space or something?
- [ ] Pressing back arrow in browser goes to previous interactive code, not previous page in documentation. We should add a flag to disable the History feature, and then disable it in the documentation.
- [X] Semicolons have to be escaped to be used on shells, so they shouldn't be used as the separators
- [ ] Load packages automatically prevents explicit package list
- [ ] Pilgram was not being inferred automatically
- [ ] The letter "B" is broken in documentation search (not sure why that letter in particular)
- [ ] The import js should work at the top level. It can still error if you try to call anything outside of pyodide, but just importing it shouldn't break anything.
- [ ] Present breadcrumbs better when showing where errors are in Pages' content.

# Nice
- [ ] There should be a way to reset the timer examples; they'll already be done by the time you scroll down to the bottom of the page.
- [ ] When there is a route name mismatch via a button, the error says "link" instead
- [ ] There is a need for a "nothing" component, so student can return a blank space. That way we can alow primitive type without none/null support.
- [ ] Make links on documentation more noticeable - i.e., reference
- [ ] Remove warning for "The form field ____" was sent to "___" but the function has no matching
- [ ] Need a reset code button in the documentation so students can return to default code for the example
- [ ] Need to document the placeholder attribute for textbox in the documentation


# Cosmetic

- [ ] Almond theme (and possibly others): shows frame right up against side, but not when deployed
- [ ] Applying the "almond" theme correctly in code visually changes the site correctly, but it also produces a "could not apply the new theme..." error in the debug panel.
- [ ] Reloading shows the old pre-compiled template while it's reloading, because nothing has changed it.
- [ ] Add a file example so that they can download a txt file to text upload
- [ ] The image example should use a cat or something
- [ ] Need a way to lock zooming in/out for the Map
- [ ] In the leaflet maps, provide a way for the user to get the color of the tile at the latitude and longitude
- [ ] Need method of intercepting live video frames from the camera stream
- [ ] Add "@" to headers in docs for route page, so that it's easier to find

- [ ] The documentation bar at the side the scroll is red and orange instead of blue
- [ ] The vscode docs inline will show true docs instead of the simplified docs

# Somewhat vague - needs more investigation

- [ ] The current table error looks bad.
- [ ] The water theme causes the console debug to generate in drafter
- [ ] CurrentLocation was failing on a Mac laptop

# Bugs that might be impossible to fix

