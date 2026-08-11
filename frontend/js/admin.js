/**
 * admin.js – Full Admin Portal Logic
 * Covers: Pilgrim flow data entry, queue analysis, session info,
 * chart rendering, transport CRUD, crowd upload, emergency alerts.
 */
'use strict';

let _pilgrimChart = null; // Chart.js instance

// ──────────────────────────────────────────────────────────────────────────────
// Queue status badge colour map
// ──────────────────────────────────────────────────────────────────────────────
const STATUS_COLORS = {
  'LOW':       '#10B981',
  'MODERATE':  '#F59E0B',
  'HIGH':      '#F97316',
  'VERY HIGH': '#EF4444',
  'CRITICAL':  '#7C3AED',
  'N/A':       '#6B7280',
};

function queueBadgeClass(status) {
  return {
    'LOW':       'queue-badge-low',
    'MODERATE':  'queue-badge-moderate',
    'HIGH':      'queue-badge-high',
    'VERY HIGH': 'queue-badge-very-high',
    'CRITICAL':  'queue-badge-critical',
  }[status] || 'queue-badge-moderate';
}

// ──────────────────────────────────────────────────────────────────────────────
// Main init – called when admin page is rendered
// ──────────────────────────────────────────────────────────────────────────────
function initAdminModule() {
  // 1. Check if current user is admin
  const authToken = localStorage.getItem('authToken');
  const notice    = document.getElementById('adminAuthNotice');
  const content   = document.getElementById('adminContent');

  if (!authToken) {
    if (notice)  notice.style.display = 'flex';
    if (content) content.hidden = true;
    return;
  }

  // Verify admin role with a quick profile fetch
  API.authGet('profile')
    .then(profile => {
      if (!['admin', 'super_admin'].includes(profile.role)) {
        if (notice)  notice.style.display = 'flex';
        if (content) content.hidden = true;
        return;
      }
      // Authorised
      if (notice)  notice.style.display = 'none';
      if (content) content.hidden = false;

      loadAdminSessionInfo();
      loadAdminDashboard();
      loadPilgrimFlowTable(null);
      setupFlowForm();
      setupAdminRouteForm();
      initAdminCrowdUpload();
      loadAdminEmergencies();
      startAdminClock();
    })
    .catch(() => {
      if (notice)  notice.style.display = 'flex';
      if (content) content.hidden = true;
    });
}

// ──────────────────────────────────────────────────────────────────────────────
// Admin login redirect helper
// ──────────────────────────────────────────────────────────────────────────────
window.loginAsAdmin = function () {
  const authBtn = document.getElementById('authBtn');
  if (authBtn) authBtn.click(); // open auth dialog
  setTimeout(() => {
    if (typeof switchAuthTab === 'function') switchAuthTab('admin');
  }, 100);
};

// ──────────────────────────────────────────────────────────────────────────────
// Session info
// ──────────────────────────────────────────────────────────────────────────────
async function loadAdminSessionInfo() {
  try {
    const info = await API.authGet('admin/session-info');
    const el = (id) => document.getElementById(id);
    if (el('adminHeaderName'))  el('adminHeaderName').textContent  = info.admin_name || info.admin_email || '—';
    if (el('adminHeaderDate'))  el('adminHeaderDate').textContent  = info.server_date || '—';
    if (el('adminHeaderTime'))  el('adminHeaderTime').textContent  = info.server_time || '—';
    if (el('adminSessionIn'))   el('adminSessionIn').textContent   = info.login_time  || '—';
  } catch (_) {}
}

// ──────────────────────────────────────────────────────────────────────────────
// Live clock (updates time every second from local clock offset)
// ──────────────────────────────────────────────────────────────────────────────
function startAdminClock() {
  setInterval(() => {
    const el = document.getElementById('adminHeaderTime');
    if (el) {
      const now = new Date();
      el.textContent = now.toUTCString().split(' ')[4] + ' UTC';
    }
  }, 1000);
}

// ──────────────────────────────────────────────────────────────────────────────
// Admin dashboard summary cards
// ──────────────────────────────────────────────────────────────────────────────
async function loadAdminDashboard() {
  try {
    const d = await API.authGet('admin/dashboard');
    const el = (id) => document.getElementById(id);

    if (el('cardTotalPilgrims'))  el('cardTotalPilgrims').textContent  = (d.total_pilgrims_today || 0).toLocaleString();
    if (el('cardCurrentCrowd'))   el('cardCurrentCrowd').textContent   = (d.current_crowd || 0).toLocaleString();
    if (el('cardIncoming'))       el('cardIncoming').textContent        = (d.total_incoming || 0).toLocaleString();
    if (el('cardOutgoing'))       el('cardOutgoing').textContent        = (d.total_outgoing || 0).toLocaleString();
    if (el('cardQueueStatus'))    el('cardQueueStatus').textContent     = d.queue_status || 'N/A';
    if (el('cardPredictedCrowd')) el('cardPredictedCrowd').textContent  = (d.predicted_crowd || 0).toLocaleString();

    // Colour the queue card
    const qCard = el('cardQueueStatusCard');
    if (qCard) {
      qCard.style.borderColor = STATUS_COLORS[d.queue_status] || '#6B7280';
      qCard.style.boxShadow   = `0 0 12px ${STATUS_COLORS[d.queue_status] || '#6B7280'}44`;
    }
  } catch (_) {}

  // Also load queue analysis
  try {
    const a = await API.authGet('admin/queue-analysis');
    const el = (id) => document.getElementById(id);

    const badge = el('queueStatusBadge');
    if (badge) {
      badge.textContent = a.queue_status || 'MODERATE';
      badge.className = `queue-badge ${queueBadgeClass(a.queue_status)}`;
    }

    if (el('queueTrendDisplay')) {
      const trendArrow = a.trend === 'INCREASING' ? '↑' : (a.trend === 'DECREASING' ? '↓' : '→');
      el('queueTrendDisplay').textContent = `${trendArrow} ${a.trend || 'STABLE'}`;
      el('queueTrendDisplay').style.color = a.trend === 'INCREASING' ? '#EF4444' : (a.trend === 'DECREASING' ? '#10B981' : 'var(--gold)');
    }

    const pressurePct = Math.round((a.queue_pressure || 0) * 100);
    const pBar = el('pressureBar');
    if (pBar) {
      pBar.style.width = `${pressurePct}%`;
      pBar.style.background = pressurePct > 70 ? '#EF4444' : (pressurePct > 40 ? '#F59E0B' : '#10B981');
    }
    if (el('pressurePercent')) el('pressurePercent').textContent = `${pressurePct}%`;
    if (el('queuePredictionText')) el('queuePredictionText').textContent = a.prediction || 'No prediction data yet.';
  } catch (_) {}
}

// ──────────────────────────────────────────────────────────────────────────────
// Pilgrim Flow Data Submission Form
// ──────────────────────────────────────────────────────────────────────────────
function setupFlowForm() {
  // Pre-fill date with today
  const dateInput = document.getElementById('flowDate');
  if (dateInput) {
    dateInput.valueAsDate = new Date();
  }

  // Pre-select nearest time slot
  const slotSelect = document.getElementById('flowTimeSlot');
  if (slotSelect) {
    const h = new Date().getHours();
    const slots = Array.from(slotSelect.options).map(o => o.value);
    const startHour = Math.floor(h / 2) * 2;
    const slotKey = `${String(startHour).padStart(2,'0')}:00|${String((startHour+2)%24).padStart(2,'0')}:00`;
    const matchIdx = slots.indexOf(slotKey);
    if (matchIdx >= 0) slotSelect.selectedIndex = matchIdx;
  }

  const form   = document.getElementById('pilgrimFlowForm');
  const status = document.getElementById('flowFormStatus');
  const btn    = document.getElementById('submitFlowBtn');

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (status) { status.style.color = 'var(--muted)'; status.textContent = '⏳ Submitting…'; }
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Submitting…'; }

    const slotVal = document.getElementById('flowTimeSlot')?.value || '00:00|02:00';
    const [startTime, endTime] = slotVal.split('|');
    const festival = document.querySelector('input[name="festival"]:checked')?.value === 'true';

    const payload = {
      date:               document.getElementById('flowDate')?.value,
      start_time:         startTime,
      end_time:           endTime,
      incoming_pilgrims:  parseInt(document.getElementById('flowIncoming')?.value || '0', 10),
      outgoing_pilgrims:  parseInt(document.getElementById('flowOutgoing')?.value || '0', 10),
      festival,
    };

    try {
      const result = await API.authPost('admin/pilgrim-data', payload);

      if (status) { status.style.color = '#10B981'; status.textContent = '✅ Data submitted successfully.'; }
      if (btn)    { btn.disabled = false; btn.textContent = '⚡ Submit Pilgrim Data'; }

      // Show result box
      const box = document.getElementById('flowResultBox');
      const content = document.getElementById('flowResultContent');
      if (box && content) {
        box.hidden = false;
        content.innerHTML = `
          <div class="result-item"><span>Net Pilgrims</span><strong>${result.net_pilgrims >= 0 ? '+' : ''}${result.net_pilgrims.toLocaleString()}</strong></div>
          <div class="result-item"><span>Est. Crowd</span><strong>${result.estimated_crowd.toLocaleString()}</strong></div>
          <div class="result-item"><span>Queue Status</span><strong style="color:${STATUS_COLORS[result.queue_status] || '#6B7280'}">${result.queue_status}</strong></div>
          <div class="result-item"><span>Crowd Pressure</span><strong>${Math.round(result.queue_pressure * 100)}%</strong></div>
          <div class="result-item"><span>Slot</span><strong>${result.start_time} – ${result.end_time}</strong></div>
          <div class="result-item"><span>Festival</span><strong>${result.festival ? '🎉 YES' : '🗓️ NO'}</strong></div>
        `;
      }

      if (window.showToast) window.showToast('Pilgrim data submitted. Queue analysis updated!', 'success');

      // Refresh dashboard and table
      loadAdminDashboard();
      loadPilgrimFlowTable(document.getElementById('tableFilterDate')?.value || null);
    } catch (err) {
      const msg = err?.detail || err?.message || 'Submission failed.';
      if (status) { status.style.color = '#EF4444'; status.textContent = `❌ ${msg}`; }
      if (btn)    { btn.disabled = false; btn.textContent = '⚡ Submit Pilgrim Data'; }
    }
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Time Slot History Table
// ──────────────────────────────────────────────────────────────────────────────
async function loadPilgrimFlowTable(filterDate) {
  const tbody = document.getElementById('pilgrimFlowBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:1rem; color:var(--muted);">Loading…</td></tr>';

  try {
    const qs = filterDate ? `?date=${filterDate}` : '';
    const rows = await API.authGet(`admin/pilgrim-data${qs}`);

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:1.5rem; color:var(--muted);">No data recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = rows.map(r => {
      const netSign  = r.net_pilgrims >= 0 ? '+' : '';
      const statusColor = STATUS_COLORS[r.queue_status] || '#6B7280';
      return `
        <tr>
          <td>${r.date}</td>
          <td>${r.start_time} – ${r.end_time}</td>
          <td style="color:#10B981; font-weight:600;">↑ ${r.incoming_pilgrims.toLocaleString()}</td>
          <td style="color:#F59E0B; font-weight:600;">↓ ${r.outgoing_pilgrims.toLocaleString()}</td>
          <td style="font-weight:700; color:${r.net_pilgrims >= 0 ? '#10B981' : '#EF4444'}">${netSign}${r.net_pilgrims.toLocaleString()}</td>
          <td style="font-weight:700;">${r.estimated_crowd.toLocaleString()}</td>
          <td><span style="color:${statusColor}; font-weight:700; font-size:0.82rem;">● ${r.queue_status}</span></td>
          <td>${r.festival ? '🎉 YES' : '—'}</td>
        </tr>
      `;
    }).join('');

    // Rebuild chart with fresh data
    renderPilgrimFlowChart(rows);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:1rem; color:var(--danger);">Error: ${err?.detail || err?.message || 'Failed to load data.'}</td></tr>`;
  }
}

// Filter & Refresh buttons
document.getElementById('filterTableBtn')?.addEventListener('click', () => {
  const d = document.getElementById('tableFilterDate')?.value || null;
  loadPilgrimFlowTable(d);
});
document.getElementById('refreshTableBtn')?.addEventListener('click', () => {
  loadPilgrimFlowTable(null);
  loadAdminDashboard();
});

// ──────────────────────────────────────────────────────────────────────────────
// Chart.js Visualization
// ──────────────────────────────────────────────────────────────────────────────
function renderPilgrimFlowChart(rows) {
  if (!window.Chart) return;
  const canvas = document.getElementById('pilgrimFlowChart');
  if (!canvas) return;

  const labels    = rows.map(r => `${r.start_time}–${r.end_time}`);
  const incoming  = rows.map(r => r.incoming_pilgrims);
  const outgoing  = rows.map(r => r.outgoing_pilgrims);
  const crowd     = rows.map(r => r.estimated_crowd);

  if (_pilgrimChart) {
    _pilgrimChart.destroy();
    _pilgrimChart = null;
  }

  const ctx = canvas.getContext('2d');
  _pilgrimChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Incoming Pilgrims',
          data: incoming,
          borderColor: '#10B981',
          backgroundColor: 'rgba(16,185,129,0.12)',
          tension: 0.4,
          pointBackgroundColor: '#10B981',
          fill: true,
        },
        {
          label: 'Outgoing Pilgrims',
          data: outgoing,
          borderColor: '#F59E0B',
          backgroundColor: 'rgba(245,158,11,0.12)',
          tension: 0.4,
          pointBackgroundColor: '#F59E0B',
          fill: true,
        },
        {
          label: 'Estimated Crowd',
          data: crowd,
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239,68,68,0.08)',
          tension: 0.4,
          pointBackgroundColor: '#EF4444',
          borderWidth: 2.5,
          fill: false,
          yAxisID: 'y2',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--text') || '#fff' }
        },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        x: {
          ticks: { color: '#94A3B8', font: { size: 11 } },
          grid:  { color: 'rgba(255,255,255,0.05)' },
        },
        y: {
          position: 'left',
          ticks: { color: '#94A3B8' },
          grid:  { color: 'rgba(255,255,255,0.05)' },
          title: { display: true, text: 'Pilgrims (in/out)', color: '#94A3B8', font: { size: 11 } },
        },
        y2: {
          position: 'right',
          ticks: { color: '#EF4444' },
          grid:  { drawOnChartArea: false },
          title: { display: true, text: 'Estimated Crowd', color: '#EF4444', font: { size: 11 } },
        },
      },
    },
  });
}

// Expose for async Chart.js load
window.initPilgrimChart = function () {
  const rows_el = document.getElementById('pilgrimFlowBody');
  if (!rows_el) return;
  // Re-fetch data if chart is not yet rendered
  API.authGet('admin/pilgrim-data')
    .then(rows => renderPilgrimFlowChart(rows))
    .catch(() => {});
};

// ──────────────────────────────────────────────────────────────────────────────
// Admin Logout
// ──────────────────────────────────────────────────────────────────────────────
document.getElementById('adminLogoutBtn')?.addEventListener('click', () => {
  if (typeof logout === 'function') logout();
});

// ──────────────────────────────────────────────────────────────────────────────
// Crowd Image Upload
// ──────────────────────────────────────────────────────────────────────────────
function initAdminCrowdUpload() {
  const uploadBtn      = document.getElementById('adminUploadCrowdBtn');
  const statusSpan     = document.getElementById('adminCrowdStatus');
  const locationSelect = document.getElementById('adminCrowdLocation');
  const overrideSelect = document.getElementById('adminCrowdOverride');

  if (!uploadBtn) return;

  uploadBtn.addEventListener('click', async () => {
    if (statusSpan) statusSpan.textContent = '⏳ Analyzing crowd image with AI…';
    const locName     = locationSelect ? locationSelect.value : 'VQC I';
    const manualLevel = overrideSelect ? overrideSelect.value : null;
    try {
      const payload = { location_name: locName, manual_crowd_level: manualLevel || undefined };
      const data = await API.authPost('admin/crowd/upload', payload);
      if (statusSpan) {
        statusSpan.style.color = '#10B981';
        statusSpan.textContent = `✅ Crowd Level: ${data.crowd_level || 'HIGH'} (Wait: ${data.estimated_wait_minutes || 180} mins)`;
      }
      if (window.showToast) window.showToast('Live Queue Intelligence updated!', 'success');
    } catch (err) {
      if (statusSpan) { statusSpan.style.color = '#EF4444'; statusSpan.textContent = `ℹ️ ${err.message}`; }
    }
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Transport Routes Admin CRUD (reused from original admin.js)
// ──────────────────────────────────────────────────────────────────────────────
async function loadAdminTransportRoutes() {
  const tbody = document.getElementById('adminRoutesBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:1rem; color:var(--muted);">Loading…</td></tr>';
  try {
    const data   = await API.authGet('transport/search');
    const routes = data.routes || [];
    if (!routes.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:1rem; color:var(--muted);">No transport routes found.</td></tr>';
      return;
    }
    const statusColors = { VERIFIED: '#10B981', NEEDS_REVIEW: '#F59E0B', OUTDATED: '#EF4444', INACTIVE: '#6B7280' };
    tbody.innerHTML = routes.map(r => `
      <tr style="border-bottom: 1px solid var(--border);">
        <td style="padding: 0.65rem 0.5rem;"><strong>${r.route_name || '—'}</strong><br/><small style="color:var(--muted);">${r.source_location || ''} → ${r.destination_location || ''}</small></td>
        <td style="padding: 0.65rem 0.5rem;"><span style="font-size:0.8rem; background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius:4px;">${r.vehicle_type || '—'}</span></td>
        <td style="padding: 0.65rem 0.5rem; font-weight:700; color: var(--gold);">${r.fare || 'FREE'}</td>
        <td style="padding: 0.65rem 0.5rem;"><span style="color: ${statusColors[r.data_status] || '#10B981'}; font-weight:700; font-size:0.8rem;">● ${r.data_status || 'VERIFIED'}</span></td>
        <td style="padding: 0.65rem 0.5rem; font-size: 0.8rem; color: var(--muted);">${r.last_verified || '—'}</td>
        <td style="padding: 0.65rem 0.5rem;">
          <button onclick="adminEditRoute(${r.id})" style="font-size:0.78rem; padding:0.3rem 0.65rem; border-radius:4px; border:1px solid var(--border); background:transparent; color:var(--gold); cursor:pointer; margin-right:0.35rem;">✏️ Edit</button>
          <button onclick="adminDeleteRoute(${r.id}, '${(r.route_name||'').replace(/'/g,'')}')" style="font-size:0.78rem; padding:0.3rem 0.65rem; border-radius:4px; border:1px solid var(--danger); background:transparent; color:var(--danger); cursor:pointer;">🗑️ Delete</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1rem; color:var(--danger);">Could not load routes: ${err.message}</td></tr>`;
  }
}

function setupAdminRouteForm() {
  const form = document.getElementById('adminAddRouteForm');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const statusEl = document.getElementById('adminRouteFormStatus');
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    const routeId = form.dataset.editId || null;
    const payload = {
      route_name: body.route_name || '', source_location: body.source_location || '',
      destination_location: body.destination_location || '', vehicle_type: body.vehicle_type || 'APSRTC Bus',
      operator: body.operator || 'APSRTC', fare: body.fare || 'FREE',
      estimated_duration: body.estimated_duration || '', data_status: body.data_status || 'VERIFIED', is_active: true,
    };
    if (statusEl) { statusEl.style.color = 'var(--muted)'; statusEl.textContent = '⏳ Saving…'; }
    try {
      if (routeId) {
        await API.authPut(`transport/admin/routes/${routeId}`, payload);
        if (statusEl) { statusEl.style.color = '#10B981'; statusEl.textContent = '✅ Route updated successfully.'; }
      } else {
        await API.authPost('transport/admin/routes', payload);
        if (statusEl) { statusEl.style.color = '#10B981'; statusEl.textContent = '✅ Route added successfully.'; }
      }
      form.reset(); delete form.dataset.editId;
      const sb = form.querySelector('button[type="submit"]');
      if (sb) sb.textContent = '➕ Save Transport Route';
      await loadAdminTransportRoutes();
    } catch (err) {
      if (statusEl) { statusEl.style.color = 'var(--danger)'; statusEl.textContent = `❌ ${err.message || 'Failed to save route.'}`; }
    }
  });
  loadAdminTransportRoutes();
}

window.adminEditRoute = async function (routeId) {
  try {
    const data = await API.authGet(`transport/routes/${routeId}`);
    const r = data.route || data;
    const form = document.getElementById('adminAddRouteForm');
    if (!form) return;
    form.querySelector('[name="route_name"]').value = r.route_name || '';
    form.querySelector('[name="source_location"]').value = r.source_location || '';
    form.querySelector('[name="destination_location"]').value = r.destination_location || '';
    form.querySelector('[name="vehicle_type"]').value = r.vehicle_type || 'APSRTC Bus';
    form.querySelector('[name="operator"]').value = r.operator || '';
    form.querySelector('[name="fare"]').value = r.fare || '';
    form.querySelector('[name="estimated_duration"]').value = r.estimated_duration || '';
    form.querySelector('[name="data_status"]').value = r.data_status || 'VERIFIED';
    form.dataset.editId = routeId;
    const sb = form.querySelector('button[type="submit"]');
    if (sb) sb.textContent = '💾 Update Transport Route';
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const statusEl = document.getElementById('adminRouteFormStatus');
    if (statusEl) { statusEl.style.color = 'var(--gold)'; statusEl.textContent = `Editing Route #${routeId}. Make changes then click Update.`; }
  } catch (err) { alert(`Could not load route: ${err.message}`); }
};

window.adminDeleteRoute = async function (routeId, routeName) {
  if (!confirm(`⚠️ Delete route:\n"${routeName}"?\n\nThis cannot be undone.`)) return;
  try {
    await API.authDelete(`transport/admin/routes/${routeId}`);
    if (window.showToast) window.showToast(`Route "${routeName}" deleted.`, 'success');
    await loadAdminTransportRoutes();
  } catch (err) { alert(`Failed to delete route: ${err.message}`); }
};

// ──────────────────────────────────────────────────────────────────────────────
// Emergency Alerts
// ──────────────────────────────────────────────────────────────────────────────
async function loadAdminEmergencies() {
  const tbody = document.getElementById('alertsBody');
  if (!tbody) return;
  try {
    const alerts = await API.authGet('admin/emergencies');
    if (!alerts.length) { tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1rem; color:var(--muted);">No emergency alerts.</td></tr>'; return; }
    tbody.innerHTML = alerts.slice(0, 20).map(a => `
      <tr>
        <td>${a.id}</td>
        <td>${a.alert_type}</td>
        <td style="color:${a.status === 'open' ? '#EF4444' : '#10B981'};">${a.status}</td>
        <td style="font-size:0.8rem; color:var(--muted);">${new Date(a.created_at).toLocaleString()}</td>
      </tr>
    `).join('');
  } catch (_) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1rem; color:var(--muted);">Could not load alerts.</td></tr>';
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// Exports
// ──────────────────────────────────────────────────────────────────────────────
window.initAdminModule          = initAdminModule;
window.loadAdminTransportRoutes = loadAdminTransportRoutes;
