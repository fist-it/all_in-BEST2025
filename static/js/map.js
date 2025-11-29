const map = L.map('map').setView([54.4000, 18.5000], 11);
var markersLayer = L.layerGroup().addTo(map);
map.removeControl(map.zoomControl);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

async function fetchEvents() {
  const response = await fetch('/static/data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json');
  const data = await response.json();
  return data;
}

var events = fetchEvents();
var clickedDistrictInfo = null;
var layers = [];
var markersById = {};

var dzielnice = new L.Shapefile('/static/data/dzielnice.zip', {
    onEachFeature: function(feature, layer) {
        var l_m = feature.properties.L_MIESZK;
        var color = "#00FF00";
        if (l_m > 20000) color = "#FF0000";
        else if (l_m > 15000) color = "#FF7F00";
        else if (l_m > 10000) color = "#FFFF00";
        else if (l_m > 5000) color = "#7FFF00";

        layer.setStyle({
            fillColor: color,
            color: "#29526E",
            weight: 1,
            fillOpacity: 0.3
        });

        layer.on('click', function(e) {
            var popText = (l_m > 0) ? l_m.toString() : "Brak danych";
            clickedDistrictInfo = `
                <div style="background:#f0f8ff; padding:5px; border-radius:4px; margin-bottom:5px; border:1px solid #ccc;">
                    <b>Dzielnica: ${feature.properties.DZIELNICY}</b><br>
                    Mieszkańców: ${popText}
                </div>
            `;
            
        });
    }
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

// ostatnie wybrane coordy
var selectedCoords = null;
var is_popup_open = false;
var allEvents = []; // Przechowuje wszystkie zdarzenia
var existingMarkers = {};

map.on('click', function(e) {
    selectedCoords = e.latlng;
    
    var content = '<div class="popup-menu">';
    
    if (clickedDistrictInfo) {
        content += clickedDistrictInfo;
        clickedDistrictInfo = null;
    }

    var lat = e.latlng.lat.toFixed(5);
    var lng = e.latlng.lng.toFixed(5);
    content += `<div style="font-size:10px; color:#888; margin:5px 0;">${lat}, ${lng}</div>`;

    content += `
        <button class="btn-add" onclick="openAddEventModal()">➕ Dodaj zdarzenie</button>
        <button class="btn-search" onclick="searchNearby()">🔍 Szukaj w promieniu 1km</button>
        <button onclick="copyCoords()">📋 Kopiuj współrzędne</button>
    </div>`;

    L.popup()
        .setLatLng(e.latlng)
        .setContent(content)
        .openOn(map);
});

function openAddEventModal() {
    if (!selectedCoords) return;
    map.closePopup();
    
    document.getElementById('input-lat').value = selectedCoords.lat;
    document.getElementById('input-lng').value = selectedCoords.lng;
    document.getElementById('display-coords').innerText = 
        selectedCoords.lat.toFixed(5) + ", " + selectedCoords.lng.toFixed(5);
    
    document.getElementById('eventModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('eventModal').style.display = 'none';
    document.getElementById('addEventForm').reset();
}

document.getElementById('addEventForm').addEventListener('submit', function(e) {
    e.preventDefault();

    var formData = new FormData(this);

    fetch('/api/add_event', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json().then(data => ({status: response.status, body: data})))
    .then(result => {
        if (result.status === 201) {
            closeModal();
            updateMap();
        } else {
            alert("Błąd: " + (result.body.error || "Coś poszło nie tak"));
            if (result.status === 401) {
                window.location.href = "/login";
            }
        }
    })
    .catch(err => {
        console.error("Error:", err);
        alert("Błąd połączenia z serwerem.");
    });
});

function createMarker(event) {
    if (!event.latitude || !event.longitude) return;

    var marker;
    var type = event.event_type || 'static'; 

    if (type === 'live') {
        var customIcon = L.divIcon({
            className: 'pulsating-circle',
            html: `<div></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]  
        });
        marker = L.marker([event.latitude, event.longitude], {icon: customIcon});
    } else {
        var customIcon = L.divIcon({
            className: 'custom-icon-container',
            html: `<div class="static-marker"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        marker = L.marker([event.latitude, event.longitude], {icon: customIcon});
    }
        
    var deleteButtonHtml = '';
    if (event.is_mine) {
        deleteButtonHtml = `
            <div style="margin-top: 10px; border-top: 1px solid #eee; padding-top: 5px;">
                <button onclick="deleteEvent(${event.id})" 
                        style="background:none; border:none; color:red; cursor:pointer; font-size:11px; text-decoration:underline;">
                    🗑️ Usuń moje zgłoszenie
                </button>
            </div>
        `;
    }

    var popupContent = `
        <div style="text-align:center; min-width:160px;">
            <strong style="font-size:14px;">${event.name}</strong><br>
            <span style="color:gray; font-size:11px;">${event['location.name']}</span>
            <hr style="margin:5px 0;">
            <div style="margin-bottom:5px;">
                Głosów: <b id="vote-count-${event.id}">${event.upvoteCount || 0}</b>
            </div>
            <div>
                <button onclick="vote(${event.id}, 'up')" style="cursor:pointer; background:#d4edda; border:1px solid #c3e6cb; padding:2px 8px; border-radius:4px;">👍</button>
                <button onclick="vote(${event.id}, 'down')" style="cursor:pointer; background:#f8d7da; border:1px solid #f5c6cb; padding:2px 8px; border-radius:4px;">👎</button>
            </div>
            ${deleteButtonHtml}
        </div>
    `;

    marker.bindPopup(popupContent);
    
    markersLayer.addLayer(marker);
    
    markersById[event.id] = marker; 
}

function searchNearby() {
    if (!selectedCoords) return;
    map.closePopup();

    var lat = selectedCoords.lat;
    var lng = selectedCoords.lng;
    var radius = 1000; // metry

    markersLayer.clearLayers();

    var foundCount = 0;
    
    allEvents.forEach(event => {
        if (!event.latitude || !event.longitude) return;

        var eventLatLng = L.latLng(event.latitude, event.longitude);
        var dist = eventLatLng.distanceTo(selectedCoords); 

        if (dist <= radius) {
            createMarker(event);
            foundCount++;
        }
    });

    var circle = L.circle(selectedCoords, {
        radius: radius,
        color: '#29526E',
        fillColor: '#29526E',
        fillOpacity: 0.1
    });
    resetButton.addTo(map);
    markersLayer.addLayer(circle);

    map.fitBounds(circle.getBounds());
}

function copyCoords() {
    var text = `${selectedCoords.lat}, ${selectedCoords.lng}`;
    navigator.clipboard.writeText(text).then(() => {
        map.closePopup();
    });
}

function updateMap() {
    fetch('/api/events/user')
        .then(response => response.json())
        .then(events => {
            allEvents = events; 
            markersLayer.clearLayers();
            markersById = {};

            events.forEach(event => {
                createMarker(event);
            });
        })
        .catch(err => console.error("Błąd pobierania eventów:", err));
}

function vote(id, type) {
  fetch('/api/vote', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({event_id: id, vote: type})
  }).then(res => res.json().then(d => {
      if(d.new_score !== undefined) {
          var el = document.getElementById('vote-count-'+id);
          if(el) el.innerText = d.new_score;
      } else { alert(d.error); }
  }));
}

updateMap();

function deleteEvent(eventId) {
    if (!confirm("Czy na pewno chcesz usunąć to zgłoszenie? Tego nie da się cofnąć.")) {
        return;
    }

    map.closePopup();

    fetch(`/api/delete_event/${eventId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => {
        if (res.status === 200) {
            if (markersById[eventId]) {
                markersLayer.removeLayer(markersById[eventId]);
                delete markersById[eventId];
            }
            updateMap(); 
        } else {
            res.json().then(data => {
                alert("Błąd: " + (data.error || "Nie udało się usunąć."));
            });
        }
    })
    .catch(err => {
        console.error("Błąd sieci:", err);
        alert("Wystąpił błąd połączenia.");
    });
}
var resetButton = L.control({position: 'bottomleft'});

resetButton.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'reset-btn-container');
    div.innerHTML = '<button class="reset-control" onclick="resetSearch()">❌ Wyczyść filtr</button>';
    return div;
};

function resetSearch() {
    resetButton.remove(); 
    isSearchActive = false;
    
    markersLayer.clearLayers();
    existingMarkers = {}
    updateMap();
}

