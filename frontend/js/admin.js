/**
 * admin.js – Admin Dashboard, Crowd Management & Transport Route Management
 * Handles crowd image analysis, analytics fetching, and transport admin CRUD.
 */
'use strict';

// ── Crowd Upload Module ────────────────────────────────────────────────────
function initAdminModule() {
  const uploadBtn    = document.getElementById('adminUploadCrowdBtn');
  const statusSpan   = document.getElementById('adminCrowdStatus');
  const locationSelect = document.getElementById('adminCrowdLocation');
  const overrideSelect = document.getElementById('adminCrowdOverride');

  if (uploadBtn) {
    uploadBtn.addEventListener('click', async () => {
      if (statusSpan) statusSpan.textContent = '⏳ Analyzing crowd image with AI...';

      const locName    = locationSelect ? locationSelect.value : 'VQC I';
      const manualLevel = overrideSelect ? overrideSelect.value : null;

      try {
        const payload = {
          location_name: locName,
          manual_crowd_level: manualLevel || undefined
        };

        const data = await API.authPost('admin/crowd/upload', payload);
        if (statusSpan) {
          statusSpan.style.color = '#10B981';
          statusSpan.textContent = `✅ Success! Crowd Level: ${data.crowd_level || 'HIGH'} (Estimated Wait: ${data.estimated_wait_minutes || 180} mins)`;
        }
        if (window.showToast) window.showToast('Live Queue Intelligence updated successfully!', 'success');
      } catch (err) {
        console.warn('Admin upload notice:', err.message);
        if (statusSpan) {
          statusSpan.style.color = '#EF4444';
          statusSpan.textContent = `ℹ️ ${err.message}`;
        }
      }
    });
  }

  // Setup Transport Route form
  setupAdminRouteForm();
}

// ── Transport Routes Admin Management ────────────────────────────────────
async function loadAdminTransportRoutes() {
  const tbody = document.getElementById('adminRoutesBody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:1rem; color:var(--muted);">Loading transport routes...</td></tr>';

  try {
    const data = await API.authGet('transport/search');
    const routes = data.routes || [];

    if (!routes.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:1rem; color:var(--muted);">No transport routes found. Add one above.</td></tr>';
      return;
    }

    const statusColors = {
      'VERIFIED':     '#10B981',
      'NEEDS_REVIEW': '#F59E0B',
      'OUTDATED':     '#EF4444',
      'INACTIVE':     '#6B7280'
    };

    tbody.innerHTML = routes.map(r => `
      <tr style="border-bottom: 1px solid var(--border);">
        <td style="padding: 0.65rem 0.5rem;">
          <strong style="font-size:0.9rem;">${r.route_name || '—'}</strong><br/>
          <small style="color:var(--muted);">${r.source_location || ''} → ${r.destination_location || ''}</small>
        </td>
        <td style="padding: 0.65rem 0.5rem;">
          <span style="font-size:0.8rem; background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius:4px;">${r.vehicle_type || '—'}</span>
        </td>
        <td style="padding: 0.65rem 0.5rem; font-weight:700; color: var(--gold);">${r.fare || 'FREE'}</td>
        <td style="padding: 0.65rem 0.5rem;">
          <span style="color: ${statusColors[r.data_status] || '#10B981'}; font-weight: 700; font-size:0.8rem;">● ${r.data_status || 'VERIFIED'}</span>
        </td>
        <td style="padding: 0.65rem 0.5rem; font-size: 0.8rem; color: var(--muted);">${r.last_verified || '—'}</td>
        <td style="padding: 0.65rem 0.5rem;">
          <button
            onclick="adminEditRoute(${r.id})"
            style="font-size:0.78rem; padding:0.3rem 0.65rem; border-radius:4px; border:1px solid var(--border); background:transparent; color:var(--gold); cursor:pointer; margin-right:0.35rem;"
          >✏️ Edit</button>
          <button
            onclick="adminDeleteRoute(${r.id}, '${(r.route_name || '').replace(/'/g, '')}')"
            style="font-size:0.78rem; padding:0.3rem 0.65rem; border-radius:4px; border:1px solid var(--danger); background:transparent; color:var(--danger); cursor:pointer;"
          >🗑️ Delete</button>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Failed to load transport routes:', err);
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

    // Build the payload matching the API schema
    const routeId = form.dataset.editId || null;
    const payload = {
      route_name:           body.route_name || '',
      source_location:      body.source_location || '',
      destination_location: body.destination_location || '',
      vehicle_type:         body.vehicle_type || 'APSRTC Bus',
      operator:             body.operator || 'APSRTC',
      fare:                 body.fare || 'FREE',
      estimated_duration:   body.estimated_duration || '',
      data_status:          body.data_status || 'VERIFIED',
      is_active:            true,
    };

    if (statusEl) { statusEl.style.color = 'var(--muted)'; statusEl.textContent = '⏳ Saving...'; }

    try {
      if (routeId) {
        // Update existing route
        await API.authPut(`transport/admin/routes/${routeId}`, payload);
        if (statusEl) { statusEl.style.color = '#10B981'; statusEl.textContent = '✅ Route updated successfully.'; }
      } else {
        // Create new route
        await API.authPost('transport/admin/routes', payload);
        if (statusEl) { statusEl.style.color = '#10B981'; statusEl.textContent = '✅ Route added successfully.'; }
      }

      form.reset();
      delete form.dataset.editId;
      // Restore button label
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.textContent = '➕ Save Transport Route';

      // Reload table
      await loadAdminTransportRoutes();

    } catch (err) {
      console.error('Save transport route failed:', err);
      if (statusEl) { statusEl.style.color = 'var(--danger)'; statusEl.textContent = `❌ ${err.message || 'Failed to save route.'}`; }
    }
  });
}

// Edit: populate form with existing route data
window.adminEditRoute = async function(routeId) {
  try {
    const data = await API.authGet(`transport/routes/${routeId}`);
    const r = data.route || data;
    const form = document.getElementById('adminAddRouteForm');
    if (!form) return;

    // Populate all fields
    form.querySelector('[name="route_name"]').value           = r.route_name || '';
    form.querySelector('[name="source_location"]').value      = r.source_location || '';
    form.querySelector('[name="destination_location"]').value = r.destination_location || '';
    form.querySelector('[name="vehicle_type"]').value         = r.vehicle_type || 'APSRTC Bus';
    form.querySelector('[name="operator"]').value             = r.operator || '';
    form.querySelector('[name="fare"]').value                 = r.fare || '';
    form.querySelector('[name="estimated_duration"]').value   = r.estimated_duration || '';
    form.querySelector('[name="data_status"]').value          = r.data_status || 'VERIFIED';

    // Mark form in edit mode
    form.dataset.editId = routeId;
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.textContent = '💾 Update Transport Route';

    // Scroll to form
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });

    const statusEl = document.getElementById('adminRouteFormStatus');
    if (statusEl) { statusEl.style.color = 'var(--gold)'; statusEl.textContent = `Editing Route #${routeId}. Make changes then click Update.`; }

  } catch (err) {
    console.error('Failed to load route for editing:', err);
    alert(`Could not load route for editing: ${err.message}`);
  }
};

// Delete route with confirmation
window.adminDeleteRoute = async function(routeId, routeName) {
  if (!confirm(`⚠️ Are you sure you want to delete the route:\n"${routeName}"?\n\nThis action cannot be undone.`)) return;

  try {
    await API.authDelete(`transport/admin/routes/${routeId}`);
    if (window.showToast) window.showToast(`Route "${routeName}" deleted.`, 'success');
    await loadAdminTransportRoutes();
  } catch (err) {
    console.error('Delete transport route failed:', err);
    alert(`Failed to delete route: ${err.message}`);
  }
};

window.initAdminModule = initAdminModule;
window.loadAdminTransportRoutes = loadAdminTransportRoutes;
