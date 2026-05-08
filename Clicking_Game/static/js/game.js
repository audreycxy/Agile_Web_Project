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
    // Egg Data:
    const EGG_CONFIG = {
        standard: {name: "Egg", baseClicks: 10, basePoints: 1},
        water: {name: "Water Egg", baseClicks: 20, basePoints: 5} // example additonal type
    };

    // Game State (default/guest):
    let gameState = {
        totalPoints: INITIAL_STATE.points,
        currentLevel: INITIAL_STATE.current_level,
        currentType: INITIAL_STATE.current_type,
        clicksRemaning: INITIAL_STATE.clicks_remaining ?? EGG_CONFIG[INITIAL_STATE.current_type].baseClicks,
        isGuest: INITIAL_STATE.is_guest
    };

    

    updateProgressUI();

    function handleEggClick() {
        gameState.clicksRemaning--;
        updateProgressUI()
        if (gameState.clicksRemaning <= 0) {
            console.log("zero clicks left"); // no clicks left print
            const earned = calculateReward();
            gameState.totalPoints += earned;
            updatePointsUI(earned);
        }
    }

    function calculateReward() { // add level as a parameter once added
        const level = 1 // placeholder for level (should probably be renamed to power to not be confused with levels as in stages)

        const egg = EGG_CONFIG[gameState.currentType];
        return Math.floor(egg.basePoints * level);
    }

    function updatePointsUI(pointsEarned) {
        document.getElementById('egg-points').innerText = gameState.totalPoints;
        console.log(`Earned ${pointsEarned} points!`); // amount rewarded print
    }

    function updateProgressUI() {
        const requiredClicks = EGG_CONFIG[gameState.currentType].baseClicks
        const percentage = ((requiredClicks - gameState.clicksRemaning) / requiredClicks) * 100;
        const barWidth = Math.min(Math.max(percentage, 0), 100);

        document.getElementById('progress-bar').style.width = `${barWidth}%`;
        document.getElementById('click-count').innerText = `${gameState.clicksRemaning}/${requiredClicks} left`;
    }

    // Event Listeners/Triggers:
    document.getElementById('egg-btn').addEventListener('click', handleEggClick);

    window.addEventListener('load', () => { // only displays game content on the html once all assets are loaded
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('game-screen').style.display ='';
    })
})();