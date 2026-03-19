const loginForm = document.getElementById("loginForm");
const message = document.getElementById("message");

loginForm.addEventListener("submit", function(event) {
  event.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  if (email === "" || password === "") {
    message.textContent = "Please fill in all fields.";
    message.className = "message";
  } else {
    message.textContent = "Login successful!";
    message.className = "message success";
  }
});