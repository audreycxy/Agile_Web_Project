const playerData = {
  username: "player01",
  highestScore: 120,
  latestResult: "90 points"
};


document.getElementById("profileText").textContent = `Username: ${playerData.username}`;
document.getElementById("highestScore").textContent = playerData.highestScore;
document.getElementById("latestResult").textContent = playerData.latestResult;

const actionMessage = document.getElementById("actionMessage");

document.getElementById("startGameBtn").addEventListener("click", function () {
  actionMessage.textContent = "Starting game...";
});

document.getElementById("viewHistoryBtn").addEventListener("click", function () {
  actionMessage.textContent = "Opening results/history page...";
});

document.getElementById("logoutBtn").addEventListener("click", function () {
  window.location.href = "/logout";
});