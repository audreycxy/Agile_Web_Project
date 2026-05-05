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

  /*
    Connect the search input to the searchTable function.
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
    Sort the table once when the page first loads.
  */
  sortTable();
});
