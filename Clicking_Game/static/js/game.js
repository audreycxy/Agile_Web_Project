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
        standard: {name: "Egg", baseClicks: 10, basePoints: 1, image: "static/images/defaultegg_nobackground.png"},
        water: {name: "Water Egg", baseClicks: 20, basePoints: 5, image: "static/images/defaultegg_nobackground.png"} // example additonal type
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

    let isAnimating = false;

    function handleEggClick() {
        if (isAnimating) return;

        gameState.clicksRemaning--;
        updateProgressUI()

        if (gameState.clicksRemaning <= 0) {
            console.log("zero clicks left"); // no clicks left print
            const earned = calculateReward();
            gameState.totalPoints += earned;
            updatePointsUI(earned);
            triggerEggBreak();
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

    function updateEggImage() {
        const eggImage = document.querySelectorAll('.egg-image');
        eggImage.forEach(eggImage => {
            eggImage.style.backgroundImage = `url('${EGG_CONFIG[gameState.currentType].image}')`
        })
    }

    function triggerEggBreak() {
        isAnimating = true; // animation lock engaged

        const main = document.getElementById('main-egg');
        const top = document.getElementById('top-half');
        const bottom = document.getElementById('bottom-half');
        const next = document.getElementById('next-egg');

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
        }, 600)

        console.log('broke and replaced the egg')
    }

    // Event Listeners/Triggers:
    document.getElementById('egg-btn').addEventListener('click', handleEggClick);

    window.addEventListener('load', () => { // only displays game content on the html once all assets are loaded
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('game-screen').style.display ='';
    })
})();