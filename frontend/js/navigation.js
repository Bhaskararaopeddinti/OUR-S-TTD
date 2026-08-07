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
function initNavigationPage() {
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
  initMap();
  
  // Load all locations
  loadAllLocations();
}

// Initialize Leaflet map
function initMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer || typeof L === 'undefined') return;

  // Center on Tirumala temple
  const centerLat = 13.6839;
  const centerLng = 79.3476;

  map = L.map('map').setView([centerLat, centerLng], 14);

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  }).addTo(map);

  // Add zoom control
  L.control.zoom({ position: 'topright' }).addTo(map);
}

// Load all navigation locations from API
async function loadAllLocations() {
  try {
    const response = await fetch('/api/locations');
    const data = await response.json();
    allLocations = data.locations || [];
    
    // Display all markers
    displayMarkers(allLocations);
    
    // Update facility list
    displayFacilityList(allLocations);
    
  } catch (error) {
    console.error('Failed to load locations:', error);
    document.getElementById('facilityList').innerHTML = '<p class="error">Failed to load facilities</p>';
  }
}

// Display markers on map
function displayMarkers(locations) {
  // Clear existing markers
  markers.forEach(marker => map.removeLayer(marker));
  markers = [];

  locations.forEach(loc => {
    const icon = categoryIcons[loc.category] || '📍';
    
    // Create custom icon with emoji
    const customIcon = L.divIcon({
      html: `<div style="font-size: 24px; text-shadow: 0 0 2px white;">${icon}</div>`,
      className: 'custom-marker',
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = L.marker([loc.latitude, loc.longitude], { icon: customIcon })
      .addTo(map)
      .bindPopup(`
        <div style="min-width: 200px;">
          <h3>${icon} ${loc.name}</h3>
          <p><strong>Category:</strong> ${loc.category}</p>
          <p><strong>Address:</strong> ${loc.address || 'N/A'}</p>
          <p><strong>Hours:</strong> ${loc.opening_hours || '24/7'}</p>
          ${loc.wheelchair_accessible ? '<p>♿ Wheelchair accessible</p>' : ''}
          <button onclick="selectFacility(${loc.id})" style="margin-top: 8px; padding: 4px 8px;">View Details</button>
        </div>
      `);

    markers.push(marker);
  });

  // Fit bounds to show all markers
  if (markers.length > 0) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
}

// Display facility list
function displayFacilityList(locations) {
  const listContainer = document.getElementById('facilityList');
  
  if (locations.length === 0) {
    listContainer.innerHTML = '<p class="hint">No facilities found</p>';
    return;
  }

  listContainer.innerHTML = locations.map(loc => {
    const icon = categoryIcons[loc.category] || '📍';
    return `
      <div class="facility-list-item" onclick="selectFacility(${loc.id})">
        <span class="facility-icon">${icon}</span>
        <div class="facility-info">
          <strong>${loc.name}</strong>
          <small>${loc.category}</small>
        </div>
      </div>
    `;
  }).join('');
}

// Handle search
async function handleSearch() {
  const searchTerm = document.getElementById('searchInput').value.trim();
  const categoryFilter = document.getElementById('categoryFilter').value;
  
  if (!searchTerm && !categoryFilter) {
    displayMarkers(allLocations);
    displayFacilityList(allLocations);
    return;
  }

  try {
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (categoryFilter) params.append('category', categoryFilter);
    
    const response = await fetch(`/api/locations?${params.toString()}`);
    const data = await response.json();
    
    displayMarkers(data.locations || []);
    displayFacilityList(data.locations || []);
    
  } catch (error) {
    console.error('Search failed:', error);
  }
}

// Handle category filter
function handleFilter() {
  handleSearch();
}

// Show nearest facilities
async function showNearest() {
  if (!userLocation) {
    alert('Please get your location first');
    return;
  }

  const categoryFilter = document.getElementById('categoryFilter').value;
  
  try {
    const params = new URLSearchParams();
    params.append('latitude', userLocation.latitude);
    params.append('longitude', userLocation.longitude);
    params.append('limit', '10');
    if (categoryFilter) params.append('category', categoryFilter);
    
    const response = await fetch(`/api/locations/nearest?${params.toString()}`);
    const data = await response.json();
    
    displayMarkers(data.nearest || []);
    displayFacilityList(data.nearest || []);
    
    // Center map on user location
    if (map && userLocation) {
      map.setView([userLocation.latitude, userLocation.longitude], 15);
      
      // Add user location marker
      const userMarker = L.marker([userLocation.latitude, userLocation.longitude], {
        icon: L.divIcon({
          html: '<div style="font-size: 30px;">📍</div>',
          className: 'user-marker',
          iconSize: [35, 35],
          iconAnchor: [17, 17]
        })
      }).addTo(map).bindPopup('📍 You are here');
      markers.push(userMarker);
    }
    
  } catch (error) {
    console.error('Failed to get nearest locations:', error);
  }
}

// Get user's current location
function getCurrentLocation() {
  const status = document.getElementById('locationStatus');
  const display = document.getElementById('currentLocation');
  
  if (!navigator.geolocation) {
    status.textContent = 'Geolocation not supported by your browser';
    status.className = 'status error';
    return;
  }
  
  status.textContent = 'Getting your location...';
  status.className = 'status';
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      userLocation = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude
      };
      
      display.innerHTML = `
        <p><strong>Latitude:</strong> ${userLocation.latitude.toFixed(6)}</p>
        <p><strong>Longitude:</strong> ${userLocation.longitude.toFixed(6)}</p>
      `;
      status.textContent = 'Location found!';
      status.className = 'status success';
      
      // Center map on user location
      if (map) {
        map.setView([userLocation.latitude, userLocation.longitude], 15);
      }
    },
    (error) => {
      status.textContent = 'Could not get your location. Please enable location services.';
      status.className = 'status error';
    }
  );
}

// Select a facility and show details
async function selectFacility(locationId) {
  try {
    const response = await fetch(`/api/locations/${locationId}`);
    const loc = await response.json();
    
    const detailsDiv = document.getElementById('facilityDetails');
    const icon = categoryIcons[loc.category] || '📍';
    
    detailsDiv.innerHTML = `
      <div class="facility-detail-card">
        <h4>${icon} ${loc.name}</h4>
        <p><strong>Category:</strong> ${loc.category}</p>
        <p><strong>Address:</strong> ${loc.address || 'N/A'}</p>
        <p><strong>Description:</strong> ${loc.description || 'N/A'}</p>
        <p><strong>Opening Hours:</strong> ${loc.opening_hours || '24/7'}</p>
        <p><strong>Contact:</strong> ${loc.contact_number || 'N/A'}</p>
        ${loc.wheelchair_accessible ? '<p>♿ <strong>Wheelchair Accessible</strong></p>' : ''}
        <p><small><strong>Source:</strong> ${loc.source}</small></p>
        <p><small><strong>Last Verified:</strong> ${loc.last_verified || 'N/A'}</small></p>
        
        <div class="facility-actions">
          <button class="primary" onclick="navigateToLocation(${loc.latitude}, ${loc.longitude}, '${loc.name.replace(/'/g, "\\'")}')">
            🗺️ Navigate (Google Maps)
          </button>
          ${userLocation ? `
            <button class="secondary" onclick="calculateDistance(${loc.latitude}, ${loc.longitude})">
              📏 Calculate Distance
            </button>
          ` : ''}
        </div>
      </div>
    `;
    
    // Center map on selected facility
    if (map) {
      map.setView([loc.latitude, loc.longitude], 16);
    }
    
  } catch (error) {
    console.error('Failed to get facility details:', error);
  }
}

// Navigate to location using Google Maps
function navigateToLocation(lat, lng, name) {
  const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  window.open(url, '_blank', 'noopener');
}

// Calculate distance from user location
function calculateDistance(lat, lng) {
  if (!userLocation) {
    alert('Please get your location first');
    return;
  }
  
  const R = 6371000; // Earth's radius in meters
  const lat1 = userLocation.latitude * Math.PI / 180;
  const lat2 = lat * Math.PI / 180;
  const dLat = (lat - userLocation.latitude) * Math.PI / 180;
  const dLng = (lng - userLocation.longitude) * Math.PI / 180;
  
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1) * Math.cos(lat2) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distance = R * c;
  
  const distanceKm = (distance / 1000).toFixed(2);
  const walkingTime = Math.round(distance / 80); // Average walking speed ~80m/min
  
  alert(`Distance: ${distanceKm} km\nEstimated walking time: ~${walkingTime} minutes`);
}

// Re-center map to Tirumala temple
function recenterMap() {
  if (map) {
    map.setView([13.6839, 79.3476], 14);
  }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.navigation-page')) {
    initNavigationPage();
  }
});
