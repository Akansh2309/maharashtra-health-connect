// STATE.JS
// This file holds the global variables and application state.
// We keep it separate so any file can access or modify the current state.

const State = {
    // Array holding all hospital data loaded from JSON
    hospitals: [],
    
    // Array holding hospitals after filtering is applied
    filteredHospitals: [],
    
    // The user's current GPS location [latitude, longitude]
    userLocation: null,
    
    // Current active filter (all, government, private, rural, emergency)
    currentFilter: 'all',
    
    // Reference to the Leaflet map object
    map: null,
    
    // Group of Leaflet markers
    markerGroup: null
};
