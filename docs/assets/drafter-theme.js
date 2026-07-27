/* Drafter docs theme behavior.
 *
 * The "More" dropdown in the header opens on hover/focus via CSS, but that
 * gives no affordance for clicks or touch. This toggles it on click, closes
 * it on outside click or Escape, and keeps aria-expanded in sync.
 */
(function () {
  function setup() {
    var more = document.querySelector(".drafter-more");
    if (!more) {
      return;
    }
    var button = more.querySelector(".drafter-more__button");

    function setOpen(open) {
      more.classList.toggle("drafter-more--open", open);
      button.setAttribute("aria-expanded", open ? "true" : "false");
    }

    button.setAttribute("aria-expanded", "false");
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      setOpen(!more.classList.contains("drafter-more--open"));
    });
    document.addEventListener("click", function (event) {
      if (!more.contains(event.target)) {
        setOpen(false);
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
