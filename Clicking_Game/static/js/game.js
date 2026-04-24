// Looks for the play buttons on both the guest page and player dashboard (and elsewhere) and redirects to game page on click.
const playBtns = document.querySelectorAll(".btn-play")
playBtns.forEach(button => {
    button.addEventListener('click', () => {
        window.location.href = "/game";
    })
})