// Looks for the play buttons on both the guest page and player dashboard (and elsewhere) and redirects to game page on click.
const playBtns = document.querySelectorAll(".btn-play");
if (playBtns.length > 0) {
    Array.from(playBtns).forEach(btn => {
        btn.addEventListener('click', () => {
            window.location.href = "/game";
        });
    });
}

(function () {
    if (typeof INITIAL_STATE === "undefined") {
        return;
    }

    // Egg Data:
    const EGG_CONFIG = {
        standard: { name: "Standard", baseClicks: 10, basePoints: 1, image: "static/images/defaultegg_nobackground.png" },
        water: { name: "Water", baseClicks: 20, basePoints: 5, image: "static/images/wateregg.png" }, // example additonal type
        gold: { name: "Golden", baseClicks: 1, basePoints: 1, image: "static/images/defaultegg_nobackground.png" }
    };

    // Game State (default/guest):
    let gameState = {
        totalPoints: INITIAL_STATE.points,
        // currentLevel: INITIAL_STATE.current_level,
        currentLevel: INITIAL_STATE.current_infinity_level,
        currentType: INITIAL_STATE.current_type,
        highestType: INITIAL_STATE.highest_type ?? INITIAL_STATE.current_type,
        clicksRemaining: INITIAL_STATE.clicks_remaining ?? EGG_CONFIG[INITIAL_STATE.current_type].baseClicks,
        progressPercent: INITIAL_STATE.progress_percent ?? 0,
        isGuest: INITIAL_STATE.is_guest
    };

    function jsonPostOptions(payload) {
        return {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": CSRF_TOKEN,
            },
            body: JSON.stringify(payload),
        };
    }

    function saveGameState() {
        if (gameState.isGuest) {
            return Promise.resolve();
        }

        return fetch("/save_game_state", jsonPostOptions({
            points: gameState.totalPoints,
            current_infinity_level: gameState.currentLevel,
            current_type: gameState.currentType,
            highest_type: gameState.highestType,
            clicks_remaining: gameState.clicksRemaining,
            progress_percent: gameState.progressPercent,
        }));
    }

    updateProgressUI();

    let isAnimating = false;
    let isRestarting = false;

    function handleEggClick() {
        if (isAnimating) return;

        gameState.clicksRemaining--;
        updateProgressUI()

        if (gameState.clicksRemaining <= 0) {
            console.log("zero clicks left"); // no clicks left print
            const earned = calculateReward();
            gameState.totalPoints += earned;
            updatePointsUI();

            // need to add a check for out of bounds
            const eggKeys = Object.keys(EGG_CONFIG);
            const nextIndex =  eggKeys.indexOf(gameState.currentType) + 1;
            gameState.currentType = eggKeys[nextIndex];

            gameState.clicksRemaining = EGG_CONFIG[gameState.currentType].baseClicks;
            updateProgressUI()
            
            triggerEggBreak();
        }
    }

    function calculateReward() { // add level as a parameter once added
        const level = 1 // placeholder for level (should probably be renamed to power to not be confused with levels as in stages)

        const egg = EGG_CONFIG[gameState.currentType];
        return Math.floor(egg.basePoints * level);
    }

    function updatePointsUI() {
        document.getElementById('egg-points').innerText = gameState.totalPoints;
    }

    function updateProgressUI() {
        const requiredClicks = EGG_CONFIG[gameState.currentType].baseClicks
        const percentage = ((requiredClicks - gameState.clicksRemaining) / requiredClicks) * 100;
        const barWidth = Math.min(Math.max(percentage, 0), 100);

        gameState.progressPercent = barWidth;
        document.getElementById('progress-bar').style.width = `${barWidth}%`;
        document.getElementById('click-count').innerText = `${gameState.clicksRemaining}/${requiredClicks} left`;
    }

    function updateHighestType(eggKeys) {
        const currentHighestIndex = eggKeys.indexOf(gameState.highestType);
        const currentTypeIndex = eggKeys.indexOf(gameState.currentType);

        if (currentTypeIndex > currentHighestIndex) {
            gameState.highestType = gameState.currentType;
        }
    }

    function formatScore(points) {
        return Number(points || 0).toLocaleString();
    }

    function renderLeaderboard(players, currentUserId) {
        const leaderboardList = document.getElementById("leaderboard-list");

        if (!leaderboardList) {
            return;
        }

        if (!players.length) {
            const emptyItem = document.createElement("li");
            emptyItem.className = "list-group-item text-muted";
            emptyItem.textContent = "No scores yet.";
            leaderboardList.replaceChildren(emptyItem);
            return;
        }

        const items = players.map((player, index) => {
            const isCurrentUser = currentUserId === player.id;
            const listItem = document.createElement("li");
            const nameSpan = document.createElement("span");
            const scoreBadge = document.createElement("span");
            const displayName = isCurrentUser ? `${player.name} (You)` : player.name;

            listItem.className = isCurrentUser
                ? "list-group-item list-group-item-warning d-flex justify-content-between align-items-center"
                : "list-group-item d-flex justify-content-between align-items-center";
            nameSpan.textContent = `${index + 1}. ${displayName}`;
            scoreBadge.className = "badge bg-dark rounded-pill";
            scoreBadge.textContent = formatScore(player.points);

            listItem.append(nameSpan, scoreBadge);
            return listItem;
        });

        leaderboardList.replaceChildren(...items);
    }

    function fetchLeaderboard() {
        return fetch(LEADERBOARD_API_URL)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Leaderboard request failed with status ${response.status}`);
                }

                return response.json();
            })
            .then(data => {
                renderLeaderboard(data.players ?? [], data.current_user_id ?? null);
            })
            .catch(error => {
                console.error("Failed to load leaderboard", error);

                const leaderboardList = document.getElementById("leaderboard-list");
                if (leaderboardList) {
                    const errorItem = document.createElement("li");
                    errorItem.className = "list-group-item text-danger";
                    errorItem.textContent = "Unable to load leaderboard.";
                    leaderboardList.replaceChildren(errorItem);
                }
            });
    }

    function updateEggImage() {
        const eggImage = document.querySelectorAll('.egg-image');
        eggImage.forEach(eggImage => {
            eggImage.style.backgroundImage = `url('${EGG_CONFIG[gameState.currentType].image}')`
        })
        document.getElementById('egg-type-display').innerText = gameState.currentType;
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

    // Event Listeners/Triggers:
    document.getElementById('egg-btn').addEventListener('click', handleEggClick);

    window.addEventListener('load', () => { // only displays game content on the html once all assets are loaded
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('game-screen').style.display = '';
        fetchLeaderboard();
    })
})();
