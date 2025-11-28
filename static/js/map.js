// =========================
// 1. LOGIKA MAPY LEAFLET
// =========================
const map = L.map('map').setView([54.4000, 18.5000], 11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

function loadGeoJSON() {
    // 1. Zmieniamy endpoint na nowy
    fetch('/api/data/geojson')
        .then(response => {
            if (response.redirected) return null;
            return response.json();
        })
        .then(data => {
            if (!data) return;
            
            console.log('GeoJSON pobrany z API:', data);
            
            // 2. KLUCZOWY MOMENT: Ładowanie GeoJSON za pomocą L.geoJSON
            L.geoJSON(data, {
                // Ta funkcja stylizuje obiekty GeoJSON
                style: function (feature) {
                    switch (feature.geometry.type) {
                        case 'Polygon':
                            // Styl dla Strefy Czystego Transportu
                            return {
                                color: feature.properties.color || "blue",
                                weight: 3,
                                opacity: 0.6,
                                fillOpacity: 0.2
                            };
                        case 'LineString':
                            // Styl dla Trasy Optymalizacyjnej
                            return {
                                color: feature.properties.color || "red",
                                weight: 5,
                                opacity: 0.8
                            };
                    }
                },
                // Ta funkcja dodaje pop-up po kliknięciu
                onEachFeature: function (feature, layer) {
                    if (feature.properties && feature.properties.name) {
                        layer.bindPopup(`<b>${feature.properties.name}</b><br>${feature.properties.description || ''}`);
                    }
                }
            }).addTo(map);

        })
        .catch(error => console.error('Błąd pobierania GeoJSON:', error));
}

// Uruchomienie nowej funkcji ładowania danych
loadGeoJSON();

// =========================
// 2. LOGIKA CHATBOTA AI
// =========================
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');

function appendMessage(sender, text) {
    const p = document.createElement('p');
    p.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatMessages.appendChild(p);
    // Przewijanie do najnowszej wiadomości
    chatMessages.scrollTop = chatMessages.scrollHeight; 
}

function sendMessage() {
    const message = userInput.value.trim();
    if (message === '') return;

    // 1. Wyświetlenie wiadomości użytkownika
    appendMessage('Ty', message);
    userInput.value = ''; // Wyczyszczenie pola

    // 2. Wysyłanie do API Flask
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        // 3. Wyświetlenie odpowiedzi AI
        appendMessage('AI', data.response);
    })
    .catch(error => {
        appendMessage('AI', 'Przepraszam, wystąpił błąd komunikacji z serwerem.');
        console.error('Błąd API chatbota:', error);
    });
}

// Umożliwienie wysyłania wiadomości przez naciśnięcie Enter
userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});