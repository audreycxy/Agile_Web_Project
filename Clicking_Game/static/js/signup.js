// Handle sign-up form submission
// Validate that all fields are filled and that the password matches the confirmation password
const signupForm = document.getElementById("signupForm");

if (signupForm) {
  signupForm.addEventListener("submit", function(event) {
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const message = document.getElementById("message");

    if (username === "" || email === "" || password === "" || confirmPassword === "") {
      event.preventDefault();
      message.textContent = "Please fill in all fields.";
      return;
    }

    if (password !== confirmPassword) {
      event.preventDefault();
      message.textContent = "Passwords do not match.";
    }
  });
}
