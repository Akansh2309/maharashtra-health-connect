// UI.JS
// Manages updating the DOM (Document Object Model) like rendering the hospital list and updating stats.

const UIController = {

    // Helper to determine traffic light color based on beds
    getBedColor: function(beds) {
        if (!beds || beds < 10) return 'var(--color-red)';
        if (beds <= 50) return '#eab308'; // Yellow
        return 'var(--color-green)';
    },

    // Render the list of hospitals in the left sidebar
    renderHospitalList: function() {
        const container = document.getElementById('hospital-list');
        container.innerHTML = ''; // Clear out the old list

        // Update the count shown above the list
        document.getElementById('hospital-count').innerHTML = `${State.filteredHospitals.length} <span>hospitals</span>`;

        // If no hospitals match the filter, show a message
        if (State.filteredHospitals.length === 0) {
            container.innerHTML = `<div style="text-align:center;color:var(--text-muted);margin-top:20px;">No hospitals found.</div>`;
            return;
        }

        // Create a card for each hospital
        State.filteredHospitals.forEach(hospital => {
            const div = document.createElement('div');
            div.className = 'hospital-card';
            
            // Generate the badges (e.g. "Govt", "ER")
            let badges = '';
            if (hospital.type === 'government') badges += `<span class="badge govt">Govt</span>`;
            if (hospital.type === 'private') badges += `<span class="badge pvt">Private</span>`;
            if (hospital.hasEmergency) badges += `<span class="badge" style="background:rgba(239, 68, 68, 0.2);color:var(--color-red);">ER</span>`;

            // Calculate distance if user location is known
            let distanceStr = '';
            let dist = 0;
            if (State.userLocation && hospital.lat && hospital.lng) {
                dist = this.calculateDistance(
                    State.userLocation[0], State.userLocation[1],
                    hospital.lat, hospital.lng
                );
                distanceStr = `<i class="fas fa-location-arrow"></i> ${dist.toFixed(1)} km`;
            }

            const bedColor = this.getBedColor(hospital.totalBeds);

            // Put it all together into the HTML structure
            div.innerHTML = `
                <div class="hc-badges">${badges}</div>
                <div class="hc-title">${hospital.name}</div>
                <div style="font-size:0.7rem; color:var(--text-muted); margin-bottom:10px;">${hospital.city || ''}, ${hospital.district || ''}</div>
                <div class="hc-stats">
                    <span style="color:${bedColor}"><i class="fas fa-bed"></i> ${hospital.totalBeds || 0} Beds</span>
                    <span><i class="fas fa-star"></i> ${hospital.rating || 'N/A'}</span>
                    <span>${distanceStr}</span>
                </div>
            `;

            // When clicked, zoom map and open detail panel
            div.onclick = () => {
                if(hospital.lat && hospital.lng) {
                    State.map.flyTo([hospital.lat, hospital.lng], 14, {duration: 1.5});
                }
                this.openDetailPanel(hospital, dist);
            };

            container.appendChild(div);
        });
    },

    // Detail Panel Logic
    openDetailPanel: function(hospital, distance) {
        document.getElementById('detail-overlay').classList.add('active');
        document.getElementById('detail-panel').classList.add('active');

        // Populate Header
        document.getElementById('detail-name').innerText = hospital.name;
        document.getElementById('detail-address').innerText = hospital.address || `${hospital.city}, ${hospital.district}`;

        // Populate Route Bar
        document.getElementById('route-distance').innerText = distance ? distance.toFixed(1) + ' km' : '--';
        document.getElementById('route-time').innerText = distance ? Math.round((distance / 40) * 60) + ' min' : '--';
        document.getElementById('route-phone').innerText = hospital.phone || 'N/A';

        // Populate Content
        const content = document.getElementById('detail-content');
        
        let doctorsHtml = '';
        if (hospital.doctors && hospital.doctors.length > 0) {
            doctorsHtml = hospital.doctors.map(d => `
                <div style="background:rgba(255,255,255,0.05); padding:10px; margin-bottom:10px; border-radius:8px;">
                    <strong>${d.name}</strong><br>
                    <span style="font-size:0.8rem; color:var(--text-muted);">${d.specialization} &bull; ${d.experience} yrs</span>
                </div>
            `).join('');
        } else {
            doctorsHtml = '<p style="color:var(--text-muted); font-size:0.8rem;">No doctors listed.</p>';
        }

        const bedColor = this.getBedColor(hospital.totalBeds);

        content.innerHTML = `
            <div style="margin-bottom:20px;">
                <h3 style="font-size:0.9rem; margin-bottom:10px; color:var(--text-muted);">Overview</h3>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Rating:</span> <strong>${hospital.rating} <i class="fas fa-star" style="color:var(--accent-amber); font-size:0.8rem;"></i> (${hospital.reviewCount} reviews)</strong></div>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Established:</span> <strong>${hospital.established}</strong></div>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Type:</span> <strong style="text-transform:capitalize;">${hospital.type}</strong></div>
            </div>

            <div style="margin-bottom:20px;">
                <h3 style="font-size:0.9rem; margin-bottom:10px; color:var(--text-muted);">Capacity</h3>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Total Beds:</span> <strong style="color:${bedColor}">${hospital.totalBeds}</strong></div>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>ICU Beds:</span> <strong>${hospital.icuBeds}</strong></div>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Ventilators:</span> <strong>${hospital.ventilators}</strong></div>
            </div>

            <div style="margin-bottom:20px;">
                <h3 style="font-size:0.9rem; margin-bottom:10px; color:var(--text-muted);">Key Doctors</h3>
                ${doctorsHtml}
            </div>

            <div style="margin-bottom:20px;">
                <h3 style="font-size:0.9rem; margin-bottom:10px; color:var(--text-muted);">Reviews</h3>
                <div id="reviews-container" style="max-height: 200px; overflow-y: auto; margin-bottom: 10px;">
                    <div style="text-align:center; color:var(--text-muted); font-size:0.8rem; padding:10px;">Loading reviews...</div>
                </div>
                <div class="review-form">
                    <textarea id="review-text" placeholder="Write a review..."></textarea>
                    <div class="review-form-actions">
                        <div class="star-input" id="star-input">
                            <i class="fas fa-star" data-val="1"></i>
                            <i class="fas fa-star" data-val="2"></i>
                            <i class="fas fa-star" data-val="3"></i>
                            <i class="fas fa-star" data-val="4"></i>
                            <i class="fas fa-star" data-val="5"></i>
                        </div>
                        <button class="review-submit" onclick="submitReview('${hospital.id}')">Submit</button>
                    </div>
                </div>
            </div>
        `;

        // Initialize star rating logic
        setTimeout(() => {
            const stars = document.querySelectorAll('#star-input i');
            let currentRating = 0;
            stars.forEach(star => {
                star.onclick = (e) => {
                    currentRating = e.target.getAttribute('data-val');
                    document.getElementById('star-input').setAttribute('data-rating', currentRating);
                    stars.forEach(s => {
                        if (s.getAttribute('data-val') <= currentRating) {
                            s.classList.add('active');
                        } else {
                            s.classList.remove('active');
                        }
                    });
                };
            });
            // Fetch reviews
            if(window.loadReviews) {
                window.loadReviews(hospital.id);
            }
        }, 100);

        // Configure Navigation Button
        const navBtn = document.getElementById('nav-btn');
        navBtn.onclick = () => {
            window.open(`https://www.google.com/maps/dir/?api=1&destination=${hospital.lat},${hospital.lng}`, '_blank');
        };
    },

    closeDetailPanel: function() {
        document.getElementById('detail-overlay').classList.remove('active');
        document.getElementById('detail-panel').classList.remove('active');
    },

    // Update the numbers in the floating stat cards
    updateStats: function() {
        // Total hospitals shown
        document.getElementById('stat-total').innerText = State.filteredHospitals.length;
        
        // Count rural hospitals
        const ruralCount = State.filteredHospitals.filter(h => h.area === 'rural').length;
        document.getElementById('stat-rural').innerText = ruralCount;
        
        // Sum up total available beds
        const totalBeds = State.filteredHospitals.reduce((sum, h) => sum + (h.totalBeds || 0), 0);
        document.getElementById('stat-beds').innerText = totalBeds;
    },

    // Math helper to calculate distance between two GPS coordinates in Kilometers (Haversine formula)
    calculateDistance: function(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
};
