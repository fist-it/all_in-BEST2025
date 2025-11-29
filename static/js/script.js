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

function toggleNav() {
    var sidePanel = document.getElementById("sidePanel");
    
    if (sidePanel.style.width === "250px") {
        sidePanel.style.width = "0px";
        sidePanel.style.left = "-200px"; 
    } else {
        sidePanel.style.width = "250px";
        sidePanel.style.left = "16px";
    }
}

function toggleNavAdmin() {
    var sidePanel = document.getElementById("sidePanel2");
    
    if (sidePanel.style.width === "450px") {
        sidePanel.style.width = "0px";
        sidePanel.style.left = "-400px"; 
    } else {
        sidePanel.style.width = "450px";
        sidePanel.style.left = "16px";
    }
}