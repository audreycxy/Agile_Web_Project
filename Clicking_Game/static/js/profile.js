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

initializePasswordToggle();
