/**
 * navigation.js – Smart Navigation with Leaflet.js and OpenStreetMap
 * Interactive map with all Tirumala facilities, search, and crowd-aware routing.
 */
'use strict';

let map = null;
let markers = [];
let userLocation = null;
let allLocations = [];

// Category icons for markers
const categoryIcons = {
  temple: '🛕',
  queue: '⏳',
  food: '🍛',
  laddu: '🍬',
  phone_deposit: '📵',
  restroom: '🚻',
  water: '💧',
  medical: '🏥',
  transport: '🚌',
  parking: '🅿️',
  accommodation: '🏨',
  footpath: '🚶',
  tonsure: '✂️',
  police: '👮',
  information: 'ℹ️',
  lost_found: '🔍',
  cloak_room: '🧳'
};

// Initialize navigation page
function initNavigation() {
  // Get current location button
  document.getElementById('getCurrentLocation')?.addEventListener('click', getCurrentLocation);
  
  // Search button
  document.getElementById('searchBtn')?.addEventListener('click', handleSearch);
  
  // Search on Enter key
  document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
  });
  
  // Category filter
  document.getElementById('categoryFilter')?.addEventListener('change', handleFilter);
  
  // Nearest button
  document.getElementById('nearestBtn')?.addEventListener('click', showNearest);
  
  // Re-center button
  document.getElementById('recenterBtn')?.addEventListener('click', recenterMap);
  
  // Initialize map
  initializeMap();
  
  // Load locations
  loadLocations();
}

// Initialize Leaflet map
function initializeMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer || typeof L === 'undefined') return;

  // Center on Tirumala temple
  const centerLat = 13.6839;
  const centerLng = 79.3476;

  map = L.map('map').setView([centerLat, centerLng], 14);

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);
}

// Load locations from API
async function loadLocations() {
  try {
    const response = await fetch('/api/locations');
    const data = await response.json();
    
    allLocations = data.locations || [];
    displayLocations(allLocations);
  } catch (error) {
    console.error('Failed to load locations:', error);
  }
}

// Display locations on map
function displayLocations(locations) {
  if (!map) return;
  
  // Clear existing markers
  markers.forEach(marker => map.removeLayer(marker));
  markers = [];
  
  // Add new markers
  locations.forEach(loc => {
    const icon = categoryIcons[loc.category] || '📍';
    
    const marker = L.marker([loc.latitude, loc.longitude], {
      icon: L.divIcon({
        className: 'custom-marker',
        html: `<div style="font-size: 24px;">${icon}</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      })
    }).addTo(map);
    
    // Add popup
    marker.bindPopup(`
      <div class="marker-popup">
        <strong>${loc.name}</strong><br>
        ${loc.description || ''}<br>
        <button onclick="navigate('navigation')" style="margin-top: 5px;">Navigate</button>
      </div>
    `);
    
    markers.push(marker);
  });
}

// Re-center map
function recenterMap() {
  if (!map) return;
  map.setView([13.6839, 79.3476], 14);
}

// Handle search
function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const searchTerm = searchInput?.value.trim();
  
  if (!searchTerm) {
    displayLocations(allLocations);
    return;
  }
  
  const filtered = allLocations.filter(loc => 
    loc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    loc.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    loc.category.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  displayLocations(filtered);
}

// Handle category filter
function handleFilter() {
  const categoryFilter = document.getElementById('categoryFilter');
  const category = categoryFilter?.value;
  
  if (!category) {
    displayLocations(allLocations);
    return;
  }
  
  const filtered = allLocations.filter(loc => loc.category === category);
  displayLocations(filtered);
}

// Show nearest locations
async function showNearest() {
  if (!userLocation) {
    getCurrentLocation();
    return;
  }
  
  try {
    const response = await fetch(`/api/locations/nearest?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}&limit=5`);
    const data = await response.json();
    
    if (data.nearest && data.nearest.length > 0) {
      displayLocations(data.nearest.map(n => ({
        ...n,
        category: n.category
      })));
      
      showToast(`Found ${data.nearest.length} nearest locations`, 'success');
    }
  } catch (error) {
    console.error('Failed to get nearest locations:', error);
  }
}

// Get current location
function getCurrentLocation() {
  if (!navigator.geolocation) {
    showToast('Geolocation not supported', 'error');
    return;
  }
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      userLocation = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude
      };
      
      const locationDisplay = document.getElementById('currentLocation');
      if (locationDisplay) {
        locationDisplay.innerHTML = `
          <div>Lat: ${userLocation.latitude.toFixed(6)}</div>
          <div>Lng: ${userLocation.longitude.toFixed(6)}</div>
        `;
      }
      
      showToast('Location found!', 'success');
      
      // Center map on user location
      if (map) {
        map.setView([userLocation.latitude, userLocation.longitude], 15);
      }
    },
    (error) => {
      showToast('Failed to get location', 'error');
    }
  );
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.navigation-page')) {
    initNavigation();
  }
});
