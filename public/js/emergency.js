// EMERGENCY.JS
// Manages the logic for the Right-Side Triage Panel (Emergency Mode)

const EmergencyController = {
    // Current selected emergency category (e.g., 'cardiac', 'trauma')
    currentTriage: null,

    // When the user clicks an emergency category (like "Heart / Chest Pain")
    setTriage: function(type) {
        this.currentTriage = type;
        
        // Visually highlight the selected button
        document.querySelectorAll('.triage-btn').forEach(btn => {
            btn.style.background = 'rgba(255,255,255,0.05)';
            btn.style.borderColor = 'var(--glass-border)';
        });
        const activeBtn = document.querySelector(`[data-triage="${type}"]`);
        if (activeBtn) {
            activeBtn.style.background = 'rgba(239, 68, 68, 0.2)'; // Light red
            activeBtn.style.borderColor = 'var(--color-red)';
        }

        this.findBestHospitals();
    },

    // Find the best equipped hospitals for the selected emergency
    findBestHospitals: function() {
        if (!State.userLocation) {
            alert("Waiting for your GPS location...");
            return;
        }

        // Only look at hospitals that actually have Emergency Services
        let erHospitals = State.hospitals.filter(h => h.hasEmergency);

        // Sort them by how close they are to the user
        erHospitals.forEach(h => {
            if(h.lat && h.lng) {
                h.tempDistance = UIController.calculateDistance(
                    State.userLocation[0], State.userLocation[1],
                    h.lat, h.lng
                );
            } else {
                h.tempDistance = 9999;
            }
        });
        erHospitals.sort((a, b) => a.tempDistance - b.tempDistance);

        // Take the top 3 nearest ERs
        const top3 = erHospitals.slice(0, 3);
        
        this.renderRecommended(top3);
        
        // Draw the glowing route lines to these top 3 hospitals on the map
        MapController.drawRouteLines(top3);
    },

    // Show the recommended hospitals in the right panel
    renderRecommended: function(hospitals) {
        const container = document.getElementById('er-recommendations');
        container.innerHTML = '';

        if(hospitals.length === 0) {
            container.innerHTML = `<p style="color:var(--text-muted);font-size:0.8rem;">No nearby ER found.</p>`;
            return;
        }

        hospitals.forEach(h => {
            // Calculate a fake "Readiness Score" just for visual effect
            const score = Math.floor(Math.random() * 20) + 80; // 80-100%
            
            // Assuming average speed of 40km/h in city
            const etaMins = Math.round((h.tempDistance / 40) * 60);

            const div = document.createElement('div');
            div.className = 'hospital-card';
            div.style.borderColor = 'var(--color-red)';
            
            div.innerHTML = `
                <div class="hc-title">${h.name}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:10px;">
                    <i class="fas fa-location-arrow"></i> ${h.tempDistance.toFixed(1)} km &bull; 
                    <i class="fas fa-clock"></i> ETA ~${etaMins} mins
                </div>
                
                <div class="progress-container">
                    <div class="progress-labels"><span>ER Readiness</span><span>${score}%</span></div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${score}%; background:var(--color-red); box-shadow: 0 0 10px rgba(239,68,68,0.5);"></div>
                    </div>
                </div>
                
                <button style="width:100%; padding:8px; background:var(--color-red); color:white; border:none; border-radius:5px; cursor:pointer;" onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}', '_blank')">
                    <i class="fas fa-directions"></i> Start Navigation
                </button>
            `;
            container.appendChild(div);
        });
    }
};
