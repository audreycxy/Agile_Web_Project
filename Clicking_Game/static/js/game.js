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

  function handleEggClick(damageAmount = null) {
    if (isAnimating || isSyncing) return;

    const damage = damageAmount !== null ? damageAmount : gameState.clickPower;
    gameState.clicksRemaining -= damage;

    updateProgressUI();

    if (gameState.clicksRemaining <= 0) {
      gameState.clicksRemaining = 0;
      isSyncing = true;

      const earned = calculateReward();
      gameState.totalPoints += earned;

      const eggKeys = EGG_ORDER;
      const nextIndex = eggKeys.indexOf(gameState.currentType) + 1;

      if (gameState.currentType !== eggKeys[eggKeys.length - 1]) {
        if (gameState.highestType == gameState.currentType) {
          gameState.highestType = eggKeys[nextIndex];
        }

        gameState.currentType = eggKeys[nextIndex];
      }

      gameState.clicksRemaining = EGG_CONFIG[gameState.currentType].base_clicks;

      if (!gameState.isGuest) {
        fetch("/api/sync", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
              .content,
          },
          body: JSON.stringify({}),
        })
          .then((response) => response.json())
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
    const eggKeys = EGG_ORDER;
    const nextIndex = eggKeys.indexOf(gameState.currentType) + direction;
    const highestIndex = eggKeys.indexOf(gameState.highestType);

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
      fetch("/api/navigate", {
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
        .then((response) => response.json())
        .then((data) => {
          if (data.status !== "success") {
            console.error("Navigation sync failed:", data.error);
          }
        })
        .catch((err) => console.error("Network error during sync:", err));
    }
  }

  function buyUpgrade(type) {
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
      fetch("/api/buy_upgrade", {
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
        .then((response) => response.json())
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

  setInterval(() => {
    if (gameState.autoClickerPower > 0) {
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
    updateProgressUI();
    updateUpgradeUI();
    updatePointsUI();
    
    document.getElementById("loading-overlay").style.display = "none";
    document.getElementById("game-screen").style.display = "";
    updateEggImage();
  });

  window.changeEgg = changeEgg;
})();
