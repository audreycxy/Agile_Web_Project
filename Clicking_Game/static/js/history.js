// Run the code after the page has finished loading
document.addEventListener("DOMContentLoaded", () => {
  console.log("Game History page loaded.");

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
