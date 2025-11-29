// script.js

// Pobieramy elementy
const openPanelButton = document.getElementById('openPanel');
const closePanelButton = document.getElementById('closePanel');
const sidePanel = document.getElementById('sidePanel');

// Funkcja otwierająca okienko
openPanelButton.addEventListener('click', () => {
    sidePanel.classList.add('open');
});

// Funkcja zamykająca okienko
closePanelButton.addEventListener('click', () => {
    sidePanel.classList.remove('open');
});

function openNav() {
    document.getElementById("sidePanel").style.width = "250px";
    document.getElementById("sidePanel").style.left = "0px";
}
function closeNav() {
    document.getElementById("sidePanel").style.width = "0px";
    document.getElementById("sidePanel").style.left = "-200px";
}