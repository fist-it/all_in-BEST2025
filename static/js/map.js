const map = L.map('map').setView([54.4000, 18.5000], 11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

map.removeControl(map.zoomControl);
