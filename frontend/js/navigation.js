/**
 * navigation.js – Smart Navigation with Leaflet.js and OpenStreetMap
 * Interactive map with all Tirumala facilities, search, and crowd-aware routing.
 */
'use strict';

let map = null;
let markers = [];
let userLocation = null;
let allLocations = [];
let routeControl = null;

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
  
  // Clear existing markers and route
  markers.forEach(marker => map.removeLayer(marker));
  markers = [];
  clearRoute();
  
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
    
    marker.bindPopup(`
      <div class="marker-popup">
        <strong>${loc.name}</strong><br>
        ${loc.description || ''}<br>
        <button onclick="routeToLocation(${loc.latitude}, ${loc.longitude}, '${loc.name.replace(/'/g, "\\'")}')" style="margin-top: 5px;">Route Here</button>
      </div>
    `);
    
    marker.on('click', () => showLocationDetails(loc));
    markers.push(marker);
  });
  
  populateFacilityList(locations);
}

function populateFacilityList(locations) {
  const list = document.getElementById('facilityList');
  const details = document.getElementById('facilityDetails');
  if (!list) return;

  if (!locations.length) {
    list.innerHTML = '<p class="hint">No facilities found for that search.</p>';
    if (details) details.innerHTML = '<p class="hint">Select a facility marker to see details.</p>';
    return;
  }

  list.innerHTML = locations.map(loc => `
    <div class="facility-item" tabindex="0" role="button" onclick="focusOnLocation(${loc.latitude}, ${loc.longitude}, '${loc.name.replace(/'/g, "\\'")}')">
      <strong>${loc.name}</strong>
      <p>${loc.category.replace('_', ' ')}</p>
      <button class="quick-action-btn small" onclick="event.stopPropagation(); routeToLocation(${loc.latitude}, ${loc.longitude}, '${loc.name.replace(/'/g, "\\'")}')">Route</button>
    </div>
  `).join('');

  if (details && locations.length) {
    showLocationDetails(locations[0]);
  }
}

function showLocationDetails(loc) {
  const details = document.getElementById('facilityDetails');
  if (!details) return;
  details.innerHTML = `
    <h4>${loc.name}</h4>
    <p>${loc.description || 'No description available.'}</p>
    <p><strong>Category:</strong> ${loc.category}</p>
    <p><strong>Address:</strong> ${loc.address || 'Not available'}</p>
    <button class="quick-action-btn" onclick="routeToLocation(${loc.latitude}, ${loc.longitude}, '${loc.name.replace(/'/g, "\\'")}')">Show travel route</button>
  `;
}

function focusOnLocation(lat, lng, name) {
  if (!map) return;
  map.setView([lat, lng], 16);
  showToast(`Focused on ${name}`, 'info');
}

function clearRoute() {
  if (routeControl) {
    map.removeControl(routeControl);
    routeControl = null;
  }
}

function routeToLocation(lat, lng, name) {
  if (!userLocation) {
    showToast('Please share your current location first.', 'info');
    return;
  }

  if (typeof L === 'undefined' || typeof L.Routing === 'undefined') {
    showToast('Routing plugin not loaded.', 'error');
    return;
  }

  clearRoute();
  routeControl = L.Routing.control({
    waypoints: [
      L.latLng(userLocation.latitude, userLocation.longitude),
      L.latLng(lat, lng)
    ],
    routeWhileDragging: false,
    show: false,
    addWaypoints: false,
    draggableWaypoints: false,
    lineOptions: {
      styles: [{ color: '#ff8c00', opacity: 0.9, weight: 6 }]
    },
    router: L.Routing.osrmv1({
      serviceUrl: 'https://router.project-osrm.org/route/v1/'
    })
  }).addTo(map);
  showToast(`Routing to ${name}`, 'success');
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
