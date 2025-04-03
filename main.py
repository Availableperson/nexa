<!-- index.html -->
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <title>NEXA</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body { margin: 0; font-family: 'Inter', sans-serif; background: #0d0d0d; color: #fff; display: flex; flex-direction: column; align-items: center; padding: 16px; }
    h1 { font-size: 1.4rem; margin: 10px 0 0 0; }
    input, button { font-size: 1rem; border: none; border-radius: 12px; }
    input { padding: 14px; width: 100%; max-width: 420px; margin-top: 20px; background: #1a1a1a; color: #fff; }
    #requestBtn, #confirmBtn { margin-top: 16px; padding: 16px; background: #00f3b2; color: #000; font-weight: 600; width: 100%; max-width: 420px; border-radius: 16px; cursor: pointer; }
    #status { margin-top: 16px; font-size: 0.95rem; color: #aaa; white-space: pre-wrap; text-align: center; max-width: 420px; }
    .input-wrapper { position: relative; width: 100%; max-width: 420px; }
    #suggestions { display: none; background: #1a1a1a; border-radius: 12px; box-shadow: 0 6px 16px rgba(0,0,0,0.6); position: absolute; z-index: 1000; top: 100%; width: 100%; font-size: 0.95rem; overflow: hidden; }
    #suggestions div { padding: 14px; border-bottom: 1px solid #333; cursor: pointer; transition: background 0.2s; }
    #suggestions div:hover { background: #333; }
    #driverCard { margin-top: 20px; background: #1a1a1a; padding: 16px; border-radius: 14px; max-width: 420px; display: none; width: 100%; }
    #map { height: 280px; width: 100%; max-width: 420px; margin-top: 20px; border-radius: 12px; display: none; }
    .small-text { font-size: 0.85rem; color: #888; }
  </style>
</head>
<body>
  <h1>🚖 NexaRide</h1>
  <div class="input-wrapper">
    <input type="text" id="destination" placeholder="Куда едем?" autocomplete="off" />
    <div id="suggestions"></div>
  </div>
  <button id="requestBtn">🔍 Найти водителя</button>

  <div id="driverCard">
    <div><strong>🚗 Иван (Tesla Model 3)</strong></div>
    <div class="small-text">~2.1 км от вас</div>
    <button id="confirmBtn">✅ Подтвердить поездку</button>
  </div>

  <div id="map"></div>
  <div id="status"></div>

  <script>
    const input = document.getElementById("destination");
    const suggestions = document.getElementById("suggestions");
    const status = document.getElementById("status");
    const driverCard = document.getElementById("driverCard");
    const requestBtn = document.getElementById("requestBtn");
    const confirmBtn = document.getElementById("confirmBtn");
    const mapDiv = document.getElementById("map");

    let debounceTimer, lastQuery = "";
    let coords = null;
    let map, userMarker, driverMarker;

    input.addEventListener("input", () => {
      const query = input.value.trim();
      clearTimeout(debounceTimer);
      if (query.length < 2) {
        suggestions.innerHTML = "";
        suggestions.style.display = "none";
        return;
      }
      debounceTimer = setTimeout(() => searchAddress(query), 300);
    });

    async function searchAddress(query) {
      if (query === lastQuery) return;
      lastQuery = query;
      suggestions.innerHTML = '<div>Поиск...</div>';
      suggestions.style.display = "block";

      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&accept-language=ru`);
        const data = await res.json();
        suggestions.innerHTML = "";

        if (!data.length) {
          suggestions.innerHTML = '<div>Нет результатов</div>';
        } else {
          data.forEach(item => {
            const div = document.createElement("div");
            div.textContent = item.display_name;
            div.onclick = () => {
              input.value = item.display_name;
              suggestions.innerHTML = "";
              suggestions.style.display = "none";
            };
            suggestions.appendChild(div);
          });
        }
      } catch (err) {
        suggestions.innerHTML = '<div>Ошибка загрузки</div>';
      }
    }

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".input-wrapper")) {
        suggestions.style.display = "none";
      }
    });

    requestBtn.addEventListener("click", () => {
      if (!input.value.trim()) {
        status.textContent = "Введите адрес";
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          coords = pos.coords;
          driverCard.style.display = "block";
          status.textContent = "🚕 Водитель найден!";
        },
        () => {
          status.textContent = "❌ Геолокация недоступна";
        }
      );
    });

    confirmBtn.addEventListener("click", async () => {
      status.textContent = "📡 Отправка данных...";
      try {
        const res = await fetch("https://nexa-hvic.onrender.com/ride", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            destination: input.value.trim(),
            latitude: coords.latitude,
            longitude: coords.longitude
          }),
        });

        const data = await res.json();
        if (res.ok) {
          status.textContent = "✅ Поездка подтверждена!";
          mapDiv.style.display = "block";
          setTimeout(initMap, 300);
        } else {
          status.textContent = `❌ ${data.message || "Ошибка"}`;
        }
      } catch (err) {
        status.textContent = "❌ Ошибка отправки: " + err.message;
      }
    });

    function initMap() {
      map = L.map("map").setView([coords.latitude, coords.longitude], 15);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);

      userMarker = L.marker([coords.latitude, coords.longitude])
        .addTo(map)
        .bindPopup("Вы");

      driverMarker = L.marker(
        [coords.latitude + 0.002, coords.longitude + 0.002],
        {
          icon: L.icon({
            iconUrl: "https://cdn-icons-png.flaticon.com/512/148/148842.png",
            iconSize: [32, 32],
          }),
        }
      ).addTo(map).bindPopup("Водитель");
    }
  </script>
</body>
</html>

