// Handle sign-up form submission
// Validate that all fields are filled and that the password matches the confirmation password
const signupForm = document.getElementById("signupForm");

// Switch the submit button into a loading state. The form will continue to
// submit naturally; this is purely visual feedback so the user knows the
// request is in-flight (the signup round-trip on Render free tier can take
// 5-15 seconds because of cold-start + the verification-email SMTP step).
function showSignupLoadingState() {
  const submitBtn = document.getElementById("signupSubmitBtn");
  const spinner = document.getElementById("signupSubmitSpinner");
  const label = document.getElementById("signupSubmitLabel");

  if (submitBtn) {
    submitBtn.disabled = true;
  }
  if (spinner) {
    spinner.classList.remove("d-none");
  }
  if (label) {
    label.textContent = "Signing up…";
  }
}

if (signupForm) {
  signupForm.addEventListener("submit", function (event) {
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
      return;
    }

    // Validation passed — let the form submit, but flip the button into a
    // loading state so the user gets feedback during the round-trip.
    showSignupLoadingState();
  });
}
