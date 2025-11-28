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

var dzielnice = new L.Shapefile('/static/data/dzielnice.zip', {
  onEachFeature: function(feature, layer) {
    var holder = [];
    for (var key in feature.properties) {
      holder.push(key + ": " + feature.properties[key] + "<br>");
      popupContent = holder.join("");
      layer.bindPopup(popupContent); // DO KLIKNIECIA
    };
    console.log("adding to map")
    dzielnice.addTo(map);
  },
  style: function(feature) {
    return {
      color: "#29526E",
      fillColor: "#82CDAF",
      fillOpacity: 0.5,
    }
  },
});


events.then(data => {
  data = data.entries();
  events_grouped = [];
  data.forEach(item => {
    var event = item[1]
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
