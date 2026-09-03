// MAP.JS
// Initializes the Leaflet map and handles drawing markers and glowing connections.

const MapController = {
    
    // Initialize the map inside the 'map' div
    init: function() {
        // Default center (Maharashtra approx), zoom level 6
        State.map = L.map('map', {
            zoomControl: false // We hide default controls for a cleaner UI
        }).setView([19.7515, 75.7139], 6);

        // Add a dark theme map tile layer (CartoDB Dark Matter)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
        }).addTo(State.map);

        // Group to hold all hospital markers
        State.markerGroup = L.layerGroup().addTo(State.map);
    },

    // Helper for traffic light capacity color
    getBedColor: function(beds) {
        if (!beds || beds < 10) return '#ef4444'; // Red
        if (beds <= 50) return '#eab308'; // Yellow
        return '#10b981'; // Green
    },

    // Clear existing markers and draw new ones based on the filtered list
    renderMarkers: function() {
        // Remove old markers
        State.markerGroup.clearLayers();

        // Loop through all currently filtered hospitals
        State.filteredHospitals.forEach(hospital => {
            if (!hospital.lat || !hospital.lng) return;

            // Determine marker color based on bed capacity, OR red if we are in ER mode
            let color = this.getBedColor(hospital.totalBeds);
            if (State.currentFilter === 'emergency') {
                color = '#ef4444'; // Make them red in emergency mode
            }

            // Create a custom HTML glowing marker
            const icon = L.divIcon({
                className: 'custom-icon',
                html: `<div class="glow-marker" style="background:${color}; color:${color}"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            // Build the popup content
            const popupContent = `
                <div class="popup-title">${hospital.name}</div>
                <div class="popup-stat"><span>Beds</span><span style="color:${color}">${hospital.totalBeds || 0}</span></div>
                <div class="popup-stat"><span>Doctors</span><span>${hospital.doctors ? hospital.doctors.length : 0}</span></div>
                <div class="popup-stat"><span>Type</span><span style="text-transform:capitalize;">${hospital.type}</span></div>
            `;

            // Add the marker to the map
            const marker = L.marker([hospital.lat, hospital.lng], { icon })
                .bindPopup(popupContent);
                
            State.markerGroup.addLayer(marker);
        });
    },

    // Draw glowing animated lines (used in Emergency mode)
    drawRouteLines: function(targetHospitals) {
        if (!State.userLocation) return;
        
        targetHospitals.forEach(h => {
            if(!h.lat || !h.lng) return;
            const latlngs = [
                State.userLocation,
                [h.lat, h.lng]
            ];
            // Draw a glowing RED line from user to hospital in emergency mode
            L.polyline(latlngs, {
                color: 'var(--color-red)',
                dashArray: '10, 15',
                className: 'route-glow-red' // Styled in map.css
            }).addTo(State.markerGroup);
        });
    }
};
