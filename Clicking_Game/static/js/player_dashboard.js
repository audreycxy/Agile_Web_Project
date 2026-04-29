const actionMessage = document.getElementById("actionMessage");

document.getElementById("startGameBtn").addEventListener("click", function () {
  actionMessage.textContent = "Starting game...";
  window.location.href = "/game";
});