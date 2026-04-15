const loginForm = document.getElementById("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", function(event) {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const message = document.getElementById("message");

    if (email === "" || password === "") {
      event.preventDefault();
      message.textContent = "Please fill in all fields.";
    }
  });
}
