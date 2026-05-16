// Run the code after the page has finished loading
document.addEventListener("DOMContentLoaded", () => {
  const historyChartScroll = document.getElementById("historyChartScroll");

  if (historyChartScroll && window.historyScores) {
    historyChartScroll.style.minWidth = `${Math.max(
      760,
      window.historyScores.length * 80,
    )}px`;
  }

  // Create a line chart for the player's score history
  const historyChartCanvas = document.getElementById("historyScoreChart");

  if (
    historyChartCanvas &&
    window.historyScores &&
    window.historyScores.length > 0
  ) {
    const labels = window.historyScores.map(
      (game, index) => `Game ${index + 1}`,
    );

    const scores = window.historyScores.map((game) => Number(game.score));

    new Chart(historyChartCanvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Score",
            data: scores,
            tension: 0.3,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  }

  const aiFeedbackBtn = document.getElementById("aiFeedbackBtn");
  const aiFeedbackBox = document.getElementById("aiFeedbackBox");
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");

  if (!aiFeedbackBtn || !aiFeedbackBox) {
    return;
  }

  aiFeedbackBtn.addEventListener("click", async () => {
    aiFeedbackBtn.disabled = true;
    aiFeedbackBox.textContent = "Generating feedback...";

    try {
      const response = await fetch("/ai_feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        aiFeedbackBox.textContent =
          data.feedback || "AI feedback is unavailable right now.";
        return;
      }

      aiFeedbackBox.textContent = data.feedback;
    } catch (error) {
      aiFeedbackBox.textContent = "AI feedback is unavailable right now.";
    } finally {
      aiFeedbackBtn.disabled = false;
    }
  });
});
