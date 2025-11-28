const map = L.map('map').setView([54.4000, 18.5000], 11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

async function fetchEvents() {
  const response = await fetch('/static/data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json');
  const data = await response.json();
  return data;
};

var events = fetchEvents();

// L.Shapefile('/static/data/dzielnice.zip').addTo(map);

events.then(data => {
  data = data.entries();
  console.log(data)

  events_grouped = [];
  data.forEach(item => {
    var event = item[1]
    console.log(event.latitude);
    var popupContent = `<div id="popup">
      <img src="${event.imageUrl}" alt="Event Image" width="100%">
      <b>${event.name}</b>
      <br>Uczestnicy: ${event.usersGoing}<br>
      <a href="${event.url}" target="_blank">Link do wydarzenia</a>
      </div>`;
    L.marker([event.latitude, event.longitude]).addTo(map).bindPopup(popupContent);
  })
});

map.removeControl(map.zoomControl);
