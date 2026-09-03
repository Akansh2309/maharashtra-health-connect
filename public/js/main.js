// MAIN.JS
// The core brain of the frontend. It fetches data, sets up listeners, and starts the app.

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Initialize the Leaflet Map
    MapController.init();

    // Fetch User Session for Profile
    fetch('/api/session')
        .then(res => res.json())
        .then(data => {
            if (data && data.user) {
                document.getElementById('profile-name').textContent = data.user.name;
                document.getElementById('dropdown-name').textContent = data.user.name;
                document.getElementById('dropdown-email').textContent = data.user.email;
                document.getElementById('dropdown-role').textContent = data.user.role;
                // Generate a colored avatar based on the name
                document.getElementById('profile-img').src = `https://ui-avatars.com/api/?name=${encodeURIComponent(data.user.name)}&background=random`;
            }
        })
        .catch(err => console.error("Could not fetch session:", err));

    // 2. Try to get the user's GPS Location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Success! We found the user
                State.userLocation = [position.coords.latitude, position.coords.longitude];
                
                // Add a small pulsing blue dot for the user's location
                const userIcon = L.divIcon({
                    className: 'custom-icon',
                    html: `<div class="glow-marker" style="background:#3b82f6; color:#3b82f6"></div>`,
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                });
                L.marker(State.userLocation, {icon: userIcon})
                 .addTo(State.map)
                 .bindPopup("<b>You are here</b>");

                // Center map on user
                State.map.setView(State.userLocation, 12);
                
                // Pre-calculate distances for all hospitals
                if (State.hospitals) {
                    State.hospitals.forEach(h => {
                        if (h.lat && h.lng) {
                            h.distance = UIController.calculateDistance(
                                State.userLocation[0], State.userLocation[1],
                                h.lat, h.lng
                            );
                        } else {
                            h.distance = 9999;
                        }
                    });
                }
                
                applyFilters();
            },
            (err) => {
                console.log("Location access denied or failed.", err);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    // 3. Fetch the hospital data from the backend/JSON
    fetch('/js/hospitals-data.json')
        .then(response => response.json())
        .then(data => {
            // Save data to global state
            State.hospitals = data;
            
            // Calculate distances if location already fetched
            if (State.userLocation) {
                State.hospitals.forEach(h => {
                    if (h.lat && h.lng) {
                        h.distance = UIController.calculateDistance(
                            State.userLocation[0], State.userLocation[1],
                            h.lat, h.lng
                        );
                    } else {
                        h.distance = 9999;
                    }
                });
            } else {
                State.hospitals.forEach(h => h.distance = 9999);
            }

            applyFilters();
        })
        .catch(err => console.error("Error loading hospitals:", err));

    // 4. Unified Filter Logic
    function applyFilters() {
        if (!State.hospitals) return;

        let result = State.hospitals;

        // A. Search Term
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value) {
            const term = searchInput.value.toLowerCase();
            result = result.filter(h => {
                const nameMatch = h.name.toLowerCase().includes(term);
                const cityMatch = h.city && h.city.toLowerCase().includes(term);
                const distMatch = h.district && h.district.toLowerCase().includes(term);
                return nameMatch || cityMatch || distMatch;
            });
        }

        // B. Quick Tabs
        if (State.currentFilter === 'government') {
            result = result.filter(h => h.type === 'government');
        } else if (State.currentFilter === 'private') {
            result = result.filter(h => h.type === 'private');
        } else if (State.currentFilter === 'rural') {
            result = result.filter(h => h.area === 'rural');
        } else if (State.currentFilter === 'emergency') {
            result = result.filter(h => h.hasEmergency === true);
        }

        // C. Advanced Filters (Specialist)
        const specEl = document.getElementById('filter-specialist');
        if (specEl && specEl.value !== 'all') {
            const reqSpec = specEl.value; // e.g. 'cardiology'
            result = result.filter(h => {
                if (!h.doctors) return false;
                return h.doctors.some(d => d.specialization && d.specialization.toLowerCase().includes(reqSpec));
            });
        }

        // D. Advanced Filters (Budget)
        const budgetEl = document.getElementById('filter-budget');
        if (budgetEl && budgetEl.value !== 'all') {
            const b = budgetEl.value;
            if (b === 'free') {
                result = result.filter(h => h.type === 'government'); // Proxy for free
            } else if (b === 'high') {
                result = result.filter(h => h.rating >= 4.5 && h.type === 'private');
            } else if (b === 'low') {
                // Just an example logic for low budget
                result = result.filter(h => h.rating < 4.5 || h.type === 'government');
            }
        }

        // E. Sorting
        const sortEl = document.getElementById('sort-options');
        if (sortEl && sortEl.value !== 'none') {
            const s = sortEl.value;
            if (s === 'distance') {
                result.sort((a, b) => a.distance - b.distance);
            } else if (s === 'beds') {
                result.sort((a, b) => (b.totalBeds || 0) - (a.totalBeds || 0));
            } else if (s === 'rating') {
                result.sort((a, b) => (b.rating || 0) - (a.rating || 0));
            }
        }

        State.filteredHospitals = result;

        // Re-render UI
        MapController.renderMarkers();
        UIController.renderHospitalList();
        UIController.updateStats();
    }

    // Attach Event Listeners
    document.getElementById('search-input')?.addEventListener('input', applyFilters);
    document.getElementById('filter-specialist')?.addEventListener('change', applyFilters);
    document.getElementById('filter-budget')?.addEventListener('change', applyFilters);
    document.getElementById('sort-options')?.addEventListener('change', applyFilters);

    // Filter Tabs
    const tabs = document.querySelectorAll('.filter-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            State.currentFilter = e.target.dataset.filter;
            applyFilters();
        });
    });
});

// Review System
window.loadReviews = function(hospitalId) {
    fetch('/api/reviews/' + hospitalId)
        .then(res => res.json())
        .then(reviews => {
            const container = document.getElementById('reviews-container');
            if(!container) return;
            
            if(!reviews || reviews.length === 0) {
                container.innerHTML = '<div style="text-align:center; color:var(--text-muted); font-size:0.8rem; padding:10px;">No reviews yet. Be the first!</div>';
                return;
            }
            
            container.innerHTML = reviews.map(r => `
                <div class="review-card">
                    <div class="review-header">
                        <span class="review-name">${r.user}</span>
                        <span class="review-date">${r.date || 'Just now'}</span>
                    </div>
                    <div class="review-stars">
                        ${Array(5).fill().map((_, i) => `<i class="fas fa-star" style="color: ${i < r.rating ? 'var(--accent-amber)' : 'var(--border-glass)'}; font-size:0.6rem;"></i>`).join('')}
                    </div>
                    <div class="review-text">${r.text}</div>
                </div>
            `).join('');
        })
        .catch(err => console.error("Could not load reviews", err));
};

window.submitReview = function(hospitalId) {
    const text = document.getElementById('review-text').value;
    const rating = document.getElementById('star-input').getAttribute('data-rating');
    
    if(!rating || !text) {
        alert("Please provide both a rating and a review.");
        return;
    }
    
    fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hospital_id: parseInt(hospitalId), rating: parseInt(rating), text: text })
    })
    .then(res => {
        if(!res.ok) {
            if(res.status === 401) throw new Error("Please log in to submit a review.");
            throw new Error("Failed to submit review");
        }
        return res.json();
    })
    .then(data => {
        document.getElementById('review-text').value = '';
        document.getElementById('star-input').setAttribute('data-rating', '0');
        document.querySelectorAll('#star-input i').forEach(s => s.classList.remove('active'));
        
        // Reload reviews
        window.loadReviews(hospitalId);
    })
    .catch(err => {
        alert(err.message);
    });
};
