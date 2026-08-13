/**
 * sos.js – Emergency SOS dialog handling with geolocation.
 * Safely initialises only when required DOM elements are present.
 */
'use strict';

function initSOS() {
  const sosFab    = document.getElementById('sosFab');
  const sosDialog = document.getElementById('sosDialog');
  const sosClose  = document.getElementById('sosClose');
  const sosOptions = document.getElementById('sosOptions');
  const sosResult  = document.getElementById('sosResult');

  // Guard: only set up listeners if the SOS elements exist on this page
  if (!sosFab || !sosDialog) return;

  sosFab.addEventListener('click', () => sosDialog.showModal());
  if (sosClose) sosClose.addEventListener('click', () => sosDialog.close());

  if (sosOptions) {
    sosOptions.addEventListener('click', async e => {
      const btn = e.target.closest('button');
      if (!btn) return;
      if (sosResult) {
        sosResult.className = 'status';
        sosResult.textContent = '📡 Sending your location to support desk…';
      }

      let position = {};
      try {
        position = await new Promise((ok, bad) =>
          navigator.geolocation.getCurrentPosition(
            p => ok({ latitude: p.coords.latitude, longitude: p.coords.longitude }),
            bad, { timeout: 6000 }
          )
        );
      } catch { /* no location available */ }

      try {
        const r = await API.post('sos', {
          alert_type: btn.value,
          description: `SOS from app: ${btn.value}`,
          ...position
        });
        if (sosResult) sosResult.textContent = r.message || '✓ Alert sent.';
      } catch {
        if (sosResult) {
          sosResult.className = 'status error';
          sosResult.textContent = '⚠ Could not send alert. Please contact a nearby volunteer or call 155257.';
        }
      }
    });
  }
}

// Run on DOM ready — safe even if SOS elements are missing
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSOS);
} else {
  initSOS();
}

// Also expose for dynamic page loading
window.initSOS = initSOS;
