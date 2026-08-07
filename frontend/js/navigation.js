/**
 * navigation.js – Real Walk Navigation with Leaflet.js and OSRM.
 * Enhanced Live Navigation experience with route summary, ETA, and directions.
 */
'use strict';

let map = null;
let markers = [];
let userLocation = null;
let allLocations = [];
let selectedLocation = null;
let routeLayer = null;
let userMarker = null;
let destinationMarker = null;

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

const categoryNames = {
  temple: 'Temple',
  queue: 'Queue Complex',
  food: 'Food & Annaprasadam',
  laddu: 'Laddu Counter',
  phone_deposit: 'Phone Deposit',
  restroom: 'Restroom',
  water: 'Drinking Water',
  medical: 'Medical Centre',
  transport: 'Transport',
  parking: 'Parking',
  accommodation: 'Accommodation',
  footpath: 'Footpath',
  tonsure: 'Tonsure',
  police: 'Police',
  information: 'Information',
  lost_found: 'Lost & Found',
  cloak_room: 'Cloak Room'
};

function initNavigation() {
  document.getElementById('getCurrentLocation')?.addEventListener('click', getCurrentLocation);
  document.getElementById('searchBtn')?.addEventListener('click', handleSearch);
  document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
  });
  document.getElementById('categoryFilter')?.addEventListener('change', handleFilter);
  document.getElementById('nearestBtn')?.addEventListener('click', showNearest);
  document.getElementById('recenterBtn')?.addEventListener('click', recenterMap);

  initializeMap();
  loadLocations();
}

function initializeMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer || typeof L === 'undefined') return;

  const centerLat = 13.6839;
  const centerLng = 79.3476;
  map = L.map('map', { zoomControl: false }).setView([centerLat, centerLng], 14);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);

  L.control.zoom({ position: 'topright' }).addTo(map);
  L.control.scale({ position: 'bottomleft' }).addTo(map);
}

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

function displayLocations(locations) {
  if (!map) return;

  markers.forEach(marker => map.removeLayer(marker));
  markers = [];
  clearRoute();

  const list = document.getElementById('facilityList');
  const count = document.getElementById('facilityCount');

  if (!locations.length) {
    if (list) list.innerHTML = '<p class="hint">No facilities match your search.</p>';
    if (count) count.textContent = '0 results';
    return;
  }

  if (count) count.textContent = `${locations.length} results`;
  if (list) list.innerHTML = locations.map(loc => renderFacilityCard(loc)).join('');

  locations.forEach(loc => {
    const marker = L.marker([loc.latitude, loc.longitude], {
      icon: L.divIcon({
        className: 'custom-marker',
        html: `<div class="marker-badge">${categoryIcons[loc.category] || '📍'}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32]
      })
    }).addTo(map);

    marker.bindPopup(`<strong>${loc.name}</strong><br>${categoryNames[loc.category] || loc.category}<br><button class="popup-button" onclick="routeToLocation(${loc.id})">Navigate</button>`);
    marker.on('click', () => selectLocation(loc));
    markers.push(marker);
  });
}

function renderFacilityCard(loc) {
  return `
    <article class="facility-card" onclick="selectLocationById(${loc.id})">
      <div class="facility-card-header">
        <div class="facility-icon">${categoryIcons[loc.category] || '📍'}</div>
        <div>
          <h4>${loc.name}</h4>
          <small>${categoryNames[loc.category] || loc.category}</small>
        </div>
      </div>
      <div class="facility-card-meta">
        <div><strong>Distance</strong><span>${loc.distance_text || '—'}</span></div>
        <div><strong>Walk</strong><span>${loc.walking_time || '—'}</span></div>
      </div>
      <div class="facility-card-badges">
        <span class="badge crowd">Crowd: ${loc.crowd_level || 'Moderate'}</span>
        <span class="badge status">${loc.status || 'Open'}</span>
      </div>
      <div class="facility-card-actions">
        <button class="quick-action-btn" onclick="event.stopPropagation(); routeToLocation(${loc.id})">Navigate</button>
        <button class="secondary-action" onclick="event.stopPropagation(); selectLocationById(${loc.id})">View Details</button>
      </div>
    </article>
  `;
}

function selectLocationById(id) {
  const location = allLocations.find(loc => loc.id === id);
  if (!location) return;
  selectLocation(location);
}

function selectLocation(loc) {
  selectedLocation = loc;
  const summary = document.getElementById('routeSummary');
  if (summary) {
    summary.innerHTML = `
      <div class="route-panel">
        <h4>${loc.name}</h4>
        <p>${categoryNames[loc.category] || loc.category}</p>
        <p>${loc.address || 'No address available'}</p>
        <div class="route-stat-row"><span>Distance</span><strong>${loc.distance_text || '—'}</strong></div>
        <div class="route-stat-row"><span>Walking Time</span><strong>${loc.walking_time || '—'}</strong></div>
        <div class="route-stat-row"><span>Crowd</span><strong>${loc.crowd_level || 'Moderate'}</strong></div>
        <button class="quick-action-btn" onclick="routeToLocation(${loc.id})">Navigate</button>
      </div>
    `;
  }

  if (map) {
    map.setView([loc.latitude, loc.longitude], 16);
  }
}

function clearRoute() {
  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
  }
  if (destinationMarker) {
    map.removeLayer(destinationMarker);
    destinationMarker = null;
  }
}

async function routeToLocation(locationId) {
  if (!userLocation) {
    showToast('Locate yourself first before navigating.', 'info');
    return;
  }

  const destination = allLocations.find(loc => loc.id === locationId);
  if (!destination) {
    showToast('Destination not found.', 'error');
    return;
  }

  try {
    const response = await fetch(`/api/navigation/route?origin_lat=${userLocation.latitude}&origin_lng=${userLocation.longitude}&destination_id=${destination.id}`);
    const data = await response.json();
    if (response.ok) {
      renderNavigationRoute(data);
      selectLocation(destination);
      showToast(`Navigating to ${destination.name}`, 'success');
    } else {
      showToast(data.detail || 'Unable to calculate route.', 'error');
    }
  } catch (error) {
    console.error('Route error:', error);
    showToast('Unable to calculate route. Try again later.', 'error');
  }
}

function renderNavigationRoute(data) {
  if (!map) return;

  clearRoute();

  if (userMarker) {
    map.removeLayer(userMarker);
    userMarker = null;
  }
  userMarker = L.circleMarker([data.origin.latitude, data.origin.longitude], {
    radius: 7,
    fillColor: '#1d6df4',
    color: '#ffffff',
    weight: 2,
    fillOpacity: 0.9
  }).addTo(map).bindPopup('Start');

  destinationMarker = L.marker([data.destination.latitude, data.destination.longitude], {
    icon: L.divIcon({
      className: 'destination-marker',
      html: '<div class="dest-icon">🏁</div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })
  }).addTo(map).bindPopup(data.destination.name);

  routeLayer = L.geoJSON(data.geometry, {
    style: {
      color: '#0d6efd',
      weight: 6,
      opacity: 0.85
    }
  }).addTo(map);

  const bounds = routeLayer.getBounds();
  map.fitBounds(bounds.pad(0.25));

  const summary = document.getElementById('routeSummary');
  if (summary) {
    summary.innerHTML = `
      <div class="route-panel">
        <h4>Route to ${data.destination.name}</h4>
        <div class="route-stat-row"><span>Distance</span><strong>${data.distance_text}</strong></div>
        <div class="route-stat-row"><span>Walking Time</span><strong>${data.duration_text}</strong></div>
        <div class="route-stat-row"><span>ETA</span><strong>${new Date(data.eta).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong></div>
        <div class="route-stat-row"><span>Route Type</span><strong>${data.route_type}</strong></div>
      </div>
    `;
  }

  const steps = document.getElementById('directionSteps');
  if (steps) {
    steps.innerHTML = data.instructions.length
      ? data.instructions.map(step => `
          <div class="direction-step">
            <p>${step.instruction}</p>
            <small>${step.distance_text} • ${step.duration_text}</small>
          </div>
        `).join('')
      : '<p class="hint">No turn-by-turn instructions available.</p>';
  }
}

function recenterMap() {
  if (!map) return;
  map.setView([13.6839, 79.3476], 14);
}

function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const searchTerm = searchInput?.value.trim().toLowerCase();
  if (!searchTerm) {
    displayLocations(allLocations);
    return;
  }

  const filtered = allLocations.filter(loc =>
    loc.name.toLowerCase().includes(searchTerm) ||
    loc.description?.toLowerCase().includes(searchTerm) ||
    loc.address?.toLowerCase().includes(searchTerm) ||
    (categoryNames[loc.category] || loc.category).toLowerCase().includes(searchTerm)
  );
  displayLocations(filtered);
}

function handleFilter() {
  const categoryFilter = document.getElementById('categoryFilter');
  const category = categoryFilter?.value;
  if (!category) {
    displayLocations(allLocations);
    return;
  }
  displayLocations(allLocations.filter(loc => loc.category === category));
}

async function showNearest() {
  if (!userLocation) {
    getCurrentLocation();
    return;
  }

  try {
    const response = await fetch(`/api/navigation/nearby?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}&limit=8`);
    const data = await response.json();
    if (response.ok) {
      allLocations = data.nearest || [];
      displayLocations(allLocations);
      showToast(`Found ${data.count} nearby facilities`, 'success');
    } else {
      showToast(data.detail || 'Failed to fetch nearby facilities.', 'error');
    }
  } catch (error) {
    console.error('Nearby error:', error);
    showToast('Unable to fetch nearby facilities.', 'error');
  }
}

async function getCurrentLocation() {
  if (!navigator.geolocation) {
    showToast('Geolocation not supported', 'error');
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      userLocation = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude
      };

      const locationDisplay = document.getElementById('currentLocation');
      if (locationDisplay) {
        locationDisplay.innerHTML = '<p>Finding nearby landmark...</p>';
      }

      try {
        const response = await fetch(`/api/navigation/reverse?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}`);
        const info = await response.json();
        if (locationDisplay) {
          locationDisplay.innerHTML = `
            <strong>${info.display_name || 'Current Location'}</strong>
            <p>${info.address.road || info.address.neighbourhood || info.address.suburb || info.address.city || ''}</p>
          `;
        }
      } catch {
        if (locationDisplay) {
          locationDisplay.innerHTML = `<strong>Your Location</strong><p>${userLocation.latitude.toFixed(6)}, ${userLocation.longitude.toFixed(6)}</p>`;
        }
      }

      showToast('Location obtained', 'success');

      if (map) {
        map.setView([userLocation.latitude, userLocation.longitude], 15);
        if (userMarker) {
          map.removeLayer(userMarker);
        }
        userMarker = L.circleMarker([userLocation.latitude, userLocation.longitude], {
          radius: 8,
          fillColor: '#1d6df4',
          color: '#ffffff',
          weight: 2,
          fillOpacity: 0.9
        }).addTo(map).bindPopup('You are here');
      }

      displayLocations(allLocations);
    },
    () => {
      showToast('Unable to access your location.', 'error');
    },
    { enableHighAccuracy: true, timeout: 15000 }
  );
}

function showToast(message, type = 'info') {
  if (window.showToast) {
    window.showToast(message, type);
  }
}

window.routeToLocation = routeToLocation;
window.selectLocationById = selectLocationById;

document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.navigation-page')) {
    initNavigation();
  }
});
