(function() {
    // INITIALISATION
    // Egg Order:
    const EGG_ORDER = ['standard', 'water', 'gold'];
    // Game State:
    let gameState = {
        totalPoints: INITIAL_STATE.points,
        currentInfinityLevel: INITIAL_STATE.current_infinity_level,
        currentType: INITIAL_STATE.current_type,
        highestType: INITIAL_STATE.highest_type,
        clicksRemaining: INITIAL_STATE.clicks_remaining ?? EGG_CONFIG[INITIAL_STATE.current_type].base_clicks,
        progressPercent: INITIAL_STATE.progress_percent,
        isGuest: INITIAL_STATE.is_guest,
        clickPower: INITIAL_STATE.click_power_lvl,
        autoClickerPower: INITIAL_STATE.autoclicker_lvl
    };
    updateProgressUI();
    updateUpgradeUI();
    let isAnimating = false; // for egg break
    let isSyncing = false;


    function handleEggClick(damageAmount = null) {
        if (isAnimating || isSyncing) return;

        const damage = damageAmount !== null ? damageAmount : gameState.clickPower;
        gameState.clicksRemaining -= damage;

        console.log("click power", gameState.clickPower);
        console.log("damage:", damage);

        updateProgressUI();

        if (gameState.clicksRemaining <= 0) {
            // lock click handling for reliable sync
            gameState.clicksRemaining = 0;
            isSyncing = true;

            // calculate local reward
            const earned = calculateReward();
            gameState.totalPoints += earned;

            // find next egg
            const eggKeys = EGG_ORDER;
            const nextIndex =  eggKeys.indexOf(gameState.currentType) + 1;

            // if the current egg is the last egg, don't try to move on to the next egg
            if (gameState.currentType == eggKeys[eggKeys.length-1]) {
                console.log("Final egg reached!");
            } else {
                if (gameState.highestType == gameState.currentType) {
                    gameState.highestType = eggKeys[nextIndex];
                }
                gameState.currentType = eggKeys[nextIndex];
            }
            
            console.log('next egg key:', gameState.currentType);
            console.log('available keys:', EGG_ORDER);
            gameState.clicksRemaining = EGG_CONFIG[gameState.currentType].base_clicks;

            if (!gameState.isGuest) {
                fetch("/api/sync", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "success") {
                        gameState.totalPoints = data.new_points;
                        gameState.currentType = data.current_type;
                        gameState.highestType = data.highest_type;
                        gameState.clicksRemaining = data.clicks_remaining;

                        console.log("Progress synced with server");
                        isSyncing = false;
                        updatePointsUI();
                        updateUpgradeUI();
                    }
                })
                .catch(err => {
                    isSyncing = false;
                    console.error("Sync failed:", err);
                });
            } else {
                console.log("Guest progress updated locally.");
                isSyncing = false;
                updatePointsUI();
                updateUpgradeUI();
            }
            updateProgressUI();
            triggerEggBreak();
        }
    }

    function calculateReward() { // add level as a parameter once added
        const level = 1 // placeholder for level (should probably be renamed to power to not be confused with levels as in stages)

        const egg = EGG_CONFIG[gameState.currentType];
        return Math.floor(egg.base_points * level);
    }

    function updatePointsUI() {
        document.getElementById('egg-points').innerText = gameState.totalPoints;
    }

    function updateProgressUI() {
        const requiredClicks = EGG_CONFIG[gameState.currentType].base_clicks
        const percentage = ((requiredClicks - gameState.clicksRemaining) / requiredClicks) * 100;
        const barWidth = Math.min(Math.max(percentage, 0), 100);

        document.getElementById('progress-bar').style.width = `${barWidth}%`;
        document.getElementById('click-count').innerText = `${gameState.clicksRemaining}/${requiredClicks} left`;
    }

    function updateEggImage() {
        const eggImage = document.querySelectorAll('.egg-image');
        eggImage.forEach(eggImage => {
            eggImage.style.backgroundImage = `url('${EGG_CONFIG[gameState.currentType].image}')`
        })
        document.getElementById('egg-type-display').innerText = EGG_CONFIG[gameState.currentType].name;
    }

    function triggerEggBreak() {
        isAnimating = true; // animation lock engaged

        const main = document.getElementById('main-egg');
        const top = document.getElementById('top-half');
        const bottom = document.getElementById('bottom-half');
        const next = document.getElementById('next-egg');

        next.style.backgroundImage = `url('${EGG_CONFIG[gameState.currentType].image}')`;

        // local helper for swapping visibility
        const setBreakingMode = (isBreaking) => {
            const displayState = isBreaking ? 'block' : 'none';
            main.style.display = isBreaking ? 'none' : 'block';
            top.style.display = displayState;
            bottom.style.display = displayState;
            next.style.display = displayState;
        }

        setBreakingMode(true);

        void top.offsetHeight;

        // start animations
        top.classList.add('cracked-top');
        bottom.classList.add('cracked-bottom');
        next.classList.add('reveal-egg');

        setTimeout(() => {
            setBreakingMode(false);

            top.classList.remove('cracked-top');
            bottom.classList.remove('cracked-bottom');
            next.classList.remove('reveal-egg');

            isAnimating = false; // animation lock released
            updateEggImage()
        }, 600)

        console.log('broke and replaced the egg')
    }

    function changeEgg(direction) {
        const eggKeys = EGG_ORDER;
        const nextIndex = eggKeys.indexOf(gameState.currentType) + direction;
        const highestIndex = eggKeys.indexOf(gameState.highestType);

        if (nextIndex < 0 || nextIndex > highestIndex) {
            console.log("Egg locked or doesn't exist");
            return;
        }
        if (gameState.clicksRemaining < EGG_CONFIG[gameState.currentType].base_clicks && gameState.clicksRemaining > 0) {
            const confirmed = confirm("Are you sure? Progress on this egg will be reset!");
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
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content
                },
                // Send the name of the egg we switched to
                body: JSON.stringify({ type: gameState.currentType })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status !== "success") {
                    console.error("Navigation sync failed:", data.error);
                }
            })
            .catch(err => console.error("Network error during sync:", err));
        }
    }

    function buyUpgrade(type) {
        const currentLevel = gameState[type];

        // next level costs 5x as much as the last
        const cost = Math.floor(10 * Math.pow(5, currentLevel));

        // check if player can afford
        if (gameState.totalPoints < cost) {
            return;
        }

        const oldPoints = gameState.totalPoints;
        const oldLevel = gameState[type];

        // player can afford so deduct cost
        gameState.totalPoints -= cost;
        gameState[type] += 1;

        updatePointsUI();
        updateUpgradeUI();

        // sync to server
        if (!gameState.isGuest) {
            fetch("/api/buy_upgrade", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({
                    upgrade_type: type,
                    new_level: gameState[type],
                    new_points: gameState.totalPoints
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    gameState.totalPoints = data.new_points;
                    gameState[type] = data.new_level;
                    updatePointsUI();
                    updateUpgradeUI();
                } else {
                    gameState.totalPoints = oldPoints;
                    gameState[type] = oldLevel;
                    updatePointsUI();
                    updateUpgradeUI()
                    console.error("Sync failed:", err);
                }
            })
            .catch(err => {
                gameState.totalPoints = oldPoints;
                gameState[type] = oldLevel;
                updatePointsUI();
                updateUpgradeUI();
                console.error("Sync failed:", err);
            });
        } else {
            console.log("Guest purchase done locally.");
        }
    }

    function updateUpgradeUI() {
        const upgrades = [
            { id: 'clickpower-btn', key: 'clickPower', name: 'Click Power' },
            { id: 'autoclicker-btn', key: 'autoClickerPower', name: 'Auto-Clicker' }
        ];

        upgrades.forEach(upgrade => {
            const btn = document.getElementById(upgrade.id);
            if (!btn) return;
            const level = gameState[upgrade.key];
            const cost = Math.floor(10 * Math.pow(5, level));

            btn.innerHTML = `${upgrade.name} (lvl. ${level})<br><small>(Cost: ${cost})</small>`;

            if (gameState.totalPoints < cost) {
                btn.disabled = true;
                btn.classList.replace('btn-outline-success', 'btn-outline-secondary');
            } else {
                btn.disabled = false;
                btn.classList.replace('btn-outline-secondary', 'btn-outline-success');
            }
        })
    }

    // auto-clicker functionality
    setInterval(() => {
        if (gameState.autoClickerPower > 0) {
            const autoDamage = gameState.autoClickerPower === 1 ? 1 : (gameState.autoClickerPower * 2);
            handleEggClick(autoDamage);
        }
    }, 1000);

    // Event Listeners/Triggers:
    document.getElementById('egg-btn').addEventListener('click', () => handleEggClick());
    document.getElementById('clickpower-btn').addEventListener('click', () => buyUpgrade('clickPower'));
    document.getElementById('autoclicker-btn').addEventListener('click', () => buyUpgrade('autoClickerPower'));

    window.addEventListener('load', () => { // only displays game content on the html once all assets are loaded
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('game-screen').style.display ='';
    })

    window.changeEgg = changeEgg;
})();