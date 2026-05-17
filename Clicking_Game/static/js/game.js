(function () {
  // INITIALISATION

  // Egg Order
  const EGG_ORDER = [
    "standard",
    "water",
    "fire",
    "grass",
    "steel",
    "standard-bronze",
    "water-bronze",
    "fire-bronze",
    "grass-bronze",
    "steel-bronze",
    "standard-silver",
    "water-silver",
    "fire-silver",
    "grass-silver",
    "steel-silver",
    "standard-gold",
    "water-gold",
    "fire-gold",
    "grass-gold",
    "steel-gold",
    "gold",
  ];

  // Game State
  let gameState = {
    totalPoints: INITIAL_STATE.points,
    currentInfinityLevel: INITIAL_STATE.current_infinity_level,
    currentType: INITIAL_STATE.current_type,
    highestType: INITIAL_STATE.highest_type,
    clicksRemaining:
      INITIAL_STATE.clicks_remaining ??
      EGG_CONFIG[INITIAL_STATE.current_type].base_clicks,
    progressPercent: INITIAL_STATE.progress_percent,
    isGuest: INITIAL_STATE.is_guest,
    clickPower: INITIAL_STATE.click_power_lvl,
    autoClickerPower: INITIAL_STATE.autoclicker_lvl,
  };

  let isAnimating = false;
  let isSyncing = false;
  let hasShownForcedLogoutAlert = false;
  let hasShownGameLockAlert = false;
  let ownsGameLock = false;
  let lockHeartbeatHandle = null;

  let lastManualClickTime = 0;
  // 50ms minimum gap between manual clicks. A human's fastest sustainable
  // click rate is ~10-12 cps (~80-100ms apart). Anything tighter than 50ms
  // is almost certainly a macro / auto-clicker, so we drop those clicks.
  const CLICK_DEBOUNCE = 50;
  // Auto-clicker only fires while the player has interacted within the last
  // 30 seconds. Prevents idle farming (leave the tab open all night for
  // free points).
  const AUTO_CLICKER_IDLE_TIMEOUT = 30000;
  const GAME_LOCK_KEY = `eggClicker:activeGameTab:${GAME_LOCK_SCOPE}`;
  const GAME_LOCK_TAB_ID_KEY = "eggClickerGameTabId";
  const GAME_LOCK_TIMEOUT = 10000;
  const GAME_LOCK_HEARTBEAT_INTERVAL = 3000;
  const GAME_LOCK_CONFLICT_MESSAGE = gameState.isGuest
    ? "This game is already open in another tab. Return to the existing game tab to continue."
    : "This account is already playing in another game tab. Return to the existing tab to continue.";

  let isWindowFocused = document.hasFocus();
  let lastPlayerActivityTime = Date.now();
  const gameTabId = getOrCreateGameTabId();

  function getOrCreateGameTabId() {
    const existingTabId = sessionStorage.getItem(GAME_LOCK_TAB_ID_KEY);

    if (existingTabId) {
      return existingTabId;
    }

    const newTabId =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `tab-${Date.now()}-${Math.random().toString(36).slice(2)}`;

    sessionStorage.setItem(GAME_LOCK_TAB_ID_KEY, newTabId);
    return newTabId;
  }

  function readGameLock() {
    const rawLock = localStorage.getItem(GAME_LOCK_KEY);

    if (!rawLock) {
      return null;
    }

    try {
      return JSON.parse(rawLock);
    } catch (_error) {
      return null;
    }
  }

  function isGameLockStale(lock) {
    return !lock || typeof lock.lastSeen !== "number" || Date.now() - lock.lastSeen > GAME_LOCK_TIMEOUT;
  }

  function writeGameLock() {
    localStorage.setItem(
      GAME_LOCK_KEY,
      JSON.stringify({
        tabId: gameTabId,
        lastSeen: Date.now(),
      }),
    );
  }

  function releaseGameLock() {
    if (!ownsGameLock) {
      return;
    }

    const currentLock = readGameLock();

    if (currentLock?.tabId === gameTabId) {
      localStorage.removeItem(GAME_LOCK_KEY);
    }

    ownsGameLock = false;

    if (lockHeartbeatHandle !== null) {
      clearInterval(lockHeartbeatHandle);
      lockHeartbeatHandle = null;
    }
  }

  function exitBecauseGameLockLost() {
    if (hasShownGameLockAlert) {
      return;
    }

    hasShownGameLockAlert = true;
    releaseGameLock();
    alert(GAME_LOCK_CONFLICT_MESSAGE);
    window.location.assign(GAME_LOCK_REDIRECT_URL);
  }

  function maintainGameLock() {
    if (!ownsGameLock) {
      return;
    }

    const currentLock = readGameLock();

    if (currentLock && currentLock.tabId !== gameTabId && !isGameLockStale(currentLock)) {
      exitBecauseGameLockLost();
      return;
    }

    writeGameLock();
  }

  function tryAcquireGameLock() {
    const currentLock = readGameLock();

    if (currentLock && currentLock.tabId !== gameTabId && !isGameLockStale(currentLock)) {
      return false;
    }

    writeGameLock();
    const confirmedLock = readGameLock();
    ownsGameLock = confirmedLock?.tabId === gameTabId;

    if (!ownsGameLock) {
      return false;
    }

    if (lockHeartbeatHandle !== null) {
      clearInterval(lockHeartbeatHandle);
    }

    lockHeartbeatHandle = setInterval(maintainGameLock, GAME_LOCK_HEARTBEAT_INTERVAL);
    return true;
  }

  function markPlayerActive() {
    lastPlayerActivityTime = Date.now();
  }

  // When the server tells us this session is no longer valid (typically
  // because the user logged in again from another device, which rotates
  // their active_session_token on the server), we kick them back to the
  // login page. The `hasShownForcedLogoutAlert` flag stops us spamming the
  // alert when multiple in-flight requests all return 401 at the same time.
  function forceLogout(message, redirectUrl = "/login") {
    if (hasShownForcedLogoutAlert) {
      return;
    }

    hasShownForcedLogoutAlert = true;
    alert(message || "Your session has ended. Please log in again.");
    window.location.assign(redirectUrl);
  }

  function fetchGameJson(url, options) {
    return fetch(url, options).then(async (response) => {
      const data = await response.json().catch(() => null);

      // 401 means the server has invalidated our session (single-session
      // enforcement). Bail out of the request and redirect the user before
      // the rest of the click handler can act on stale state.
      if (response.status === 401) {
        forceLogout(data?.message, data?.redirect_url);
        throw new Error(data?.message || "Authentication required.");
      }

      if (data === null) {
        throw new Error("Invalid server response.");
      }

      return data;
    });
  }

  // Four gates protect against AFK farming with an auto-clicker:
  //   1. autoClickerPower > 0   -> they actually own the upgrade
  //   2. !document.hidden       -> tab is currently visible
  //   3. isWindowFocused        -> window has OS focus
  //   4. recent activity        -> they've moved the mouse / typed / tapped
  //                                in the last AUTO_CLICKER_IDLE_TIMEOUT ms
  // All four must hold, otherwise the auto-clicker pauses.
  function isAutoClickerAllowed() {
    return (
      ownsGameLock &&
      gameState.autoClickerPower > 0 &&
      !document.hidden &&
      isWindowFocused &&
      Date.now() - lastPlayerActivityTime <= AUTO_CLICKER_IDLE_TIMEOUT
    );
  }

  function handleEggClick(damageAmount = null) {
    if (!ownsGameLock) return;
    if (isAnimating || isSyncing) return;

    if (damageAmount !== null && !isAutoClickerAllowed()) {
      return;
    }

    // Rejects sub-50ms manual clicks to prevent external macro exploitation:
    if (damageAmount === null) {
      const currentTime = Date.now();
      if (currentTime - lastManualClickTime < CLICK_DEBOUNCE) {
        return;
      }

      lastManualClickTime = currentTime;
      markPlayerActive();
    }

    // Injected clicks via handleEggClick(X) using a browser breakpoint will be treated as (standard) auto-clicks:
    const expectedAutoDamage = gameState.autoClickerPower === 1 ? 1 : gameState.autoClickerPower * 2;

    const clickDamage = gameState.clickPower === 1 ? 1 : gameState.clickPower * 3;
    const damage = damageAmount !== null ? expectedAutoDamage : clickDamage;

    gameState.clicksRemaining -= damage;

    updateProgressUI();

    if (gameState.clicksRemaining <= 0) {
      gameState.clicksRemaining = 0;
      isSyncing = true;

      const earned = calculateReward();
      gameState.totalPoints += earned;

      const eggKeys = EGG_ORDER;
      const nextIndex = eggKeys.indexOf(gameState.currentType) + 1;

      // If the current egg is not the last egg, set the current egg as the next egg:
      if (gameState.currentType !== eggKeys[eggKeys.length - 1]) {
        if (gameState.highestType == gameState.currentType) {
          gameState.highestType = eggKeys[nextIndex];
        }
        gameState.currentType = eggKeys[nextIndex];
      }

      gameState.clicksRemaining = EGG_CONFIG[gameState.currentType].base_clicks;

      if (!gameState.isGuest) {
        fetchGameJson("/api/sync", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
              .content,
          },
          body: JSON.stringify({}),
        })
          .then((data) => {
            if (data.status === "success") {
              gameState.totalPoints = data.new_points;
              gameState.currentType = data.current_type;
              gameState.highestType = data.highest_type;
              gameState.clicksRemaining = data.clicks_remaining;

              isSyncing = false;

              updatePointsUI();
              updateProgressUI();
              updateUpgradeUI();
            } else {
              isSyncing = false;
              console.error("Sync failed:", data.error);
            }
          })
          .catch((err) => {
            isSyncing = false;
            console.error("Sync failed:", err);
          });
      } else {
        isSyncing = false;

        updatePointsUI();
        updateProgressUI();
        updateUpgradeUI();
      }

      updateProgressUI();
      triggerEggBreak();
    }
  }

  function calculateReward() {
    const level = 1;
    const egg = EGG_CONFIG[gameState.currentType];

    return Math.floor(egg.base_points * level);
  }

  function updatePointsUI() {
    document.getElementById("egg-points").innerText = formatPoints(gameState.totalPoints);
  }

  function updateProgressUI() {
    const requiredClicks = EGG_CONFIG[gameState.currentType].base_clicks;
    const percentage =
      ((requiredClicks - gameState.clicksRemaining) / requiredClicks) * 100;
    const barWidth = Math.min(Math.max(percentage, 0), 100);

    document.getElementById("progress-bar").style.width = `${barWidth}%`;
    document.getElementById("click-count").innerText =
      `${gameState.clicksRemaining}/${requiredClicks} left`;
  }

  function updateEggImage() {
    const eggImages = document.querySelectorAll(".egg-image");

    eggImages.forEach((eggImage) => {
      eggImage.style.backgroundImage = `url('${EGG_CONFIG[gameState.currentType].image}')`;
    });

    document.getElementById("egg-type-display").innerText =
      EGG_CONFIG[gameState.currentType].name;
  }

  function triggerEggBreak() {
    isAnimating = true;

    const main = document.getElementById("main-egg");
    const top = document.getElementById("top-half");
    const bottom = document.getElementById("bottom-half");
    const next = document.getElementById("next-egg");

    next.style.backgroundImage = `url('${EGG_CONFIG[gameState.currentType].image}')`;

    const setBreakingMode = (isBreaking) => {
      const displayState = isBreaking ? "block" : "none";

      main.style.display = isBreaking ? "none" : "block";
      top.style.display = displayState;
      bottom.style.display = displayState;
      next.style.display = displayState;
    };

    setBreakingMode(true);

    void top.offsetHeight;

    top.classList.add("cracked-top");
    bottom.classList.add("cracked-bottom");
    next.classList.add("reveal-egg");

    setTimeout(() => {
      setBreakingMode(false);

      top.classList.remove("cracked-top");
      bottom.classList.remove("cracked-bottom");
      next.classList.remove("reveal-egg");

      isAnimating = false;
      updateEggImage();
    }, 600);
  }

  function changeEgg(direction) {
    if (!ownsGameLock) return;

    const eggKeys = EGG_ORDER;
    const nextIndex = eggKeys.indexOf(gameState.currentType) + direction;
    const highestIndex = eggKeys.indexOf(gameState.highestType);

    // Block passage to next egg if it's locked or doesn't exist:
    if (nextIndex < 0 || nextIndex > highestIndex) {
      return;
    }

    if (
      gameState.clicksRemaining <
      EGG_CONFIG[gameState.currentType].base_clicks &&
      gameState.clicksRemaining > 0
    ) {
      const confirmed = confirm(
        "Are you sure? Progress on this egg will be reset!",
      );

      if (!confirmed) {
        return;
      }
    }

    gameState.currentType = eggKeys[nextIndex];
    gameState.clicksRemaining = EGG_CONFIG[gameState.currentType].base_clicks;

    updateEggImage();
    updateProgressUI();

    if (!gameState.isGuest) {
      fetchGameJson("/api/navigate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
            .content,
        },
        body: JSON.stringify({
          type: gameState.currentType,
        }),
      })
        .then((data) => {
          if (data.status !== "success") {
            console.error("Navigation sync failed:", data.error);
          }
        })
        .catch((err) => console.error("Network error during sync:", err));
    }
  }

  function buyUpgrade(type) {
    if (!ownsGameLock) return;

    const currentLevel = gameState[type];

    const cost = Math.floor(10 * Math.pow(5, currentLevel));

    if (gameState.totalPoints < cost) {
      return;
    }

    const oldPoints = gameState.totalPoints;
    const oldLevel = gameState[type];

    gameState.totalPoints -= cost;
    gameState[type] += 1;

    updatePointsUI();
    updateUpgradeUI();

    if (!gameState.isGuest) {
      fetchGameJson("/api/buy_upgrade", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
            .content,
        },
        body: JSON.stringify({
          upgrade_type: type,
          new_level: gameState[type],
          new_points: gameState.totalPoints,
        }),
      })
        .then((data) => {
          if (data.status === "success") {
            gameState.totalPoints = data.new_points;
            gameState[type] = data.new_level;

            updatePointsUI();
            updateUpgradeUI();
          } else {
            gameState.totalPoints = oldPoints;
            gameState[type] = oldLevel;

            updatePointsUI();
            updateUpgradeUI();

            console.error("Sync failed:", data.error);
          }
        })
        .catch((err) => {
          gameState.totalPoints = oldPoints;
          gameState[type] = oldLevel;

          updatePointsUI();
          updateUpgradeUI();

          console.error("Sync failed:", err);
        });
    }
  }

  function updateUpgradeUI() {
    const upgrades = [
      {
        id: "clickpower-btn",
        key: "clickPower",
        name: "Click Power",
      },
      {
        id: "autoclicker-btn",
        key: "autoClickerPower",
        name: "Auto-Clicker",
      },
    ];

    upgrades.forEach((upgrade) => {
      const btn = document.getElementById(upgrade.id);

      if (!btn) return;

      const level = gameState[upgrade.key];
      const cost = Math.floor(10 * Math.pow(5, level));

      btn.innerHTML = `${upgrade.name} (lvl. ${level})<br><small>(Cost: ${formatPoints(cost)})</small>`;

      if (gameState.totalPoints < cost) {
        btn.disabled = true;
        btn.classList.add("is-disabled");
      } else {
        btn.disabled = false;
        btn.classList.remove("is-disabled");
      }
    });
  }

  function formatPoints(points) {
    return Number(points || 0).toLocaleString('en-AU', {
      notation: 'compact',
      compactDisplay: 'short',
      maximumFractionDigits: 2
    });
  }

  // Four event types together cover both desktop and mobile input:
  //   pointerdown - mouse clicks and stylus taps
  //   keydown     - any keyboard activity
  //   touchstart  - finger taps (mobile)
  //   scroll      - page scrolling (a low-effort "I'm still here" signal)
  // We use { passive: true } so we never block the browser's default
  // scrolling/input handling; we only need to *observe* activity.
  ["pointerdown", "keydown", "touchstart", "scroll"].forEach((eventName) => {
    window.addEventListener(eventName, markPlayerActive, { passive: true });
  });

  window.addEventListener("focus", () => {
    isWindowFocused = true;
    markPlayerActive();
  });

  window.addEventListener("blur", () => {
    isWindowFocused = false;
  });

  window.addEventListener("storage", (event) => {
    if (event.key !== GAME_LOCK_KEY || !ownsGameLock) {
      return;
    }

    let currentLock = null;

    if (event.newValue) {
      try {
        currentLock = JSON.parse(event.newValue);
      } catch (_error) {
        currentLock = null;
      }
    }

    if (currentLock && currentLock.tabId !== gameTabId && !isGameLockStale(currentLock)) {
      exitBecauseGameLockLost();
    }
  });

  window.addEventListener("pagehide", releaseGameLock);
  window.addEventListener("beforeunload", releaseGameLock);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      isWindowFocused = document.hasFocus();
      markPlayerActive();
    }
  });

  // Auto-clicker tick. Fires once per second, but each tick is gated by
  // isAutoClickerAllowed() above, so it does nothing while the tab is
  // hidden / unfocused / idle. The 1-second cadence is slow enough that
  // it never collides with manual clicks (which are also debounced) and
  // fast enough to feel responsive for upgrade demonstrations.
  setInterval(() => {
    if (isAutoClickerAllowed()) {
      const autoDamage =
        gameState.autoClickerPower === 1 ? 1 : gameState.autoClickerPower * 2;

      handleEggClick(autoDamage);
    }
  }, 1000);

  document
    .getElementById("egg-btn")
    .addEventListener("click", () => handleEggClick());
  document
    .getElementById("clickpower-btn")
    .addEventListener("click", () => buyUpgrade("clickPower"));
  document
    .getElementById("autoclicker-btn")
    .addEventListener("click", () => buyUpgrade("autoClickerPower"));

  window.addEventListener("load", () => {
    if (!tryAcquireGameLock()) {
      exitBecauseGameLockLost();
      return;
    }

    updateProgressUI();
    updateUpgradeUI();

    document.getElementById("loading-overlay").style.display = "none";
    document.getElementById("game-screen").style.display = "";
    updateEggImage();
  });

  window.changeEgg = changeEgg;
})();
