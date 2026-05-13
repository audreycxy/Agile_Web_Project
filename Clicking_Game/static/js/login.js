function initializePasswordToggle() {
  const toggleButtons = document.querySelectorAll(".password-toggle-btn");

  toggleButtons.forEach((button) => {
    button.addEventListener("click", function() {
      const targetId = button.getAttribute("data-target");
      const input = document.getElementById(targetId);

      if (!input) {
        return;
      }

      const isPasswordHidden = input.type === "password";

      input.type = isPasswordHidden ? "text" : "password";
      button.textContent = isPasswordHidden ? "Hide" : "Show";
      button.setAttribute("aria-pressed", String(isPasswordHidden));
    });
  });
}

// Handle login form submission
// Check whether the email and password fields are filled before allowing the form to submit
const loginForm = document.getElementById("loginForm");

initializePasswordToggle();

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
