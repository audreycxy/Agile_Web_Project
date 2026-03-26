document.getElementById("signupForm").addEventListener("submit", function(event) {
    event.preventDefault();

    // Read values entered by the user.
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const message = document.getElementById("message");

    // Check whether all fields were filled in.
    if (username === "" || email === "" || password === "" || confirmPassword === "") {
        message.textContent = "Please fill in all fields.";
        message.style.color = "red";
        return;
    }

    // Check whether both password fields match.
    if (password !== confirmPassword) {
        message.textContent = "Passwords do not match.";
        message.style.color = "red";
        return;
    }

    // Temporary success message for frontend testing only. Can remove once connected to backend.
    message.textContent = "Sign up successful!";
    message.style.color = "green";
});