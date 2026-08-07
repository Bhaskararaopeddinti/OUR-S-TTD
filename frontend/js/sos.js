/**
 * sos.js – Emergency SOS dialog handling with geolocation.
 */
'use strict';

const sosFab    = document.getElementById('sosFab');
const sosDialog = document.getElementById('sosDialog');
const sosClose  = document.getElementById('sosClose');
const sosOptions = document.getElementById('sosOptions');
const sosResult  = document.getElementById('sosResult');

sosFab.addEventListener('click', () => sosDialog.showModal());
sosClose.addEventListener('click', () => sosDialog.close());

sosOptions.addEventListener('click', async e => {
  const btn = e.target.closest('button');
  if (!btn) return;
  sosResult.className = 'status';
  sosResult.textContent = '📡 Sending your location to support desk…';

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
    sosResult.textContent = r.message || '✓ Alert sent.';
  } catch {
    sosResult.className = 'status error';
    sosResult.textContent = '⚠ Could not send alert. Please contact a nearby volunteer or call 155257.';
  }
});
