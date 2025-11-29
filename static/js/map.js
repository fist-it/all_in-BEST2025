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

var layers = [];

var dzielnice = new L.Shapefile('/static/data/dzielnice.zip', {
  onEachFeature: function(feature, layer) {
    var holder = [];
    // for (var key in feature.properties) {
    //   holder.push(key + ": " + feature.properties[key] + "<br>");
    //   popupContent = holder.join("");
    //   layer.bindPopup(popupContent); // DO KLIKNIECIA
    // };
    liczba_mieszkancow = feature.properties.L_MIESZK;
    if (liczba_mieszkancow > 20000) {
      layer.setStyle({fillColor: "#FF0000"});
    } else if (liczba_mieszkancow > 15000) {
      layer.setStyle({fillColor: "#FF7F00"});
    } else if (liczba_mieszkancow > 10000) {
      layer.setStyle({fillColor: "#FFFF00"});
    } else if (liczba_mieszkancow > 5000) {
      layer.setStyle({fillColor: "#7FFF00"});
    } else {
      layer.setStyle({fillColor: "#00FF00"});
    }
    liczba_mieszkancow_text = "<br><b>Liczba mieszkańców</b>: " + liczba_mieszkancow.toString() + "<br>";
    if (liczba_mieszkancow == null) {
      liczba_mieszkancow_text = "<br><b>Liczba mieszkańców</b>: Brak danych<br>";
    }
    if (liczba_mieszkancow == 0) {
      liczba_mieszkancow_text = "<br><b>Liczba mieszkańców</b>: Brak danych<br>";
    }
      
    popupContent = "<div id='popup'><b>Dzielnica:</b> " + feature.properties.DZIELNICY + liczba_mieszkancow_text + "</div>";

    layer.bindPopup(popupContent); // DO KLIKNIECIA
    layers.push(layer);
    // console.log("adding to map")
  },
  style: function(feature) {
    return {
      color: "#29526E",
      fillOpacity: 0.5,
    }
  },
});
dzielnice.addTo(map);


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
