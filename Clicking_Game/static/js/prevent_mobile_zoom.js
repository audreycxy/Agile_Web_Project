/*
  Prevent unwanted mobile double-tap zoom on rapid-tap game controls.

  CSS touch-action: manipulation is the first layer of protection.
  This script adds a safer fallback for mobile browsers where rapid tapping
  may still trigger double-tap zoom during the clicking game.

  It only applies to game-related tap targets, so normal page gestures are
  affected as little as possible.
*/

(function () {
  let lastTouchEndAt = 0;

  const rapidTapSelector = [
    "#egg-btn",
    "#demoEggButton",
    ".demo-egg-button",
    "#clickpower-btn",
    "#autoclicker-btn",
    "#prev-egg",
    "#next-egg-btn",
  ].join(",");

  document.addEventListener(
    "touchend",
    function (event) {
      const target = event.target.closest(rapidTapSelector);

      if (!target) {
        return;
      }

      const now = Date.now();

      if (now - lastTouchEndAt <= 350) {
        event.preventDefault();
      }

      lastTouchEndAt = now;
    },
    { passive: false },
  );
})();
