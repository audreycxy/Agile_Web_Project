/*
  searchTable()

  Purpose:
  Filters the player results table based on the username entered by the admin.

  How it works:
  1. Read the value from the search input.
  2. Convert the input to lowercase.
  3. Loop through each table row.
  4. Compare the player username with the search text.
  5. Hide rows that do not match and show rows that match.
*/
function searchTable() {
  const input = document.getElementById("searchInput").value.toLowerCase();

  const rows = document.querySelectorAll("#resultsTable tbody tr");

  rows.forEach((row) => {
    /*
      The "No player results found" row does not contain normal result data.
      Therefore, rows with fewer than 4 cells are skipped.
    */
    if (row.cells.length < 4) {
      return;
    }

    const username = row.cells[0].innerText.toLowerCase();

    row.style.display = username.includes(input) ? "" : "none";
  });
}

/*
  sortTable()

  Purpose:
  Sorts the player results table based on the selected dropdown option.

  The admin can sort by:
  - score
  - highest score
  - date played
*/
function sortTable() {
  const sortValue = document.getElementById("sortSelect").value;
  const table = document.getElementById("resultsTable");
  const tbody = table.querySelector("tbody");

  /*
    Convert table rows into an array so that the rows can be sorted.
    Only rows with 4 cells are real result rows.
  */
  const rows = Array.from(tbody.querySelectorAll("tr")).filter(
    (row) => row.cells.length === 4,
  );

  rows.sort((a, b) => {
    if (sortValue === "score") {
      /*
        Sort score from highest to lowest.
        parseInt() converts the table text into a number.
      */
      return parseInt(b.cells[1].innerText) - parseInt(a.cells[1].innerText);
    }

    if (sortValue === "highest") {
      /*
        Sort highest score from highest to lowest.
      */
      return parseInt(b.cells[2].innerText) - parseInt(a.cells[2].innerText);
    }

    /*
      Sort date from newest to oldest.

      The visible date text is for users.
      The data-date attribute in the HTML stores the original date value,
      which is easier for JavaScript to convert into a Date object.
    */
    const dateA = new Date(a.cells[3].getAttribute("data-date"));
    const dateB = new Date(b.cells[3].getAttribute("data-date"));

    return dateB - dateA;
  });

  /*
    Append the sorted rows back into the table body.
    This updates the display order on the page.
  */
  rows.forEach((row) => tbody.appendChild(row));
}

/*
  DOMContentLoaded event

  Purpose:
  Runs the JavaScript only after the HTML page has fully loaded.
*/
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  const sortSelect = document.getElementById("sortSelect");

  const adminChartScroll = document.getElementById("adminChartScroll");
  const adminChartCanvas = document.getElementById("adminResultsChart");

  // Create a bar chart for admin player results
  if (
    adminChartCanvas &&
    window.adminResults &&
    window.adminResults.length > 0
  ) {
    // Group results by player and keep each player's highest score
    const playerHighestScores = {};

    window.adminResults.forEach((result) => {
      const playerName = result.player || "Unknown Player";
      const highestScore = Number(result.highest || result.score || 0);

      if (
        !playerHighestScores[playerName] ||
        highestScore > playerHighestScores[playerName]
      ) {
        playerHighestScores[playerName] = highestScore;
      }
    });

    // Convert grouped data into an array and show the top 10 players
    const topPlayers = Object.entries(playerHighestScores)
      .map(([player, score]) => ({
        player,
        score,
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);

    const labels = topPlayers.map((item) => item.player);
    const scores = topPlayers.map((item) => item.score);

    /*
      Stretch the scrolling chart container so wider bar charts can scroll
      horizontally on narrow screens. Uses `labels` which is in scope here.
    */
    if (adminChartScroll && labels.length > 0) {
      adminChartScroll.style.minWidth = `${Math.max(760, labels.length * 90)}px`;
    }

    new Chart(adminChartCanvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Highest Score",
            data: scores,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  }

  /*
    Connect the search input to the searchTable function so the table filters
    live as the admin types.
  */
  if (searchInput) {
    searchInput.addEventListener("keyup", searchTable);
  }

  /*
    Connect the dropdown menu to the sortTable function.
  */
  if (sortSelect) {
    sortSelect.addEventListener("change", sortTable);
  }

  /*
    Connect the explicit Search button so admins who prefer clicking a button
    over typing get the same filtering behaviour.
  */
  const searchBtn = document.getElementById("searchBtn");

  if (searchBtn) {
    searchBtn.addEventListener("click", searchTable);
  }

  /*
    Connect the Reset button to clear the search input and re-show every row.
  */
  const resetBtn = document.getElementById("resetBtn");

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (searchInput) {
        searchInput.value = "";
      }
      searchTable();
    });
  }

  /*
    Sort the table once when the page first loads.
  */
  sortTable();
});
