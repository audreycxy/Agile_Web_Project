document.addEventListener("DOMContentLoaded", () => {
  const eggButton = document.getElementById("demoEggButton");
  const scoreText = document.getElementById("demoScore");
  const clicksText = document.getElementById("demoClicks");
  const progressBar = document.getElementById("demoProgressBar");
  const levelText = document.getElementById("demoLevel");
  const hintText = document.getElementById("demoHint");

  const sectionLinks = document.querySelectorAll(".section-nav-link");
  const sections = document.querySelectorAll("#how-it-works, #features");
  const sectionIds = Array.from(sections).map((section) => section.getAttribute("id"));
  let pendingSection = "";

  const setActiveSection = (sectionId) => {
    sectionLinks.forEach((link) => {
      link.classList.remove("active");

      if (link.getAttribute("href") === "#" + sectionId) {
        link.classList.add("active");
      }
    });
  };

  const syncPendingSectionFromHash = () => {
    const hashSection = window.location.hash.replace("#", "");
    pendingSection = sectionIds.includes(hashSection) ? hashSection : "";

    if (pendingSection) {
      setActiveSection(pendingSection);
    }
  };

  if (
    !eggButton ||
    !scoreText ||
    !clicksText ||
    !progressBar ||
    !levelText ||
    !hintText
  ) {
    return;
  }

  let score = 0;
  let clicks = 0;
  const clickPower = 1;
  const previewTarget = 20;

  syncPendingSectionFromHash();

  eggButton.addEventListener("click", () => {
    if (clicks >= previewTarget) {
      return;
    }

    clicks += 1;
    score += clickPower;

    scoreText.textContent = score;
    clicksText.textContent = `Clicks: ${clicks}`;

    const progress = (clicks / previewTarget) * 100;
    progressBar.style.width = `${progress}%`;

    if (clicks === previewTarget) {
      levelText.textContent = "Preview Complete";
      hintText.textContent =
        "Preview complete! Sign up or log in to play the full game.";
      eggButton.disabled = true;
      eggButton.style.opacity = "0.85";
      eggButton.style.cursor = "default";
    }
  });

  const updateSectionHighlight = () => {
    let currentSection = "";

    sections.forEach((section) => {
      const sectionTop = section.offsetTop - 140;

      if (window.scrollY >= sectionTop) {
        currentSection = section.getAttribute("id");
      }
    });

    if (pendingSection && currentSection !== pendingSection) {
      setActiveSection(pendingSection);
      return;
    }

    if (pendingSection && currentSection === pendingSection) {
      pendingSection = "";
    }

    setActiveSection(currentSection);
  };

  sectionLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const targetSection = link.getAttribute("href").replace("#", "");

      if (sectionIds.includes(targetSection)) {
        pendingSection = targetSection;
        setActiveSection(targetSection);
      }
    });
  });

  window.addEventListener("hashchange", syncPendingSectionFromHash);
  window.addEventListener("scroll", updateSectionHighlight);
  updateSectionHighlight();
});
