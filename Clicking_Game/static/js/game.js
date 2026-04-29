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

    // Game State:
    let totalPoints = 0;
    let currentLevel = 1;
    let currentType = 'standard';
    let clicksRemaning = EGG_CONFIG[currentType].baseClicks;

    function handleEggClick() {
        clicksRemaning--;
        if (clicksRemaning <= 0) {
            console.log("zero clicks left"); // no clicks left print
            const earned = calculateReward();
            totalPoints += earned;
            updateUI(earned);
        }
    }

    function calculateReward() { // add level as a parameter once added
        const level = 1 // placeholder for level (should probably be renamed to power to not be confused with levels as in stages)

        const egg = EGG_CONFIG[currentType];
        return Math.floor(egg.basePoints * level);
    }

    function updateUI(pointsEarned) {
        document.getElementById('egg-points').innerText = totalPoints;
        console.log(`Earned ${pointsEarned} points!`); // amount rewarded print
    }

    // Event Listeners/Triggers:
    document.getElementById('egg-btn').addEventListener('click', handleEggClick);
})();