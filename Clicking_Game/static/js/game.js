// Looks for the play buttons on both the guest page and player dashboard (and elsewhere) and redirects to game page on click.
const playBtns = document.querySelectorAll(".btn-play");
if (playBtns.length > 0) {
    Array.from(playBtns).forEach(btn => {
        button.addEventListener('click', () => {
            window.location.href = "/game";
        });
    });
}

(function() {
    // Egg Order:
    const EGG_ORDER = ['standard', 'water', 'gold']
    // Game State (default/guest):
    let gameState = {
        totalPoints: INITIAL_STATE.points,
        currentLevel: INITIAL_STATE.current_level,
        currentType: INITIAL_STATE.current_type,
        highestType: INITIAL_STATE.highest_type,
        clicksRemaning: INITIAL_STATE.clicks_remaining ?? EGG_CONFIG[INITIAL_STATE.current_type].base_clicks,
        progressPercent: INITIAL_STATE.progress_percent,
        isGuest: INITIAL_STATE.is_guest
    };

    

    updateProgressUI();

    let isAnimating = false;

    function handleEggClick() {
        if (isAnimating) return;

        gameState.clicksRemaning--;
        updateProgressUI()

        if (gameState.clicksRemaning <= 0) {
            const earned = calculateReward();
            gameState.totalPoints += earned;

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
            gameState.clicksRemaning = EGG_CONFIG[gameState.currentType].base_clicks;

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
                        gameState.clicksRemaning = data.clicks_remaining;

                        console.log("Progress synced with server");
                        updatePointsUI();
                    }
                })
            } else {
                console.log("Guest progress updated locally.");
                updatePointsUI();
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
        const percentage = ((requiredClicks - gameState.clicksRemaning) / requiredClicks) * 100;
        const barWidth = Math.min(Math.max(percentage, 0), 100);

        document.getElementById('progress-bar').style.width = `${barWidth}%`;
        document.getElementById('click-count').innerText = `${gameState.clicksRemaning}/${requiredClicks} left`;
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

    function changeEgg(direction) {
        const eggKeys = EGG_ORDER;
        const nextIndex = eggKeys.indexOf(gameState.currentType) + direction;
        const highestIndex = eggKeys.indexOf(gameState.highestType);

        if (nextIndex < 0 || nextIndex > highestIndex) {
            console.log("Egg locked or doesn't exist");
            return;
        }

        gameState.currentType = eggKeys[nextIndex];
        gameState.clicksRemaning = EGG_CONFIG[gameState.currentType].base_clicks;

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

    // Event Listeners/Triggers:
    document.getElementById('egg-btn').addEventListener('click', handleEggClick);

    window.addEventListener('load', () => { // only displays game content on the html once all assets are loaded
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('game-screen').style.display ='';
    })

    window.changeEgg = changeEgg;
})();