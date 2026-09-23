/*
 * Maharashtra Health Connect — App Logic
 * Copyrights are claimed by MH Connect Team. Developed by MH Connect Team.
 * SIH 2026 — PS#26133 | Government of Maharashtra
 * 
 * Data Source: Hospital data sourced from the Maharashtra Open Data Portal 
 * and National Health Mission (NHM) open datasets.
 */

const state = {
  userLat: 19.076,
  userLng: 72.8777,
  hospitals: [],
  mlBeds: { general: 50, icu: 30, ventilator: 20 },
  filteredHospitals: [],
  map: null,
  userMarker: null,
  markers: [],
  routeLayer: null,
  currentFilter: 'all',
  currentSort: 'distance',
  currentSpecialty: '',
  currentBudget: '',
  searchQuery: '',
  userName: 'User',
};

// ====== INIT ======
async function init() {
  updateLoadingStatus(t('checking_auth'));
  try {
    const sRes = await fetch('/api/session');
    const sData = await sRes.json();
    if (!sData.authenticated) { window.location.href = '/interface.html'; return; }
    state.userName = sData.name;
    if (document.getElementById('ud-name')) document.getElementById('ud-name').textContent = sData.name;
    if (document.getElementById('ud-name-dash')) document.getElementById('ud-name-dash').textContent = sData.name;
    if (document.getElementById('ud-role-dash')) document.getElementById('ud-role-dash').textContent = sData.role === 'admin' ? t('administrator') : (sData.role === 'patient' ? 'Patient / Caregiver' : 'ASHA / Frontline Worker');
    if (document.getElementById('ud-allergies-dash') && sData.allergies) {
        document.getElementById('ud-allergies-dash').textContent = sData.allergies;
    }
    if (document.getElementById('ud-medical-history-dash') && sData.medical_history) {
        document.getElementById('ud-medical-history-dash').textContent = sData.medical_history;
    }
  } catch(e) { window.location.href = '/interface.html'; return; }

  updateLoadingStatus(t('loading_hospitals'));
  try {
    const hRes = await fetch('/api/facilities'); // 150 facilities
    state.hospitals = await hRes.json();
    
    // Fetch ML Bed Predictions
    const d = new Date();
    const bRes = await fetch(`/api/predict-beds?hour=${d.getHours()}&month=${d.getMonth()+1}&dayofweek=${d.getDay()}`);
    if(bRes.ok) {
       const bedData = await bRes.json();
       if(bedData.predictions) state.mlBeds = bedData.predictions;
    }
  } catch(e) { console.error('Failed to load hospitals/beds', e); }

  updateLoadingStatus(t('detecting_location'));
  await detectLocation();

  updateLoadingStatus(t('initializing_map'));
  initMap();
  computeDistances();
  populateSpecialtyFilter();
  applyFiltersAndSort();
  bindEvents();
  updateStats();

  // Refresh live bed availability every 1 hour (3600000 ms)
  setInterval(() => {
    applyFiltersAndSort();
    const activeHospitalId = document.getElementById('detail-name').dataset.id;
    if (activeHospitalId && document.getElementById('detail-panel').classList.contains('open')) {
      const h = state.hospitals.find(x => x.id === parseInt(activeHospitalId));
      if (h) openDetail(h);
    }
  }, 3600000);

  
}

function updateLoadingStatus(txt) {
  const el = document.getElementById('loading-status');
  if (el) el.textContent = txt;
}

// ====== LOCATION ======
function detectLocation() {
  return new Promise(resolve => {
    if (!navigator.geolocation) { resolve(); return; }
    navigator.geolocation.getCurrentPosition(
      pos => {
        state.userLat = pos.coords.latitude;
        state.userLng = pos.coords.longitude;
        reverseGeocode(state.userLat, state.userLng);
        resolve();
      },
      () => {
        document.getElementById('user-location-text').innerHTML = `<strong>Mumbai, Maharashtra</strong> ${t('default_location')}`;
        resolve();
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

async function reverseGeocode(lat, lng) {
  try {
    const r = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`);
    const d = await r.json();
    const parts = [d.address?.suburb || d.address?.village || '', d.address?.city || d.address?.town || d.address?.county || '', d.address?.state || ''].filter(Boolean);
    document.getElementById('user-location-text').innerHTML = `<strong>${parts.join(', ')}</strong>`;
  } catch(e) {
    document.getElementById('user-location-text').innerHTML = `<strong>${lat.toFixed(4)}, ${lng.toFixed(4)}</strong>`;
  }
}

// ====== MAP ======
function initMap() {
  state.map = L.map('map', { zoomControl: false, attributionControl: false }).setView([state.userLat, state.userLng], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, subdomains: 'abcd'
  }).addTo(state.map);
  L.control.zoom({ position: 'bottomright' }).addTo(state.map);

  const userIcon = L.divIcon({
    className: 'user-marker',
    html: '<div style="width:16px;height:16px;background:#34d399;border-radius:50%;border:3px solid #fff;box-shadow:0 0 12px rgba(52,211,153,.6),0 0 30px rgba(52,211,153,.3);animation:pulse 2s infinite"></div>',
    iconSize: [16, 16], iconAnchor: [8, 8]
  });
  state.userMarker = L.marker([state.userLat, state.userLng], { icon: userIcon }).addTo(state.map);
  state.userMarker.bindPopup('<strong> Your Location</strong>');

  addHospitalMarkers();
}

function addHospitalMarkers() {
  state.markers.forEach(m => state.map.removeLayer(m));
  state.markers = [];

  state.filteredHospitals.forEach(h => {
    const color = h.type === 'government' ? '#34d399' : '#818cf8';
    const areaIcon = h.area === 'rural' ? '' : '';
    const icon = L.divIcon({
      className: 'hospital-marker',
      html: `<div style="width:12px;height:12px;background:${color};border-radius:50%;border:2px solid #fff;box-shadow:0 0 8px ${color}80"></div>`,
      iconSize: [12, 12], iconAnchor: [6, 6]
    });
    const marker = L.marker([h.lat, h.lng], { icon }).addTo(state.map);
    marker.bindPopup(`<strong>${areaIcon}${h.name}</strong><br>${h.city}`);
    marker.on('click', () => openDetail(h));
    state.markers.push(marker);
  });
}

// ====== DISTANCE ======
function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLng/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

function computeDistances() {
  state.hospitals.forEach(h => {
    h._distance = haversine(state.userLat, state.userLng, h.lat, h.lng);
  });
}

// ====== SPECIALTY FILTER ======
function populateSpecialtyFilter() {
  const specialties = new Set();
  state.hospitals.forEach(h => {
    h.doctors.forEach(d => specialties.add(d.specialization));
  });
  const sel = document.getElementById('filter-specialty');
  [...specialties].sort().forEach(s => {
    const opt = document.createElement('option');
    opt.value = s; opt.textContent = s;
    sel.appendChild(opt);
  });
}

// ====== FILTERS & SORT ======
function applyFiltersAndSort() {
  let list = [...state.hospitals];

  // Type/area filter
  if (state.currentFilter === 'government') list = list.filter(h => h.type === 'government');
  else if (state.currentFilter === 'private') list = list.filter(h => h.type === 'private');
  else if (state.currentFilter === 'rural') list = list.filter(h => h.area === 'rural');
  else if (state.currentFilter === 'emergency') list = list.filter(h => h.hasEmergency);

  // Specialty filter
  if (state.currentSpecialty) {
    list = list.filter(h => h.doctors.some(d => d.specialization === state.currentSpecialty));
  }

  // Budget filter (private only)
  if (state.currentBudget) {
    const [minB, maxB] = state.currentBudget.split('-').map(Number);
    list = list.filter(h => {
      if (!h.budget) return false; // exclude govt from budget filter
      return h.budget.minEstimate <= maxB && h.budget.maxEstimate >= minB;
    });
  }

  // Search
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    list = list.filter(h =>
      h.name.toLowerCase().includes(q) ||
      h.city.toLowerCase().includes(q) ||
      h.district.toLowerCase().includes(q) ||
      h.specializations.some(s => s.toLowerCase().includes(q)) ||
      h.doctors.some(d => d.name.toLowerCase().includes(q) || d.specialization.toLowerCase().includes(q))
    );
  }

  // Sort
  if (state.currentSort === 'distance') list.sort((a, b) => a._distance - b._distance);
  else if (state.currentSort === 'rating') list.sort((a, b) => b.rating - a.rating);
  else if (state.currentSort === 'beds') list.sort((a, b) => b.totalBeds - a.totalBeds);

  state.filteredHospitals = list;
  renderHospitalList();
  addHospitalMarkers();
  updateStats();
}

function updateStats() {
  document.getElementById('stat-total').textContent = state.hospitals.length;
  document.getElementById('stat-nearby').textContent = state.hospitals.filter(h => h._distance <= 25).length;
  document.getElementById('stat-rural').textContent = state.hospitals.filter(h => h.area === 'rural').length;
  document.getElementById('stat-beds').textContent = state.hospitals.reduce((s, h) => s + h.totalBeds, 0).toLocaleString();
  document.getElementById('hospital-count').textContent = `${state.filteredHospitals.length} ${t('hospitals')}`;
}

// ====== RENDER LIST ======
function toggleElaborate(id, event) {
  event.stopPropagation();
  const content = document.getElementById(`elaborate-${id}`);
  const icon = document.getElementById(`icon-${id}`);
  if(content.style.display === 'none') {
    content.style.display = 'block';
    icon.style.transform = 'rotate(180deg)';
  } else {
    content.style.display = 'none';
    icon.style.transform = 'rotate(0deg)';
  }
}

function renderHospitalList() {
  const container = document.getElementById('hospital-list');
  if (state.filteredHospitals.length === 0) {
    container.innerHTML = `<div style="text-align:center;padding:30px;color:var(--text-muted);font-size:.82rem"><i class="fas fa-search" style="font-size:2rem;margin-bottom:10px;display:block;opacity:.3"></i>${t('no_hospitals_found')}</div>`;
    return;
  }

  container.innerHTML = state.filteredHospitals.map((h, i) => {
    const dist = h._distance < 1 ? `${(h._distance * 1000).toFixed(0)}m` : `${h._distance.toFixed(1)} km`;
    const typeCls = h.type === 'government' ? 'govt' : 'pvt';
    const typeLabel = h.type === 'government' ? t('govt') : t('pvt');
    const areaCls = h.area;
    const areaLabel = h.area === 'rural' ? t('rural_tag') : h.area === 'semi-urban' ? t('semi_urban') : t('urban');
    const stars = ''.repeat(Math.round(h.rating)) + ''.repeat(5 - Math.round(h.rating));
    const budgetHtml = h.budget ? `<span class="hc-budget">₹${(h.budget.minEstimate/1000).toFixed(0)}k — ₹${(h.budget.maxEstimate/1000).toFixed(0)}k</span>` : '';

    // Dynamic bed availability simulation
    const avail = Math.floor(h.totalBeds * (state.mlBeds.general / 100));

    return `
      <div class="hospital-card" style="animation-delay:${i * 40}ms">
        <div class="hc-top">
          <div>
            <div class="hc-name">${h.name}</div>
          </div>
          <div style="display:flex;gap:4px;align-items:center">
            <span class="hc-area-tag ${areaCls}">${areaLabel}</span>
            <span class="hc-type ${typeCls}">${typeLabel}</span>
          </div>
        </div>
        
        <!-- DEFAULT VIEW: Very simple, just address, specialist count, distance -->
        <div class="hc-info" style="font-size: 1rem; color: var(--text-primary); margin: 10px 0;">
          <div style="margin-bottom: 6px;"><i class="fas fa-map-marker-alt" style="color:var(--accent-primary)"></i> ${h.address}, ${h.city}, ${h.district}</div>
          <div style="margin-bottom: 6px;"><i class="fas fa-user-md" style="color:var(--accent-primary)"></i> ${h.doctors.length} Specialists Available</div>
          <div style="margin-bottom: 6px;"><i class="fas fa-route" style="color:var(--accent-primary)"></i> Distance: <strong>${dist}</strong></div>
        </div>
        
        <div class="hc-bottom" style="margin-top: 15px; border-top: 1px solid var(--border-glass); padding-top: 10px;">
          <button class="btn-elaborate" onclick="openDetail(state.hospitals.find(x=>x.id===${h.id}))" style="width: 100%; padding: 12px; background: var(--bg-glass-hover); border: 1px solid var(--border-active); color: var(--text-primary); border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
            <span data-i18n="elaborate">Elaborate (Details & Map)</span>
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>`;
  }).join('');
}

// ====== DETAIL PANEL ======
function openDetail(h) {
  const nameEl = document.getElementById('detail-name');
  nameEl.textContent = h.name;
  nameEl.dataset.id = h.id;
  document.getElementById('detail-address').textContent = h.address;
  document.getElementById('detail-overlay').classList.add('show');
  document.getElementById('detail-panel').classList.add('open');

  // Route
  showRoute(h);

  // Content
  const genAvail = Math.floor(h.totalBeds * (state.mlBeds.general / 100));
  const icuAvail = Math.floor(h.icuBeds * (state.mlBeds.icu / 100));
  const ventAvail = Math.floor(h.ventilators * (state.mlBeds.ventilator / 100));
  const genPct = (genAvail / h.totalBeds * 100).toFixed(0);
  const icuPct = h.icuBeds > 0 ? (icuAvail / h.icuBeds * 100).toFixed(0) : 0;
  const ventPct = h.ventilators > 0 ? (ventAvail / h.ventilators * 100).toFixed(0) : 0;

  const getBarColor = pct => pct > 50 ? 'green' : pct > 20 ? 'amber' : 'red';

  let html = '';

  // Quick Actions
  html += `<div class="detail-actions">
    <a href="tel:${h.phone}" class="detail-action-btn"><i class="fas fa-phone"></i><span>${t('call_hospital')}</span></a>
    <a href="tel:108" class="detail-action-btn emergency"><i class="fas fa-ambulance"></i><span>${t('call_108')}</span></a>
    <a href="https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}" target="_blank" class="detail-action-btn"><i class="fas fa-directions"></i><span>${t('google_maps')}</span></a>
  </div>`;

  // Info
  html += `<div class="detail-section">
    <div class="detail-section-title"><i class="fas fa-info-circle"></i> ${t('hospital_info')}</div>
    <div style="display:flex;flex-wrap:wrap;gap:12px;font-size:.72rem;color:var(--text-secondary)">
      <span><strong>${t('type')}:</strong> ${h.type === 'government' ? t('govt_full') : t('pvt_full')}</span>
      <span><strong>${t('area')}:</strong> ${h.area === 'rural' ? t('rural_full') : h.area === 'semi-urban' ? t('semi_urban_full') : t('urban_full')}</span>
      <span><strong>${t('district')}:</strong> ${h.district}</span>
      <span><strong>Est:</strong> ${h.established}</span>
      <span><strong>Phone:</strong> <a href="tel:${h.phone}" style="color:var(--accent-primary);text-decoration:none">${h.phone}</a></span>
    </div>
  </div>`;

  // Beds
  html += `<div class="detail-section">
    <div class="detail-section-title"><i class="fas fa-bed"></i> ${t('bed_availability')}</div>
    <div class="bed-bar"><div class="bed-bar-label"><span>${t('general_beds')}</span><span style="color:var(--accent-${getBarColor(genPct)})">${genAvail} / ${h.totalBeds}</span></div><div class="bed-bar-track"><div class="bed-bar-fill ${getBarColor(genPct)}" style="width:${genPct}%"></div></div></div>
    <div class="bed-bar"><div class="bed-bar-label"><span>${t('icu_beds')}</span><span style="color:var(--accent-${getBarColor(icuPct)})">${icuAvail} / ${h.icuBeds}</span></div><div class="bed-bar-track"><div class="bed-bar-fill ${getBarColor(icuPct)}" style="width:${icuPct}%"></div></div></div>
    <div class="bed-bar"><div class="bed-bar-label"><span>${t('ventilators')}</span><span style="color:var(--accent-${getBarColor(ventPct)})">${ventAvail} / ${h.ventilators}</span></div><div class="bed-bar-track"><div class="bed-bar-fill ${getBarColor(ventPct)}" style="width:${ventPct}%"></div></div></div>
  </div>`;

  // Budget (private only)
  if (h.budget) {
    html += `<div class="detail-section">
      <div class="detail-section-title"><i class="fas fa-wallet"></i> ${t('estimated_budget')}</div>
      <div class="budget-card">
        <div class="budget-row"><span class="budget-label">${t('consultation_fee')}</span><span class="budget-value">₹${h.budget.consultationFee.toLocaleString()}</span></div>
        <div class="budget-row"><span class="budget-label">${t('daily_room_charge')}</span><span class="budget-value">₹${h.budget.dailyCharge.toLocaleString()}</span></div>
        <div class="budget-row"><span class="budget-label">${t('category')}</span><span class="budget-value" style="text-transform:capitalize">${h.budget.category}</span></div>
        <div class="budget-range">${t('typical_treatment_range')}: <strong>₹${h.budget.minEstimate.toLocaleString()} — ₹${h.budget.maxEstimate.toLocaleString()}</strong></div>
      </div>
    </div>`;
  }

  // Doctors
  html += `<div class="detail-section">
    <div class="detail-section-title"><i class="fas fa-user-md"></i> ${t('doctors')} (${h.doctors.length})</div>
    ${h.doctors.map(d => {
      const isAvail = d.available && (hour >= 8 && hour <= 20);
      const initials = d.name.replace('Dr. ', '').split(' ').map(w => w[0]).join('').slice(0, 2);
      return `<div class="doctor-card">
        <div class="doc-avatar">${initials}</div>
        <div class="doc-info"><div class="doc-name">${d.name}</div><div class="doc-spec">${d.specialization}</div><div class="doc-exp">${d.experience} ${t('yrs_experience')}</div></div>
        <span class="doc-status ${isAvail ? 'available' : 'away'}">${isAvail ? t('available') : t('away')}</span>
      </div>`;
    }).join('')}
  </div>`;

  // Specializations
  html += `<div class="detail-section">
    <div class="detail-section-title"><i class="fas fa-stethoscope"></i> ${t('specializations')}</div>
    <div class="tag-list">${h.specializations.map(s => `<span class="tag">${s}</span>`).join('')}</div>
  </div>`;

  // Facilities
  html += `<div class="detail-section">
    <div class="detail-section-title"><i class="fas fa-hospital"></i> ${t('facilities')}</div>
    <div class="tag-list">${h.facilities.map(f => `<span class="tag">${f}</span>`).join('')}</div>
  </div>`;

  // Reviews
  const reviews = JSON.parse(localStorage.getItem(`reviews_${h.id}`) || '[]');
  if (reviews.length === 0) {
    // Seed demo reviews
    const seeds = [
      { name: 'Priya M.', rating: 4, text: 'Good facilities and caring staff. Wait time was reasonable.', timestamp: '2026-07-15' },
      { name: 'Rahul D.', rating: 5, text: 'Excellent doctors. The treatment was very effective.', timestamp: '2026-06-20' },
    ];
    seeds.forEach(s => reviews.push(s));
    localStorage.setItem(`reviews_${h.id}`, JSON.stringify(reviews));
  }

  html += `<div class="detail-section">
    <div class="detail-section-title"><i class="fas fa-star"></i> ${t('reviews')} (${reviews.length})</div>
    ${reviews.slice(-5).reverse().map(r => `
      <div class="review-card">
        <div class="review-header"><span class="review-name">${r.name}</span><span class="review-date">${r.timestamp}</span></div>
        <div class="review-stars">${'<i class="fas fa-star"></i>'.repeat(r.rating)}${'<i class="far fa-star"></i>'.repeat(5 - r.rating)}</div>
        <div class="review-text">${r.text}</div>
      </div>`).join('')}
    <div class="review-form">
      <div class="review-form-actions" style="margin-bottom:8px">
        <div class="star-input" id="star-input">${[1,2,3,4,5].map(n => `<i class="far fa-star" data-val="${n}" onmouseover="hoverStar(${n})" onmouseout="resetStars()" onclick="selectStar(${n})"></i>`).join('')}</div>
      </div>
      <textarea id="review-text" placeholder="${t('write_review')}"></textarea>
      <div class="review-form-actions"><span></span><button class="review-submit" onclick="submitReview(${h.id})">${t('submit_review')}</button></div>
    </div>
  </div>`;

  // Copyright
  html += `<div style="text-align:center;padding:16px 0;font-size:.6rem;color:var(--text-muted);border-top:1px solid var(--border-glass);margin-top:10px">Copyrights are claimed by MH Connect Team &bull; Developed by MH Connect Team</div>`;

  document.getElementById('detail-content').innerHTML = html;
}

function closeDetail() {
  document.getElementById('detail-overlay').classList.remove('show');
  document.getElementById('detail-panel').classList.remove('open');
  if (state.routeLayer) { state.map.removeLayer(state.routeLayer); state.routeLayer = null; }
}

// ====== ROUTING ======
async function showRoute(h) {
  if (state.routeLayer) state.map.removeLayer(state.routeLayer);

  const distKm = h._distance;
  const hour = new Date().getHours();
  const trafficLevel = (hour >= 8 && hour <= 10) || (hour >= 17 && hour <= 20) ? 'Heavy' : hour >= 11 && hour <= 16 ? 'Moderate' : 'Light';
  const trafficMul = trafficLevel === 'Heavy' ? 1.6 : trafficLevel === 'Moderate' ? 1.3 : 1.0;

  try {
    const url = `https://router.project-osrm.org/route/v1/driving/${state.userLng},${state.userLat};${h.lng},${h.lat}?overview=full&geometries=geojson`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.routes && data.routes.length) {
      const route = data.routes[0];
      const coords = route.geometry.coordinates.map(c => [c[1], c[0]]);
      state.routeLayer = L.polyline(coords, { color: '#38bdf8', weight: 4, opacity: 0.8, dashArray: '8, 4' }).addTo(state.map);
      state.map.fitBounds(state.routeLayer.getBounds(), { padding: [50, 50] });
      const km = (route.distance / 1000).toFixed(1);
      const mins = Math.ceil(route.duration / 60 * trafficMul);
      document.getElementById('route-distance').textContent = `${km} km`;
      document.getElementById('route-time').textContent = mins < 60 ? `${mins} min` : `${Math.floor(mins/60)}h ${mins%60}m`;
      document.getElementById('route-traffic').textContent = t(trafficLevel.toLowerCase());
      document.getElementById('route-traffic').style.color = trafficLevel === 'Heavy' ? '#f87171' : trafficLevel === 'Moderate' ? '#fbbf24' : '#34d399';
      return;
    }
  } catch(e) {}

  // Fallback
  state.routeLayer = L.polyline([[state.userLat, state.userLng], [h.lat, h.lng]], { color: '#818cf8', weight: 3, opacity: 0.6, dashArray: '6,6' }).addTo(state.map);
  state.map.fitBounds(state.routeLayer.getBounds(), { padding: [50, 50] });
  const estTime = Math.ceil(distKm / 40 * 60 * trafficMul);
  document.getElementById('route-distance').textContent = `~${distKm.toFixed(1)} km`;
  document.getElementById('route-time').textContent = estTime < 60 ? `~${estTime} min` : `~${Math.floor(estTime/60)}h ${estTime%60}m`;
  document.getElementById('route-traffic').textContent = trafficLevel;
}

// ====== REVIEWS ======
let selectedRating = 0;
function hoverStar(n) {
  document.querySelectorAll('#star-input i').forEach((el, i) => {
    el.className = i < n ? 'fas fa-star active' : 'far fa-star';
  });
}
function resetStars() {
  document.querySelectorAll('#star-input i').forEach((el, i) => {
    el.className = i < selectedRating ? 'fas fa-star active' : 'far fa-star';
  });
}
function selectStar(n) { selectedRating = n; hoverStar(n); }

function submitReview(hid) {
  const text = document.getElementById('review-text').value.trim();
  if (!text || selectedRating === 0) return;
  const reviews = JSON.parse(localStorage.getItem(`reviews_${hid}`) || '[]');
  reviews.push({ name: state.userName, rating: selectedRating, text, timestamp: new Date().toISOString().split('T')[0] });
  localStorage.setItem(`reviews_${hid}`, JSON.stringify(reviews));
  // Also post to server
  fetch('/api/reviews', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hospitalId: hid, rating: selectedRating, text, timestamp: new Date().toISOString().split('T')[0] })
  }).catch(() => {});
  selectedRating = 0;
  openDetail(state.hospitals.find(h => h.id === hid));
}

// ====== EMERGENCY ======
function openEmergency() {
  document.getElementById('emergency-modal').classList.add('show');
  renderEmergencyList();
}
function closeEmergency() {
  document.getElementById('emergency-modal').classList.remove('show');
}

function triageFilter(type) {
  document.querySelectorAll('.triage-btn').forEach(b => b.classList.remove('selected'));
  event.target.closest('.triage-btn').classList.add('selected');

  const specMap = {
    'cardiac': ['Cardiology', 'Cardiologist'],
    'trauma': ['Orthopedics', 'Orthopedic Surgeon', 'General Surgery', 'General Surgeon'],
    'breathing': ['Pulmonology', 'Pulmonologist'],
    'stroke': ['Neurology', 'Neurologist', 'Neurosurgery', 'Neurosurgeon'],
    'pediatric': ['Pediatrics', 'Pediatrician', 'Pediatric Surgery', 'Pediatric Surgeon'],
    'obstetric': ['Obstetrics & Gynecology', 'Gynecologist'],
    'burn': ['Burn Unit', 'General Surgery', 'Plastic Surgery'],
    'general': []
  };
  renderEmergencyList(specMap[type] || []);
}

function renderEmergencyList(requiredSpecs) {
  let list = state.hospitals.filter(h => h.hasEmergency).sort((a, b) => a._distance - b._distance);

  if (requiredSpecs && requiredSpecs.length > 0) {
    const specList = list.filter(h =>
      h.specializations.some(s => requiredSpecs.some(rs => s.toLowerCase().includes(rs.toLowerCase()))) ||
      h.doctors.some(d => requiredSpecs.some(rs => d.specialization.toLowerCase().includes(rs.toLowerCase()))) ||
      h.facilities.some(f => requiredSpecs.some(rs => f.toLowerCase().includes(rs.toLowerCase())))
    );
    if (specList.length > 0) list = specList;
  }

  const top = list.slice(0, 8);
  document.getElementById('emg-hospital-list').innerHTML = top.map((h, i) => {
    const dist = h._distance < 1 ? `${(h._distance*1000).toFixed(0)}m` : `${h._distance.toFixed(1)} km`;
    const eta = Math.ceil(h._distance / 40 * 60);
    return `<div class="emg-hospital-item" onclick="closeEmergency();openDetail(state.hospitals.find(x=>x.id===${h.id}))">
      <div class="emg-rank">${i + 1}</div>
      <div class="emg-h-info">
        <div class="emg-h-name">${h.area === 'rural' ? ' ' : ''}${h.name}</div>
        <div class="emg-h-detail">
          <span>${h.city}</span>
          <span>ICU: ${h.icuBeds}</span>
          <span>ETA: ~${eta} min</span>
        </div>
      </div>
      <div class="emg-h-dist">${dist}</div>
    </div>`;
  }).join('');
}

// ====== USER MENU ======
function toggleUserMenu() {
  document.getElementById('user-dropdown').classList.toggle('show');
}

// ====== EVENT BINDINGS ======
function bindEvents() {
  // Filters
  document.querySelectorAll('.filter-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentFilter = btn.dataset.filter;
      applyFiltersAndSort();
    });
  });

  // Sort
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentSort = btn.dataset.sort;
      applyFiltersAndSort();
    });
  });

  // Search
  document.getElementById('search-input').addEventListener('input', e => {
    state.searchQuery = e.target.value;
    applyFiltersAndSort();
  });

  // Specialty filter
  document.getElementById('filter-specialty').addEventListener('change', e => {
    state.currentSpecialty = e.target.value;
    applyFiltersAndSort();
  });

  // Budget filter
  document.getElementById('filter-budget').addEventListener('change', e => {
    state.currentBudget = e.target.value;
    applyFiltersAndSort();
  });

  // Detail panel close
  document.getElementById('detail-back').addEventListener('click', closeDetail);
  document.getElementById('detail-overlay').addEventListener('click', closeDetail);

  // Recenter
  document.getElementById('btn-recenter').addEventListener('click', () => {
    state.map.setView([state.userLat, state.userLng], 11);
  });

  // Close user menu on outside click
  document.addEventListener('click', e => {
    if (!e.target.closest('.user-menu')) {
      document.getElementById('user-dropdown').classList.remove('show');
    }
  });
}

// ====== LANGUAGE CHANGE HANDLER ======
document.addEventListener('languageChanged', () => {
  // Re-render all dynamic content with new language
  applyFiltersAndSort();
  updateStats();
  // Update role display
  const roleEl = document.getElementById('ud-role');
  const ddRoleEl = document.getElementById('dd-role');
  if (ddRoleEl && window.mhcSessionData) {
    ddRoleEl.textContent = window.mhcSessionData.role ? window.mhcSessionData.role.toUpperCase() : 'USER';
  }
  if (roleEl) {
    roleEl.textContent = roleEl.textContent.includes('Admin') || roleEl.textContent.includes('प्रशासक') ? t('administrator') : t('user');
  }
});

// ====== START ======
document.addEventListener('DOMContentLoaded', init);



// ====== PATIENT PREDICTION LOGIC ======
async function runPatientPrediction() {
    const selectedSymptoms = Array.from(document.querySelectorAll('#symptomChips .chip.selected')).map(c => c.dataset.val);
    if(selectedSymptoms.length === 0) {
        alert("Please select at least one symptom.");
        return;
    }
    
    document.getElementById('predictionResults').innerHTML = '<div class="text-center p-4"><div class="spinner"></div><p>Analyzing symptoms...</p></div>';
    document.getElementById('predictionResults').classList.remove('hidden');
    
    try {
        const payload = { 
            patient_name: "Patient", 
            age: 30, 
            village: "Local", 
            vitals: {}, 
            danger_signs: [], 
            symptoms: selectedSymptoms 
        };
        const res = await fetch('/api/predict', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        
        let html = '<h4 class="font-bold text-md mb-2">Predictions</h4>';
        if(data.prediction && data.prediction.length > 0) {
            let emergencyTriggered = false;
            
            data.prediction.forEach(p => {
                const isEmergency = p.disease.toLowerCase().includes('emergency');
                if(isEmergency && p.confidence > 25) emergencyTriggered = true;
                
                html += `
                <div class="border rounded p-3 mb-2 bg-white">
                    <div class="flex justify-between items-center mb-1">
                        <span class="font-bold text-sm ${isEmergency ? 'text-red-600' : 'text-slate-800'}">${p.disease}</span>
                        <span class="text-xs bg-slate-100 px-2 py-1 rounded">${p.confidence}%</span>
                    </div>
                </div>`;
            });
            
            // Bed Availability
            html += `<h4 class="font-bold text-md mt-4 mb-2">Estimated Bed Availability (Live)</h4>`;
            html += `
            <div class="grid grid-cols-3 gap-2 text-center text-xs">
                <div class="bg-green-50 border border-green-200 rounded p-2">
                    <div class="font-bold text-green-700 text-lg">${data.bed_availability.general}%</div>
                    <div class="text-slate-500">General</div>
                </div>
                <div class="bg-orange-50 border border-orange-200 rounded p-2">
                    <div class="font-bold text-orange-700 text-lg">${data.bed_availability.icu}%</div>
                    <div class="text-slate-500">ICU</div>
                </div>
                <div class="bg-red-50 border border-red-200 rounded p-2">
                    <div class="font-bold text-red-700 text-lg">${data.bed_availability.ventilator}%</div>
                    <div class="text-slate-500">Ventilator</div>
                </div>
            </div>`;
            
            html += `<button onclick="document.getElementById('predictor-section').style.display='none'; document.getElementById('hospitals-section').style.display='block';" class="mt-4 w-full bg-blue-600 text-white rounded p-2 text-sm font-bold">Find Hospitals</button>`;
            
            document.getElementById('predictionResults').innerHTML = html;
            
            if(emergencyTriggered) {
                alert("EMERGENCY DETECTED! Routing to nearest hospital with Emergency Room.");
                openEmergency();
            }
        } else {
            document.getElementById('predictionResults').innerHTML = '<p class="text-sm text-slate-500">No matching diseases found.</p>';
        }
    } catch (e) {
        document.getElementById('predictionResults').innerHTML = '<p class="text-sm text-red-500">Error connecting to AI service.</p>';
    }
}

function initSymptomChips() {
    const chipsContainer = document.getElementById('symptomChips');
    if(!chipsContainer) return;
    const symptoms = [
        "itching", "skin_rash", "nodal_skin_eruptions", "continuous_sneezing", "shivering", "chills", "joint_pain", 
        "stomach_pain", "acidity", "ulcers_on_tongue", "muscle_wasting", "vomiting", "burning_micturition", "spotting_ urination", 
        "fatigue", "weight_gain", "anxiety", "cold_hands_and_feets", "mood_swings", "weight_loss", "restlessness", "lethargy", 
        "patches_in_throat", "irregular_sugar_level", "cough", "high_fever", "sunken_eyes", "breathlessness", "sweating", 
        "dehydration", "indigestion", "headache", "yellowish_skin", "dark_urine", "nausea", "loss_of_appetite", "pain_behind_the_eyes", 
        "back_pain", "constipation", "abdominal_pain", "diarrhoea", "mild_fever", "yellow_urine", "yellowing_of_eyes", "acute_liver_failure", 
        "fluid_overload", "swelling_of_stomach", "swelled_lymph_nodes", "malaise", "blurred_and_distorted_vision", "phlegm", 
        "throat_irritation", "redness_of_eyes", "sinus_pressure", "runny_nose", "congestion", "chest_pain", "weakness_in_limbs", 
        "fast_heart_rate", "pain_during_bowel_movements", "pain_in_anal_region", "bloody_stool", "irritation_in_anus", "neck_pain", 
        "dizziness", "cramps", "bruising", "obesity", "swollen_legs", "swollen_blood_vessels", "puffy_face_and_eyes", "enlarged_thyroid", 
        "brittle_nails", "swollen_extremeties", "excessive_hunger", "extra_marital_contacts", "drying_and_tingling_lips", "slurred_speech", 
        "knee_pain", "hip_joint_pain", "muscle_weakness", "stiff_neck", "swelling_joints", "movement_stiffness", "spinning_movements", 
        "loss_of_balance", "unsteadiness", "weakness_of_one_body_side", "loss_of_smell", "bladder_discomfort", "foul_smell_of urine", 
        "continuous_feel_of_urine", "passage_of_gases", "internal_itching", "toxic_look_(typhos)", "depression", "irritability", 
        "muscle_pain", "altered_sensorium", "red_spots_over_body", "belly_pain", "abnormal_menstruation", "dischromic _patches", 
        "watering_from_eyes", "increased_appetite", "polyuria", "family_history", "mucoid_sputum", "rusty_sputum", "lack_of_concentration", 
        "visual_disturbances", "receiving_blood_transfusion", "receiving_unsterile_injections", "coma", "stomach_bleeding", 
        "distention_of_abdomen", "history_of_alcohol_consumption", "fluid_overload", "blood_in_sputum", "prominent_veins_on_calf", 
        "palpitations", "painful_walking", "pus_filled_pimples", "blackheads", "scurring", "skin_peeling", "silver_like_dusting", 
        "small_dents_in_nails", "inflammatory_nails", "blister", "red_sore_around_nose", "yellow_crust_ooze"
    ];
    
    // Convert to readable
    const formatName = (s) => s.replace(/_/g, ' ').replace(/\w/g, c => c.toUpperCase());
    
    symptoms.forEach(s => {
        const div = document.createElement('div');
        div.className = 'chip cursor-pointer bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-xs hover:bg-slate-300';
        div.dataset.val = s;
        div.innerText = formatName(s);
        div.onclick = function() {
            this.classList.toggle('selected');
            if(this.classList.contains('selected')) {
                this.classList.replace('bg-slate-200', 'bg-blue-600');
                this.classList.replace('text-slate-700', 'text-white');
            } else {
                this.classList.replace('bg-blue-600', 'bg-slate-200');
                this.classList.replace('text-white', 'text-slate-700');
            }
        };
        chipsContainer.appendChild(div);
    });
}
window.addEventListener('DOMContentLoaded', initSymptomChips);
