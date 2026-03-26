// Get the login form and message box from the page.
const loginForm = document.getElementById("loginForm");
const message = document.getElementById("message");

// Run this code when the user submits the form.
loginForm.addEventListener("submit", function(event) {
  // Prevent the browser from submitting the form immediately.
  event.preventDefault();

  // Read the email and password input values.
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  // Show an error if any field is empty.
  if (email === "" || password === "") {
    message.textContent = "Please fill in all fields.";
    message.className = "message";
  } else {
    // Temporary success message for frontend testing only.
    message.textContent = "Login successful!";
    message.className = "message success";
  }
});
