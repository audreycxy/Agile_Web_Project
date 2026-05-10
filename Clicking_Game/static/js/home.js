document.addEventListener("DOMContentLoaded", () => {
  const eggButton = document.getElementById("demoEggButton");
  const scoreText = document.getElementById("demoScore");
  const clicksText = document.getElementById("demoClicks");
  const progressBar = document.getElementById("demoProgressBar");
  const levelText = document.getElementById("demoLevel");
  const hintText = document.getElementById("demoHint");

  if (
    !eggButton ||
    !scoreText ||
    !clicksText ||
    !progressBar ||
    !levelText ||
    !hintText
  ) {
    return;
  }

  let score = 0;
  let clicks = 0;
  const clickPower = 1;
  const previewTarget = 20;

  eggButton.addEventListener("click", () => {
    if (clicks >= previewTarget) {
      return;
    }

    clicks += 1;
    score += clickPower;

    scoreText.textContent = score;
    clicksText.textContent = `Clicks: ${clicks}`;

    const progress = (clicks / previewTarget) * 100;
    progressBar.style.width = `${progress}%`;

    if (clicks === previewTarget) {
      levelText.textContent = "Preview Complete";
      hintText.textContent =
        "Preview complete! Sign up or log in to play the full game.";
      eggButton.disabled = true;
      eggButton.style.opacity = "0.85";
      eggButton.style.cursor = "default";
    }
  });
});
