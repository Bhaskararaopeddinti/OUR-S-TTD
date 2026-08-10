/**
 * transport.js – OURS TTD Travel & Transport Module
 * Full bus card rendering with demo data disclaimer, View Details modal, and AI integration.
 */

'use strict';

function initTransport() {
  const searchBtn = document.getElementById('transportSearchBtn');
  const fromSelect = document.getElementById('transportFromSelect');
  const toSelect   = document.getElementById('transportToSelect');
  const modeSelect = document.getElementById('transportModeSelect');

  if (searchBtn) {
    searchBtn.addEventListener('click', () => {
      fetchAndRenderRoutes(fromSelect?.value || '', toSelect?.value || '', modeSelect?.value || '');
    });
  }

  // Load all routes on page open
  fetchAndRenderRoutes('', '', '');
}

async function fetchAndRenderRoutes(fromLoc, toLoc, mode) {
  const container = document.getElementById('transportRoutesContainer');
  if (!container) return;

  container.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--muted);">🔍 Searching transport routes...</div>`;

  try {
    const params = new URLSearchParams();
    if (fromLoc) params.append('from_location', fromLoc);
    if (toLoc)   params.append('to_location', toLoc);
    if (mode)    params.append('vehicle_type', mode);

    const data = await API.get(`transport/search?${params.toString()}`);

    if (data && data.routes && data.routes.length > 0) {
      renderRouteCards(data.routes, container, fromLoc, toLoc);
    } else {
      renderNoResults(container, fromLoc, toLoc);
    }
  } catch (error) {
    console.error('Transport API error:', error);
    container.innerHTML = `
      <div class="dashboard-card" style="text-align:center;padding:2rem;color:var(--danger);">
        <p>⚠️ Unable to load transport options. Please check your connection and try again.</p>
        <button class="btn-ghost" style="margin-top:1rem;" onclick="fetchAndRenderRoutes('','','')">🔄 Retry</button>
      </div>`;
  }
}

function renderNoResults(container, fromLoc, toLoc) {
  const fromStr = fromLoc || 'selected origin';
  const toStr   = toLoc   || 'selected destination';
  container.innerHTML = `
    <div class="dashboard-card" style="text-align:center;padding:2.5rem 2rem;color:var(--muted);">
      <div style="font-size:2.5rem;margin-bottom:1rem;">🚌</div>
      <h3 style="color:var(--text);margin-bottom:0.5rem;">No direct bus route listed for this route</h3>
      <p style="margin-bottom:1rem;">No transport route found from <strong>${fromStr}</strong> to <strong>${toStr}</strong>.</p>
      <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:1rem;text-align:left;max-width:400px;margin:0 auto 1.25rem;">
        <p style="font-size:0.9rem;font-weight:600;margin-bottom:0.5rem;">You can try:</p>
        <ul style="font-size:0.85rem;line-height:2;padding-left:1.2rem;">
          <li>🔄 <strong>Nearby bus connection</strong> via Tirupati Bus Station</li>
          <li>🚕 <strong>Taxi / Cab</strong> from local stands</li>
          <li>🚶 <strong>Walking</strong> (Alipiri or Srivari Mettu footpath)</li>
          <li>🔍 <strong>Select another nearby pickup point</strong></li>
        </ul>
      </div>
      <div style="display:flex;gap:0.75rem;justify-content:center;flex-wrap:wrap;">
        <button class="btn-ghost" onclick="fetchAndRenderRoutes('','','')">Show All Routes</button>
        <button class="btn-primary" onclick="window.TTDApp && TTDApp.askAIAboutTransport('${fromStr}','${toStr}')">🤖 Ask AI for Alternatives</button>
      </div>
    </div>`;
}

function getVehicleIcon(vehicleType) {
  const icons = {
    'GOVERNMENT_BUS': '🚌',
    'TTD_BUS':        '🚌',
    'WALKING':        '🚶',
    'TAXI':           '🚕',
    'AUTO':           '🛺',
    'PACKAGE_TOUR':   '🛕',
  };
  return icons[vehicleType] || '🚌';
}

function getVehicleLabel(vehicleType) {
  const labels = {
    'GOVERNMENT_BUS': 'APSRTC Government Bus',
    'TTD_BUS':        'TTD Free Bus',
    'WALKING':        'Walking Footpath',
    'TAXI':           'Taxi / Cab',
    'AUTO':           'Auto Rickshaw',
    'PACKAGE_TOUR':   'Package Tour',
  };
  return labels[vehicleType] || vehicleType || 'Bus';
}

function renderRouteCards(routes, container, fromLoc, toLoc) {
  const isFreeRoute = r => r.fare && r.fare.toLowerCase().includes('free');
  const isDemoRoute = r => r.data_status === 'DEMO' || (r.source && r.source.toLowerCase().includes('demo'));

  container.innerHTML = `
    <div style="font-size:0.82rem;color:var(--muted);padding:0.25rem 0 0.5rem;">
      Showing <strong>${routes.length}</strong> transport option${routes.length !== 1 ? 's' : ''}
      ${fromLoc || toLoc ? ` for <strong>${fromLoc || 'Any'}</strong> → <strong>${toLoc || 'Any'}</strong>` : ''}
    </div>
    ${routes.map(r => {
      const icon      = getVehicleIcon(r.vehicle_type);
      const label     = getVehicleLabel(r.vehicle_type);
      const isFree    = isFreeRoute(r);
      const isDemo    = isDemoRoute(r);
      const accentColor = isFree ? '#10B981' : 'var(--gold)';

      return `
      <div class="dashboard-card route-card" style="border-left: 5px solid ${accentColor}; padding: 1.25rem;" id="route-card-${r.id}">

        <!-- Header -->
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">
          <div>
            <span style="background:rgba(255,255,255,0.07);color:${accentColor};font-weight:700;font-size:0.8rem;padding:0.25rem 0.65rem;border-radius:20px;">
              ${icon} ${label}
            </span>
            <h3 style="margin-top:0.5rem;margin-bottom:0.2rem;font-size:1.1rem;">${r.route_name || (r.source_location + ' → ' + r.destination_location)}</h3>
            <p style="font-size:0.85rem;color:var(--muted);">
              📍 ${r.source_location || '—'} &nbsp;→&nbsp; 🏁 ${r.destination_location || '—'}
            </p>
            ${r.route_description ? `<p style="font-size:0.82rem;color:var(--muted);margin-top:0.3rem;">${r.route_description}</p>` : ''}
          </div>
          <div style="text-align:right;flex-shrink:0;">
            <span style="font-size:1.2rem;font-weight:800;color:${accentColor};display:block;">${r.fare || 'Check at counter'}</span>
            <span style="font-size:0.75rem;color:var(--muted);">${r.operator || 'APSRTC / TTD'}</span>
          </div>
        </div>

        <!-- Details Grid -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.65rem;background:rgba(15,23,42,0.4);padding:0.85rem;border-radius:8px;margin-bottom:0.85rem;border:1px solid rgba(255,255,255,0.06);">
          <div>
            <span style="font-size:0.72rem;color:var(--muted);display:block;">DURATION</span>
            <strong>⏱️ ${r.estimated_duration || 'N/A'}</strong>
          </div>
          <div>
            <span style="font-size:0.72rem;color:var(--muted);display:block;">FREQUENCY</span>
            <strong>🔄 ${r.frequency || 'Indicative'}</strong>
          </div>
          <div>
            <span style="font-size:0.72rem;color:var(--muted);display:block;">HOURS</span>
            <strong>⏰ ${r.operating_hours || 'Indicative'}</strong>
          </div>
          <div>
            <span style="font-size:0.72rem;color:var(--muted);display:block;">STATUS</span>
            <strong style="color:${r.status === 'Available' || r.status === 'Open' ? '#10B981' : 'var(--muted)'};">● ${r.status || 'Check locally'}</strong>
          </div>
        </div>

        <!-- Demo Disclaimer if applicable -->
        ${isDemo ? `
        <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:6px;padding:0.5rem 0.75rem;margin-bottom:0.85rem;font-size:0.78rem;color:#F59E0B;">
          ⚠️ <strong>Indicative / Demo Information</strong> — Verify at official TTD/APSRTC counter.
        </div>` : ''}

        <!-- Action Buttons -->
        <div style="display:flex;gap:0.65rem;flex-wrap:wrap;">
          <button class="btn-primary" style="padding:0.55rem 1rem;font-size:0.88rem;"
            onclick="window.TTDApp.viewRouteDetails(${r.id}, '${(r.route_name||'').replace(/'/g,'').replace(/"/g,'')}')">
            📋 VIEW DETAILS
          </button>
          <button class="btn-ghost" style="padding:0.55rem 1rem;font-size:0.88rem;"
            onclick="window.TTDApp.navigateToRoute('${(r.source_location||'').replace(/'/g,'')}', '${(r.destination_location||'').replace(/'/g,'')}')">
            🗺️ VIEW ROUTE
          </button>
          <button class="btn-ghost" style="padding:0.55rem 1rem;font-size:0.88rem;color:var(--gold);"
            onclick="window.TTDApp.askAIAboutTransport('${(r.source_location||'').replace(/'/g,'')}', '${(r.destination_location||'').replace(/'/g,'')}')">
            🤖 ASK AI
          </button>
        </div>
      </div>`;
    }).join('')}
  `;
}

// ── Global TTDApp Helpers ────────────────────────────────────────────────────
window.TTDApp = window.TTDApp || {};

window.TTDApp.viewRouteDetails = function(routeId, routeNameHint) {
  API.get(`transport/routes/${routeId}`).then(data => {
    if (data && data.route) {
      const r = data.route;
      const isDemo = r.data_status === 'DEMO' || (r.source && r.source.toLowerCase().includes('demo'));
      const detailHtml = `
        <div style="max-width:520px;margin:0 auto;font-family:inherit;">
          <h3 style="margin-bottom:0.75rem;font-size:1.1rem;">${r.route_name || 'Transport Route'}</h3>
          <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
            <tr><td style="padding:0.4rem 0;color:var(--muted);width:140px;">From</td><td><strong>${r.source_location || '—'}</strong></td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">To</td><td><strong>${r.destination_location || '—'}</strong></td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Operator</td><td>${r.operator || '—'}</td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Transport</td><td>${r.vehicle_type || '—'}</td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Fare</td><td><strong style="color:var(--gold);">${r.fare || '—'}</strong></td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Duration</td><td>${r.estimated_duration || '—'}</td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Frequency</td><td>${r.frequency || '—'}</td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Hours</td><td>${r.operating_hours || '—'}</td></tr>
            <tr><td style="padding:0.4rem 0;color:var(--muted);">Status</td><td>${r.status || '—'}</td></tr>
          </table>
          ${r.route_description ? `<p style="margin-top:0.75rem;font-size:0.85rem;color:var(--muted);">${r.route_description}</p>` : ''}
          ${isDemo ? `<div style="margin-top:0.75rem;padding:0.6rem;background:rgba(245,158,11,0.12);border-radius:6px;font-size:0.8rem;color:#F59E0B;">
            ⚠️ Indicative/Demo data. Verify at TTD/APSRTC counters.
          </div>` : ''}
        </div>`;

      if (window.showToast) window.showToast('Route details loaded', 'info', 1500);

      const modal = document.createElement('div');
      modal.id = 'routeDetailModal';
      modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;padding:1rem;';
      modal.innerHTML = `
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:2rem;max-width:560px;width:100%;max-height:90vh;overflow-y:auto;position:relative;">
          <button onclick="document.getElementById('routeDetailModal').remove()"
            style="position:absolute;top:1rem;right:1rem;background:transparent;border:none;font-size:1.4rem;cursor:pointer;color:var(--muted);">✕</button>
          ${detailHtml}
        </div>`;
      document.body.appendChild(modal);
      modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
    }
  }).catch(() => {
    if (window.showToast) window.showToast('Unable to load route details.', 'error');
  });
};

window.TTDApp.navigateToRoute = function(fromLoc, toLoc) {
  if (typeof navigate === 'function') {
    navigate('navigation');
    setTimeout(() => {
      if (window.NavigationModule && typeof window.NavigationModule.setRoute === 'function') {
        window.NavigationModule.setRoute(fromLoc, toLoc);
      }
      if (window.showToast) window.showToast(`Route: ${fromLoc} → ${toLoc}`, 'info');
    }, 400);
  }
};

window.TTDApp.showRouteDetails = window.TTDApp.viewRouteDetails;

window.TTDApp.askAIAboutTransport = function(fromLoc, toLoc) {
  if (typeof navigate === 'function') {
    navigate('chatbot');
    setTimeout(() => {
      const input = document.getElementById('chatInput') || document.getElementById('chatbotInput');
      const sendBtn = document.getElementById('sendBtn') || document.getElementById('chatSend');
      if (input) {
        input.value = `How can I travel from ${fromLoc} to ${toLoc}? What are the bus options, fares and operating hours?`;
        if (typeof sendMessage === 'function') {
          sendMessage();
        } else if (sendBtn) {
          sendBtn.click();
        }
      }
    }, 500);
  }
};

// Auto-initialize when DOM has the transport page
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.transport-page')) {
    initTransport();
  }
});
