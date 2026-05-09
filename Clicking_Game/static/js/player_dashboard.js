// Handle the Start Game button on the player dashboard
// Display a short message and redirect the player to the game page
const actionMessage = document.getElementById("actionMessage");

document.getElementById("startGameBtn").addEventListener("click", function () {
  actionMessage.textContent = "Starting game...";
  window.location.href = "/game";
});