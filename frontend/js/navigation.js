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
let routingControl = null;

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
  document.getElementById('getDirectionsBtn')?.addEventListener('click', handleGetDirections);
  document.getElementById('destinationInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleGetDirections();
  });
  document.getElementById('nearestBtn')?.addEventListener('click', showNearest);
  document.getElementById('recenterBtn')?.addEventListener('click', recenterMap);
  document.getElementById('zoomInBtn')?.addEventListener('click', () => map && map.zoomIn());
  document.getElementById('zoomOutBtn')?.addEventListener('click', () => map && map.zoomOut());
  document.getElementById('fullscreenBtn')?.addEventListener('click', toggleFullscreen);
  document.getElementById('startNavigationBtn')?.addEventListener('click', startNavigation);
  
  // Category filter buttons
  document.querySelectorAll('.category-filter-btn').forEach(btn => {
    btn.addEventListener('click', handleCategoryFilter);
  });

  initializeMap();
  loadLocations();
}

function handleCategoryFilter(e) {
  const category = e.target.dataset.category;
  
  // Update active state
  document.querySelectorAll('.category-filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  e.target.classList.add('active');
  
  // Filter locations
  if (category === 'all') {
    displayLocations(allLocations);
  } else {
    const filtered = allLocations.filter(loc => loc.category === category);
    displayLocations(filtered);
  }
}

function setupAutocomplete() {
  const input = document.getElementById('destinationInput');
  const suggestions = document.getElementById('destinationSuggestions');
  
  if (!input || !suggestions) return;
  
  input.addEventListener('input', (e) => {
    const value = e.target.value.toLowerCase();
    if (value.length < 2) {
      suggestions.classList.add('hidden');
      return;
    }
    
    const matches = allLocations.filter(loc => 
      loc.name.toLowerCase().includes(value) ||
      loc.category.toLowerCase().includes(value) ||
      loc.address?.toLowerCase().includes(value)
    ).slice(0, 5);
    
    if (matches.length > 0) {
      suggestions.innerHTML = matches.map(loc => 
        `<div class="suggestion-item" onclick="selectDestination(${loc.id})">
          <span class="suggestion-icon">${categoryIcons[loc.category] || '📍'}</span>` +
          `<span class="suggestion-name">${loc.name}</span>` +
          `<span class="suggestion-category">${categoryNames[loc.category] || loc.category}</span>
        `).join('');
      suggestions.classList.remove('hidden');
    } else {
      suggestions.classList.add('hidden');
    }
  });
  
  input.addEventListener('blur', () => {
    setTimeout(() => suggestions.classList.add('hidden'), 200);
  });
}

function selectDestination(id) {
  const location = allLocations.find(loc => loc.id === id);
  if (!location) return;
  
  const input = document.getElementById('destinationInput');
  if (input) {
    input.value = location.name;
  }
  
  document.getElementById('destinationSuggestions')?.classList.add('hidden');
  selectedLocation = location;
  
  const summary = document.getElementById('routeSummary');
  if (summary) {
    summary.innerHTML = `
      <div class="route-panel">
        <h4>${location.name}</h4>
        <p>${categoryNames[location.category] || location.category}</p>
        <p>${location.address || 'No address available'}</p>
        <div class="route-stat-row"><span>Distance</span><strong>${location.distance_text || '—'}</strong></div>
        <div class="route-stat-row"><span>Walking Time</span><strong>${location.walking_time || '—'}</strong></div>
        <div class="route-stat-row"><span>Crowd</span><strong>${location.crowd_level || 'Moderate'}</strong></div>
      </div>
    `;
  }
  
  if (map) {
    map.setView([location.latitude, location.longitude], 16);
  }
}

function handleGetDirections() {
  const input = document.getElementById('destinationInput');
  const destinationName = input?.value.trim();
  
  if (!destinationName) {
    showToast('Please enter a destination', 'warning');
    return;
  }
  
  // Find location by name
  const destination = allLocations.find(loc => 
    loc.name.toLowerCase() === destinationName.toLowerCase() ||
    loc.name.toLowerCase().includes(destinationName.toLowerCase())
  );
  
  if (destination) {
    routeToLocation(destination.id);
  } else {
    showToast('Destination not found. Try selecting from the list.', 'warning');
  }
}

function toggleFullscreen() {
  const mapCard = document.querySelector('.map-card');
  if (!mapCard) return;
  
  if (!document.fullscreenElement) {
    mapCard.requestFullscreen?.() || mapCard.webkitRequestFullscreen?.();
  } else {
    document.exitFullscreen?.() || document.webkitExitFullscreen?.();
  }
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
  // Default Tirumala locations if API fails
  allLocations = getDefaultTirumalaLocations();
  
  try {
    const data = await API.get('locations');
    if (data.locations && data.locations.length > 0) {
      allLocations = data.locations;
    }
  } catch (error) {
    console.log('Using default locations:', error);
  }
  
  displayLocations(allLocations);
  setupAutocomplete();
}

function getDefaultTirumalaLocations() {
  return [
    {
      id: 1,
      name: 'Sri Venkateswara Temple',
      category: 'temple',
      latitude: 13.6839,
      longitude: 79.3476,
      address: 'Tirumala, Andhra Pradesh 517504',
      description: 'Main temple of Lord Venkateswara',
      distance_text: '0 km',
      walking_time: '0 min',
      crowd_level: 'High',
      status: 'Open'
    },
    {
      id: 2,
      name: 'Alipiri Padala Mandapam',
      category: 'footpath',
      latitude: 13.6150,
      longitude: 79.3670,
      address: 'Alipiri, Tirupati',
      description: 'Starting point for footpath trek',
      distance_text: '12 km',
      walking_time: '4 hours',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      name: 'Srivari Mettu',
      category: 'footpath',
      latitude: 13.6280,
      longitude: 79.3580,
      address: 'Tirumala Footpath',
      description: 'Ancient footpath route to temple',
      distance_text: '8 km',
      walking_time: '2.5 hours',
      crowd_level: 'High',
      status: 'Open'
    },
    {
      id: 3,
      name: 'TTD Annaprasadam Complex',
      category: 'food',
      latitude: 13.6810,
      longitude: 79.3490,
      address: 'Tirumala',
      description: 'Free food distribution center',
      distance_text: '0.5 km',
      walking_time: '5 min',
      crowd_level: 'High',
      status: 'Open'
    },
    {
      id: 4,
      name: 'Laddu Counter',
      category: 'laddu',
      latitude: 13.6820,
      longitude: 79.3480,
      address: 'Temple Complex',
      description: 'Famous Tirumala Laddu',
      distance_text: '0.3 km',
      walking_time: '3 min',
      crowd_level: 'Very High',
      status: 'Open'
    },
    {
      id: 5,
      name: 'RTC Bus Stand',
      category: 'transport',
      latitude: 13.6790,
      longitude: 79.3500,
      address: 'Tirumala Bus Stand',
      description: 'Main bus station',
      distance_text: '0.8 km',
      walking_time: '8 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 6,
      name: 'TTD Central Hospital',
      category: 'medical',
      latitude: 13.6770,
      longitude: 79.3510,
      address: 'Tirumala',
      description: '24/7 medical facility',
      distance_text: '1 km',
      walking_time: '10 min',
      crowd_level: 'Low',
      status: 'Open'
    },
    {
      id: 7,
      name: 'Parking Area',
      category: 'parking',
      latitude: 13.6750,
      longitude: 79.3520,
      address: 'Tirumala',
      description: 'Vehicle parking',
      distance_text: '1.2 km',
      walking_time: '12 min',
      crowd_level: 'High',
      status: 'Open'
    },
    {
      id: 8,
      name: 'Restroom Complex',
      category: 'restroom',
      latitude: 13.6800,
      longitude: 79.3495,
      address: 'Temple Area',
      description: 'Public restrooms',
      distance_text: '0.4 km',
      walking_time: '4 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 9,
      name: 'Drinking Water Points',
      category: 'water',
      latitude: 13.6815,
      longitude: 79.3485,
      address: 'Multiple locations',
      description: 'Free drinking water',
      distance_text: '0.2 km',
      walking_time: '2 min',
      crowd_level: 'Low',
      status: 'Open'
    },
    {
      id: 10,
      name: 'Tonsure Centre',
      category: 'tonsure',
      latitude: 13.6785,
      longitude: 79.3505,
      address: 'Tirumala',
      description: 'Head tonsure facility',
      distance_text: '0.6 km',
      walking_time: '6 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 11,
      name: 'Police Station',
      category: 'police',
      latitude: 13.6765,
      longitude: 79.3515,
      address: 'Tirumala',
      description: 'Police assistance',
      distance_text: '0.9 km',
      walking_time: '9 min',
      crowd_level: 'Low',
      status: 'Open'
    },
    {
      id: 12,
      name: 'Information Centre',
      category: 'information',
      latitude: 13.6825,
      longitude: 79.3475,
      address: 'Temple Complex',
      description: 'Tourist information',
      distance_text: '0.1 km',
      walking_time: '1 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 13,
      name: 'Cloak Room',
      category: 'cloak_room',
      latitude: 13.6810,
      longitude: 79.3480,
      address: 'Temple Complex',
      description: 'Luggage storage',
      distance_text: '0.3 km',
      walking_time: '3 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 14,
      name: 'Phone Deposit Counter',
      category: 'phone_deposit',
      latitude: 13.6820,
      longitude: 79.3470,
      address: 'Temple Entrance',
      description: 'Mobile phone storage',
      distance_text: '0.2 km',
      walking_time: '2 min',
      crowd_level: 'High',
      status: 'Open'
    },
    {
      id: 15,
      name: 'Queue Complex',
      category: 'queue',
      latitude: 13.6830,
      longitude: 79.3465,
      address: 'Temple Complex',
      description: 'Darshan queue lines',
      distance_text: '0.1 km',
      walking_time: '1 min',
      crowd_level: 'Very High',
      status: 'Open'
    },
    {
      id: 16,
      name: 'Pilgrim Amenities Centre',
      category: 'accommodation',
      latitude: 13.6740,
      longitude: 79.3530,
      address: 'Tirumala',
      description: 'Pilgrim accommodation',
      distance_text: '1.5 km',
      walking_time: '15 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 17,
      name: 'Swami Pushkarini Tank',
      category: 'temple',
      latitude: 13.6845,
      longitude: 79.3465,
      address: 'Temple Complex',
      description: 'Sacred temple tank',
      distance_text: '0.1 km',
      walking_time: '1 min',
      crowd_level: 'Moderate',
      status: 'Open'
    },
    {
      id: 18,
      name: 'Varahaswamy Temple',
      category: 'temple',
      latitude: 13.6850,
      longitude: 79.3460,
      address: 'Tirumala',
      description: 'Ancient Varahaswamy temple',
      distance_text: '0.2 km',
      walking_time: '2 min',
      crowd_level: 'Low',
      status: 'Open'
    }
  ];
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

  // Use OSRM for routing (free, works like Google Maps)
  try {
    const osrmUrl = `https://router.project-osrm.org/route/v1/walking/${userLocation.longitude},${userLocation.latitude};${destination.longitude},${destination.latitude}?overview=full&geometries=geojson&steps=true`;
    const response = await fetch(osrmUrl);
    const data = await response.json();
    
    if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
      const route = data.routes[0];
      renderOSRMRoute(route, destination);
      selectLocation(destination);
      showToast(`Navigating to ${destination.name}`, 'success');
    } else {
      showToast('Unable to calculate route. Showing direct path.', 'warning');
      showDirectRoute(destination);
    }
  } catch (error) {
    console.error('Route error:', error);
    showToast('Using direct path to destination.', 'warning');
    showDirectRoute(destination);
  }
}

function renderOSRMRoute(route, destination) {
  if (!map) return;

  clearRoute();

  // Add user marker
  if (userMarker) {
    map.removeLayer(userMarker);
  }
  userMarker = L.circleMarker([userLocation.latitude, userLocation.longitude], {
    radius: 8,
    fillColor: '#16A34A',
    color: '#ffffff',
    weight: 2,
    fillOpacity: 0.9
  }).addTo(map).bindPopup('You are here');

  // Add destination marker
  destinationMarker = L.marker([destination.latitude, destination.longitude], {
    icon: L.divIcon({
      className: 'destination-marker',
      html: '<div class="dest-icon">🏁</div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })
  }).addTo(map).bindPopup(destination.name);

  // Draw route
  if (route.geometry && route.geometry.coordinates) {
    const latLngs = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
    routeLayer = L.polyline(latLngs, {
    color: '#16A34A',
    weight: 6,
    opacity: 0.8,
    smoothFactor: 1
    }).addTo(map);
    
    map.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });
  }

  // Update route summary
  const distance = (route.distance / 1000).toFixed(2);
  const duration = Math.round(route.duration / 3600 * 60); // Convert to minutes
  const eta = new Date(Date.now() + route.duration * 1000);
  
  const summary = document.getElementById('routeSummary');
  if (summary) {
    summary.innerHTML = `
      <div class="route-panel">
        <h4>Route to ${destination.name}</h4>
        <div class="route-stat-row"><span>Distance</span><strong>${distance} km</strong></div>
        <div class="route-stat-row"><span>Walking Time</span><strong>${duration} min</strong></div>
        <div class="route-stat-row"><span>ETA</span><strong>${eta.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong></div>
        <button class="quick-action-btn" onclick="startNavigation()">🧭 Start Navigation</button>
      </div>
    `;
    
    document.getElementById('startNavigationBtn').classList.remove('hidden');
  }

  // Update turn-by-turn directions
  const steps = document.getElementById('directionSteps');
  if (steps && route.legs && route.legs[0] && route.legs[0].steps) {
    const instructions = route.legs[0].steps.map((step, index) => {
      const stepDistance = (step.distance / 1000).toFixed(2);
      const stepDuration = Math.round(step.duration / 60);
      return `
        <div class="direction-step">
          <p><strong>${index + 1}.</strong> ${step.maneuver.type.replace(/_/g, ' ').toUpperCase()}</p>
          <p>${step.name || 'Continue'}</p>
          <small>${stepDistance} km • ${stepDuration} min</small>
        </div>
      `;
    }).join('');
    
    steps.innerHTML = instructions || '<p class="hint">No turn-by-turn instructions available.</p>';
  }
}

function showDirectRoute(destination) {
  if (!map) return;

  clearRoute();

  // Add user marker
  if (userMarker) {
    map.removeLayer(userMarker);
  }
  userMarker = L.circleMarker([userLocation.latitude, userLocation.longitude], {
    radius: 8,
    fillColor: '#16A34A',
    color: '#ffffff',
    weight: 2,
    fillOpacity: 0.9
  }).addTo(map).bindPopup('You are here');

  // Add destination marker
  destinationMarker = L.marker([destination.latitude, destination.longitude], {
    icon: L.divIcon({
      className: 'destination-marker',
      html: '<div class="dest-icon">🏁</div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })
  }).addTo(map).bindPopup(destination.name);

  // Draw direct line
  routeLayer = L.polyline([[userLocation.latitude, userLocation.longitude], [destination.latitude, destination.longitude]], {
    color: '#16A34A',
    weight: 6,
    opacity: 0.5,
    dashArray: '10, 10'
  }).addTo(map);
  
  map.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });

  const summary = document.getElementById('routeSummary');
  if (summary) {
    summary.innerHTML = `
      <div class="route-panel">
        <h4>Route to ${destination.name}</h4>
        <div class="route-stat-row"><span>Distance</span><strong>${destination.distance_text || '—'}</strong></div>
        <div class="route-stat-row"><span>Walking Time</span><strong>${destination.walking_time || '—'}</strong></div>
        <p class="hint">Direct path shown. Detailed routing unavailable.</p>
      </div>
    `;
  }
  
  const steps = document.getElementById('directionSteps');
  if (steps) {
    steps.innerHTML = '<p class="hint">Head towards destination following the direct path.</p>';
  }
}

function startNavigation() {
  showToast('Navigation started! Follow the green path.', 'success');
  // Add navigation simulation here if needed
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
    const data = await API.get(`navigation/nearby?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}&limit=8`);
    allLocations = data.nearest || [];
    displayLocations(allLocations);
    showToast(`Found ${data.count || allLocations.length} nearby facilities`, 'success');
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
        const info = await API.get(`navigation/reverse?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}`);
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
window.selectDestination = selectDestination;
window.startNavigation = startNavigation;

document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.navigation-page')) {
    initNavigation();
  }
});
