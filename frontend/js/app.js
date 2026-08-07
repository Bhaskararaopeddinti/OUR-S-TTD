/**
 * app.js – OURS TTD SPA Router + Auth + Theme
 * Manages page rendering, authentication state, and theme persistence.
 */

'use strict';

// ── State ─────────────────────────────────────
let currentPage = 'home';
let authToken = localStorage.getItem('authToken') || null;
let authUser  = null;  // populated after login

// ── Page Definitions ──────────────────────────
const PAGES = {
  dashboard:  renderDashboard,
  navigation: renderNavigation,
  temple:     renderTemple,
  queue:      renderQueue,
  food:       renderFood,
  medical:    renderMedical,
  emergency:  renderEmergency,
  accommodation: renderAccommodation,
  chatbot:    renderChatbot,
  settings:   renderSettings,
  home:       renderHome,
  services:   renderServices,
  booking:    renderBooking,
  health:     renderHealth,
  lostfound:  renderLostFound,
  admin:      renderAdmin,
};

// ── Router ────────────────────────────────────
function navigate(page) {
  if (!PAGES[page]) page = 'dashboard';
  currentPage = page;
  // Update nav active state for sidebar
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === page);
  });
  const root = document.getElementById('appRoot');
  root.innerHTML = '';
  root.classList.remove('fade-in');
  void root.offsetWidth; // reflow
  root.classList.add('fade-in');
  PAGES[page]();
}

// ── Theme ─────────────────────────────────────
function setTheme(dark) {
  document.documentElement.classList.toggle('dark', dark);
  localStorage.setItem('theme', dark ? 'dark' : 'light');
}
document.getElementById('themeToggle').addEventListener('click', () => {
  setTheme(!document.documentElement.classList.contains('dark'));
});
// Init theme
const savedTheme = localStorage.getItem('theme');
setTheme(savedTheme ? savedTheme === 'dark' : true);

// ── Nav click handler ─────────────────────────
const navContainer = document.querySelector('.sidebar-nav');
navContainer?.addEventListener('click', e => {
  const btn = e.target.closest('.nav-item');
  if (btn) navigate(btn.dataset.page);
});

const mobileNav = document.querySelector('.mobile-nav');
mobileNav?.addEventListener('click', e => {
  const btn = e.target.closest('.mobile-nav-item');
  if (btn) navigate(btn.dataset.page);
});

// ── Auth ──────────────────────────────────────
const authBtn    = document.getElementById('authBtn');
const authDialog = document.getElementById('authDialog');
const authForm   = document.getElementById('authForm');
const authStatus = document.getElementById('authStatus');
const authSwitch = document.getElementById('authSwitch');
const authTitle  = document.getElementById('authTitle');
const authName   = document.getElementById('authName');
const nameLabel  = document.getElementById('nameLabel');
let isRegistering = false;

authBtn.addEventListener('click', () => {
  if (authToken) { logout(); return; }
  authDialog.showModal();
});
document.getElementById('authClose').addEventListener('click', () => authDialog.close());

authSwitch.addEventListener('click', () => {
  isRegistering = !isRegistering;
  nameLabel.hidden = !isRegistering;
  authTitle.textContent = isRegistering ? 'Create Your Account' : 'Login to Your Journey';
  document.getElementById('authSubmit').textContent = isRegistering ? 'Create Account' : 'Login';
  authSwitch.textContent = isRegistering ? 'Already registered? Login' : 'New pilgrim? Create an account';
  authStatus.textContent = '';
});

authForm.addEventListener('submit', async e => {
  e.preventDefault();
  authStatus.textContent = '';
  const submit = document.getElementById('authSubmit');
  submit.disabled = true;
  submit.innerHTML = '<span class="spinner"></span> Please wait…';

  try {
    const body = { email: document.getElementById('authEmail').value, password: document.getElementById('authPassword').value };
    if (isRegistering) body.name = document.getElementById('authName').value;
    const endpoint = isRegistering ? 'auth/register' : 'auth/login';
    const data = await API.post(endpoint, body);
    authToken = data.access_token;
    localStorage.setItem('authToken', authToken);
    authStatus.textContent = '✓ Signed in! Welcome.';
    submit.textContent = 'Done';
    setTimeout(() => {
      authDialog.close();
      onAuthSuccess();
    }, 700);
  } catch (err) {
    authStatus.className = 'status error';
    authStatus.textContent = err.detail || 'Sign in failed. Please check your details.';
    submit.disabled = false;
    submit.textContent = isRegistering ? 'Create Account' : 'Login';
  }
});

function onAuthSuccess() {
  authBtn.textContent = '✓ Signed In';
  // Show admin link if admin
  API.get('profile').then(profile => {
    authUser = profile;
    if (profile.role === 'admin') {
      document.getElementById('adminLink').hidden = false;
    }
  }).catch(() => {});
}

function logout() {
  authToken = null;
  authUser  = null;
  localStorage.removeItem('authToken');
  authBtn.textContent = 'Login';
  document.getElementById('adminLink').hidden = true;
  navigate('home');
}

// Check if already logged in on page load
if (authToken) onAuthSuccess();

// ── HOME PAGE ─────────────────────────────────
function renderHome() {
  navigate('dashboard');
}

// ── DASHBOARD PAGE ───────────────────────────
function renderDashboard() {
  fetch('pages/dashboard.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof loadDashboard === 'function') {
        loadDashboard();
      }
    })
    .catch(error => {
      console.error('Failed to load dashboard page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load dashboard page.</p>';
    });
}

// ── TEMPLE GUIDE PAGE ─────────────────────────
function renderTemple() {
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <h2>🛕 Temple Guide</h2>
      <div class="dashboard-card">
        <h3>Sri Venkateswara Temple</h3>
        <p>Main entrance to Sri Venkateswara Swamy Temple</p>
        <button class="quick-action-btn" onclick="navigate('navigation')">Navigate</button>
      </div>
    </section>
  `;
}

// ── FOOD FINDER PAGE ───────────────────────────
function renderFood() {
  fetch('pages/food.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initFood === 'function') {
        initFood();
      }
    })
    .catch(error => {
      console.error('Failed to load food page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load food page.</p>';
    });
}

// ── MEDICAL ASSISTANCE PAGE ───────────────────
function renderMedical() {
  fetch('pages/medical.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initMedical === 'function') {
        initMedical();
      }
    })
    .catch(error => {
      console.error('Failed to load medical page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load medical page.</p>';
    });
}

// ── EMERGENCY SOS PAGE ────────────────────────
function renderEmergency() {
  fetch('pages/emergency.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initEmergency === 'function') {
        initEmergency();
      }
    })
    .catch(error => {
      console.error('Failed to load emergency page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load emergency page.</p>';
    });
}

// ── ACCOMMODATION PAGE ────────────────────────
function renderAccommodation() {
  fetch('pages/accommodation.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initAccommodation === 'function') {
        initAccommodation();
      }
    })
    .catch(error => {
      console.error('Failed to load accommodation page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load accommodation page.</p>';
    });
}

// ── CHATBOT PAGE ─────────────────────────────
function renderChatbot() {
  fetch('pages/chatbot.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initChatbot === 'function') {
        initChatbot();
      }
    })
    .catch(error => {
      console.error('Failed to load chatbot page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load chatbot page.</p>';
    });
}

// ── SETTINGS PAGE ─────────────────────────────
function renderSettings() {
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <h2>⚙️ Settings</h2>
      <div class="dashboard-card">
        <h3>Language</h3>
        <select class="lang-select">
          <option>English</option>
          <option>Telugu</option>
          <option>Hindi</option>
          <option>Tamil</option>
        </select>
      </div>
      <div class="dashboard-card">
        <h3>Theme</h3>
        <button class="quick-action-btn" onclick="document.getElementById('themeToggle').click()">Toggle Theme</button>
      </div>
    </section>
  `;
}

// ── Original Home Page (for reference) ───────────
function renderOriginalHome() {
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <div class="notice" style="margin-bottom:1.5rem;">
        ℹ️ This is a <strong>project demonstration</strong>. All booking and queue data require official TTD integration.
      </div>

      <h2 data-translate>Quick Services</h2>
      <div class="quick-grid">
        ${[
          ['🛕','Live Queue','Check crowd & wait time','queue'],
          ['🗺️','Smart Navigation','Find facilities on map','navigation'],
          ['📋','Book Darshan','Darshan & accommodation','booking'],
          ['💬','AI Assistant','Ask anything','_chat'],
          ['💊','Health & Wellness','Reminders & assistance','health'],
          ['🔍','Lost & Found','Report or search','lostfound'],
          ['📦','Luggage Help','Cloak room locations','services'],
          ['🍛','Annaprasadam','Free food locations','services'],
        ].map(([icon,title,sub,page]) => `
          <div class="quick-card" onclick="${page === '_chat' ? 'document.getElementById(\'chatFab\').click()' : `navigate('${page}')`}" tabindex="0" role="button" aria-label="${title}">
            <div class="icon">${icon}</div>
            <h3>${title}</h3>
            <p>${sub}</p>
          </div>
        `).join('')}
      </div>

      <h2 style="margin-top:2rem;" data-translate>First-Time Pilgrim Guide</h2>
      <div class="journey-steps card">
        ${[
          ['🚌','Arrival'],['🅿️','Parking'],['🏨','Stay'],
          ['👜','Luggage'],['📵','Phone'],['🎟️','Ticket'],
          ['⏳','Queue'],['🛕','Darshan'],['🍬','Laddu'],['🙏','Blessings'],
        ].map(([icon,lbl]) => `
          <div class="step"><div class="step-icon">${icon}</div><div class="step-lbl">${lbl}</div></div>
        `).join('')}
      </div>

      <h2 style="margin-top:2rem;" data-translate>Facilities Directory</h2>
      <div class="facility-grid" id="facilitiesGrid"></div>
    </section>
  `;
  loadFacilitiesGrid();
  // Hero stats
  loadHeroStats();
}

async function loadHeroStats() {
  try {
    const q = await API.get('queue');
    const heroQueue = document.getElementById('heroQueue');
    const heroCrowd = document.getElementById('heroCrowd');
    if (heroQueue) heroQueue.textContent = q.wait_minutes ? `~${Math.round(q.wait_minutes/60)}h` : '—';
    if (heroCrowd) heroCrowd.textContent = q.crowd_density || 'Unknown';
  } catch (e) { /* silently fail */ }
}

async function loadFacilitiesGrid() {
  const grid = document.getElementById('facilitiesGrid');
  if (!grid) return;
  try {
    const data = await API.get('facilities');
    const facilities = data.facilities || [];
    const icons = { restroom:'🚻', food:'🍛', medical:'🏥', laddu:'🍬', phone:'📵', wheelchair:'♿', water:'💧', navigation:'🗺️' };
    grid.innerHTML = facilities.map(f => `
      <div class="facility-card" onclick="openFacilityChat('${f.name}')" tabindex="0" role="button">
        <div class="fc-icon">${icons[f.kind] || '📍'}</div>
        <h4>${f.name}</h4>
        <p>${f.locations || ''}</p>
      </div>
    `).join('') || '<p>Loading facilities…</p>';
  } catch (e) {
    if (grid) grid.innerHTML = '<p>Facilities info temporarily unavailable.</p>';
  }
}

function openFacilityChat(name) {
  document.getElementById('chatFab').click();
  const input = document.getElementById('chatInput');
  if (input) { input.value = `Where is the nearest ${name}?`; input.focus(); }
}

// ── QUEUE PAGE ────────────────────────────────
function renderQueue() {
  // Load the queue.html page template
  fetch('pages/queue.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      // Load queue intelligence data
      if (typeof loadQueueIntelligence === 'function') {
        loadQueueIntelligence();
      }
    })
    .catch(error => {
      console.error('Failed to load queue page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load queue page.</p>';
    });
}

async function loadQueueData() {
  const advice = document.getElementById('qAdvice');
  if (advice) advice.textContent = 'Fetching official status…';
  try {
    const q = await API.get('queue');
    const crowd = document.getElementById('qCrowd');
    const wait  = document.getElementById('qWait');
    const people = document.getElementById('qPeople');
    const slot  = document.getElementById('qSlot');
    const prog  = document.getElementById('qProgress');
    if (crowd)  crowd.textContent  = q.crowd_density || 'Not published';
    if (wait)   wait.textContent   = q.wait_minutes ? `${Math.floor(q.wait_minutes/60)}h ${q.wait_minutes%60}m` : '—';
    if (people) people.textContent = q.balance_tickets ? q.balance_tickets.count.toLocaleString() : '—';
    if (slot)   slot.textContent   = q.slot || '—';
    if (prog)   prog.style.width   = q.wait_minutes ? `${Math.min((q.wait_minutes/240)*100, 100)}%` : '0%';
    if (advice) advice.textContent = q.slot
      ? `Official TTD update — Running Slot: ${q.slot}. Source: tirumala.org`
      : (q.message || 'Queue wait time is not publicly published by TTD. Please visit tirumala.org for updates.');
  } catch {
    const advice = document.getElementById('qAdvice');
    if (advice) advice.textContent = 'Unable to reach official TTD status. Please visit tirumala.org directly.';
  }
}

// ── SERVICES PAGE ─────────────────────────────
function renderServices() {
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <h2 data-translate>Pilgrim Services</h2>
      <p data-translate>Tap any service to get directions or information from the AI assistant.</p>

      <div class="facility-grid" id="servicesGrid"></div>

      <div class="card" style="margin-top:1.5rem;">
        <h3>📍 Pilgrimage Checklist</h3>
        <ul>
          <li>✅ Valid Government ID (Aadhaar, Passport, etc.)</li>
          <li>✅ Darshan ticket (SSD) or free queue registration</li>
          <li>✅ Mobile phone deposited before temple entry</li>
          <li>✅ Traditional modest attire</li>
          <li>✅ Water bottle &amp; snacks for queue wait</li>
          <li>✅ Small bag (large luggage to be deposited at cloak room)</li>
          <li>✅ Emergency contacts saved offline</li>
          <li>✅ TTD Helpline number: <strong>155257</strong></li>
        </ul>
      </div>
    </section>
  `;
  const grid = document.getElementById('servicesGrid');
  const services = [
    ['🚻','Restrooms','Available at PAC I–V, VQC I &amp; II'],
    ['💧','Drinking Water','Free purified water throughout Tirumala'],
    ['🏥','Medical Aid','Aswini Hospital &amp; aid stations 24/7'],
    ['🍛','Annaprasadam','Free meals at MTVAC, PAC II &amp; VQC'],
    ['🍬','Laddu Counter','West/East Mada Street, VQC exit'],
    ['📵','Phone Deposit','VQC I &amp; II, PAC-3, PAC-5'],
    ['♿','Wheelchair Help','Medical centres &amp; help desks'],
    ['🅿️','Parking','Alipiri &amp; Tirumala parking areas'],
    ['🚌','Bus Stand','Rambagicha Bus Stand for services'],
    ['👜','Cloak Room','Luggage deposit near VQC &amp; bus stand'],
    ['✂️','Tonsure','Kalyanakatta complex, free of charge'],
    ['🔍','Lost &amp; Found','Report via Lost &amp; Found section'],
  ];
  if (grid) {
    grid.innerHTML = services.map(([icon,title,sub]) => `
      <div class="facility-card" tabindex="0" role="button" onclick="openFacilityChat('${title}')" aria-label="${title}">
        <div class="fc-icon">${icon}</div>
        <h4>${title}</h4>
        <p>${sub}</p>
      </div>
    `).join('');
  }
}

// ── BOOKING PAGE ──────────────────────────────
function renderBooking() {
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <h2>📋 Darshan &amp; Booking</h2>
      <div class="notice">
        ⚠️ <strong>Official TTD API integration pending.</strong> Creating a booking here will store a placeholder request — actual booking must be done at
        <a href="https://ttdevasthanams.ap.gov.in" target="_blank" rel="noopener">ttdevasthanams.ap.gov.in</a>.
      </div>

      ${authToken ? `
        <div class="card">
          <h3>Create a Booking Request</h3>
          <form id="bookingForm">
            <label><span>Booking Type</span>
              <select name="booking_type">
                <option value="darshan">Darshan</option>
                <option value="accommodation">Accommodation</option>
                <option value="seva">Seva</option>
              </select>
            </label>
            <label><span>Preferred Date</span>
              <input type="date" name="date" required min="${new Date().toISOString().slice(0,10)}" />
            </label>
            <label><span>Slot Preference</span>
              <input type="text" name="slot" placeholder="e.g., Morning, Afternoon" />
            </label>
            <label><span>Additional Notes</span>
              <textarea name="notes" rows="2" placeholder="Any special requirements…"></textarea>
            </label>
            <button type="submit" class="btn-primary">Submit Request</button>
            <p id="bookResult" class="status" role="status"></p>
          </form>
        </div>
        <div class="card">
          <h3>My Booking Requests</h3>
          <ul id="bookList"><li>Loading…</li></ul>
        </div>
      ` : `
        <div class="card" style="text-align:center;padding:2.5rem;">
          <p style="font-size:1.1rem;margin-bottom:1rem;">Sign in to manage your booking requests.</p>
          <button class="btn-primary" onclick="document.getElementById('authBtn').click()">Login / Register</button>
        </div>
      `}

      <div class="card">
        <h3>Official Booking Links</h3>
        <ul>
          <li>🎟️ <a href="https://ttdevasthanams.ap.gov.in/index.php/home/darshanam" target="_blank">SSD Ticket Booking (Official TTD)</a></li>
          <li>🏨 <a href="https://ttdevasthanams.ap.gov.in/index.php/home/accommodation" target="_blank">Accommodation (Official TTD)</a></li>
          <li>🙏 <a href="https://ttdevasthanams.ap.gov.in/index.php/home/sevas" target="_blank">Seva Registration (Official TTD)</a></li>
        </ul>
      </div>
    </section>
  `;
  if (authToken) {
    setupBookingForm();
    loadUserBookings();
  }
}

function setupBookingForm() {
  const form = document.getElementById('bookingForm');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const resultEl = document.getElementById('bookResult');
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    try {
      const r = await API.authPost('bookings', body);
      resultEl.className = 'status';
      resultEl.textContent = '✓ Request saved. ' + (r.message || '');
      loadUserBookings();
    } catch (err) {
      resultEl.className = 'status error';
      resultEl.textContent = err.detail || 'Unable to save booking. Please try again.';
    }
  });
}

async function loadUserBookings() {
  const list = document.getElementById('bookList');
  if (!list) return;
  try {
    const items = await API.authGet('bookings');
    if (!items.length) { list.innerHTML = '<li>No booking requests yet.</li>'; return; }
    list.innerHTML = items.map(b => `
      <li>
        <strong>${b.booking_type}</strong> — ${b.date}
        <span style="float:right;font-size:.8rem;color:var(--muted);">${b.status}</span>
        <br/><small style="color:var(--muted);">${b.notes}</small>
      </li>
    `).join('');
  } catch { list.innerHTML = '<li>Could not load bookings.</li>'; }
}

// ── NAVIGATION PAGE ───────────────────────────
function renderNavigation() {
  // Load the navigation.html page template
  fetch('pages/navigation.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      // Navigation functionality is handled by navigation.js
      if (typeof initNavigation === 'function') {
        initNavigation();
      }
    })
    .catch(error => {
      console.error('Failed to load navigation page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load navigation page.</p>';
    });
}

function renderLandmarks() {
  const grid = document.getElementById('landmarkGrid');
  if (!grid) return;
  const lms = [
    ['🛕','Srivari Temple','Main darshan complex',13.6839,79.3476],
    ['🚻','Restrooms','PAC I–V, VQC I &amp; II',13.6839,79.3476],
    ['🍛','Annaprasadam','MTVAC &amp; PAC complexes',13.6842,79.3481],
    ['🏥','Medical / Hospital','Aswini Hospital',13.6825,79.3450],
    ['🍬','Laddu Complex','West/East Mada Street',13.6850,79.3490],
    ['📵','Phone Deposit','VQC I &amp; II lines',13.6845,79.3470],
    ['♿','Wheelchair Help','Medical &amp; help desks',13.6830,79.3465],
    ['🅿️','Parking','Alipiri &amp; Tirumala',13.6800,79.3410],
    ['🚌','Bus Stand','Rambagicha Bus Stand',13.6810,79.3430],
    ['👜','Cloak Room','Near VQC &amp; bus stand',13.6835,79.3470],
    ['🏨','Accommodation','PAC 1–5 complexes',13.6820,79.3460],
    ['✂️','Tonsure (Kalyanakatta)','Kalyanakatta complex',13.6855,79.3500],
  ];
  grid.innerHTML = lms.map(([icon,name,loc,lat,lng]) => `
    <div class="facility-card" tabindex="0" role="button"
      onclick="openMapsDirections(${lat}, ${lng}, '${name.replace(/'/g,'')}')"
      aria-label="Navigate to ${name}">
      <div class="fc-icon">${icon}</div>
      <h4>${name}</h4>
      <p>${loc}</p>
      <small style="color:var(--saffron);">📍 Open in Maps</small>
    </div>
  `).join('');
}

function openMapsDirections(lat, lng, name) {
  const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(name)}`;
  window.open(url, '_blank', 'noopener');
}

// ── HEALTH PAGE ───────────────────────────────
function renderHealth() {
  // Load the health.html page template
  fetch('pages/health.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      // Health functionality is handled by health.js
    })
    .catch(error => {
      console.error('Failed to load health page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load health page.</p>';
    });
}

async function loadHealthCard() {
  try {
    const p = await API.authGet('profile');
    const el = document.getElementById('healthCard');
    if (!el) return;
    document.getElementById('hcName').textContent = `👤 ${p.name}`;
    document.getElementById('hcBlood').textContent = p.blood_group ? `🩸 Blood Group: ${p.blood_group}` : '';
    document.getElementById('hcCond').textContent  = p.medical_conditions ? `⚕️ ${p.medical_conditions}` : '';
    document.getElementById('hcEmergency').textContent = p.emergency_contact ? `📞 Emergency: ${p.emergency_contact}` : '';
  } catch { /* silent */ }
}

async function loadReminders() {
  const list = document.getElementById('reminderList');
  if (!list) return;
  try {
    const items = await API.authGet('health/reminders');
    list.innerHTML = items.length
      ? items.map(r => `<li>⏰ ${r.reminder_type} — every ${r.interval_minutes} min ${r.message ? '· ' + r.message : ''}</li>`).join('')
      : '<li>No active reminders.</li>';
  } catch { list.innerHTML = '<li>Could not load reminders.</li>'; }
}

function setupReminderForm() {
  const form = document.getElementById('reminderForm');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const status = document.getElementById('reminderStatus');
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    body.interval_minutes = parseInt(body.interval_minutes);
    try {
      await API.authPost('health/reminders', body);
      status.className = 'status';
      status.textContent = '✓ Reminder set!';
      loadReminders();
    } catch (err) {
      status.className = 'status error';
      status.textContent = err.detail || 'Failed to set reminder.';
    }
  });
}

async function triggerSOS(type) {
  const status = document.getElementById('assistStatus');
  if (status) status.textContent = 'Sending request…';
  try {
    const r = await API.post('sos', { alert_type: type });
    if (status) { status.className = 'status'; status.textContent = r.message; }
  } catch {
    if (status) { status.className = 'status error'; status.textContent = 'Could not send. Please contact a volunteer directly.'; }
  }
}

// ── LOST & FOUND PAGE ─────────────────────────
function renderLostFound() {
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <h2>🔍 Lost &amp; Found</h2>

      <div class="tab-bar">
        <button class="tab-btn active" id="tabReport" onclick="lfSwitch('report')">📝 File Report</button>
        <button class="tab-btn" id="tabSearch" onclick="lfSwitch('search')">🔎 Search</button>
      </div>

      <div id="lfReport" class="card">
        <h3>File a Lost / Found Report</h3>
        <form id="lfForm">
          <label><span>Report Type</span>
            <select name="report_type" required>
              <option value="lost_item">Lost Item</option>
              <option value="found_item">Found Item</option>
              <option value="lost_person">Lost Person</option>
              <option value="found_person">Found Person</option>
            </select>
          </label>
          <label><span>Category</span>
            <select name="category" required>
              <option value="child">Child</option>
              <option value="elderly">Elderly</option>
              <option value="bag">Bag / Luggage</option>
              <option value="phone">Mobile Phone</option>
              <option value="jewellery">Jewellery</option>
              <option value="documents">Documents / ID</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label><span>Description</span>
            <textarea name="description" required rows="3" minlength="5" placeholder="Describe clearly…"></textarea>
          </label>
          <label><span>Last Seen Location</span>
            <input type="text" name="location" placeholder="e.g., VQC II, gate 3" />
          </label>
          <label><span>Your Contact Info</span>
            <input type="text" name="contact_info" placeholder="Phone or name" />
          </label>
          <button type="submit" class="btn-primary">Submit Report</button>
          <p id="lfStatus" class="status" role="status"></p>
        </form>
      </div>

      <div id="lfSearch" class="card" hidden>
        <h3>Search Open Reports</h3>
        <div class="filter-row">
          <select id="lfTypeFilter">
            <option value="">All Types</option>
            <option value="lost_item">Lost Items</option>
            <option value="found_item">Found Items</option>
            <option value="lost_person">Lost Persons</option>
            <option value="found_person">Found Persons</option>
          </select>
          <button class="btn-primary" id="lfSearchBtn">Search</button>
        </div>
        <ul id="lfResults"><li>Click Search to view open reports.</li></ul>
      </div>
    </section>
  `;
  setupLostFoundForm();
  document.getElementById('lfSearchBtn')?.addEventListener('click', searchLostFound);
}

window.lfSwitch = function(tab) {
  document.getElementById('lfReport').hidden = (tab !== 'report');
  document.getElementById('lfSearch').hidden = (tab !== 'search');
  document.getElementById('tabReport').classList.toggle('active', tab === 'report');
  document.getElementById('tabSearch').classList.toggle('active', tab === 'search');
};

function setupLostFoundForm() {
  const form = document.getElementById('lfForm');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const status = document.getElementById('lfStatus');
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    try {
      const r = await API.post('lostfound', body);
      status.className = 'status';
      status.textContent = '✓ ' + (r.message || 'Report filed successfully.');
      form.reset();
    } catch (err) {
      status.className = 'status error';
      status.textContent = err.detail || 'Could not file report. Please try again.';
    }
  });
}

async function searchLostFound() {
  const list = document.getElementById('lfResults');
  const type = document.getElementById('lfTypeFilter')?.value || '';
  list.innerHTML = '<li>Searching…</li>';
  try {
    let url = 'lostfound';
    if (type) url += `?report_type=${type}`;
    const items = await API.get(url);
    if (!items.length) { list.innerHTML = '<li>No open reports found.</li>'; return; }
    list.innerHTML = items.map(r => `
      <li>
        <strong>[${r.report_type.replace('_',' ')}]</strong> ${r.category} — ${r.description.slice(0,100)}${r.description.length>100?'…':''}
        <br/><small style="color:var(--muted);">📍 ${r.location || 'Location not specified'} · ${r.contact_info || 'No contact'}</small>
      </li>
    `).join('');
  } catch { list.innerHTML = '<li>Could not load reports. Try again.</li>'; }
}

// ── ADMIN PAGE ────────────────────────────────
function renderAdmin() {
  const isAdmin = authUser && authUser.role === 'admin';
  document.getElementById('appRoot').innerHTML = `
    <section class="fade-in">
      <h2>🛡️ Admin Dashboard</h2>
      ${!authToken ? `
        <div class="card" style="text-align:center;padding:2.5rem;">
          <p>Admin login required.</p>
          <button class="btn-primary" onclick="document.getElementById('authBtn').click()">Login</button>
        </div>
      ` : !isAdmin ? `
        <div class="notice">⛔ Admin access required. Sign in with an admin account.</div>
      ` : `
        <div class="analytics-grid">
          <div class="stat-card accent"><span class="big" id="aTotalPilgrims">—</span><span>Total Pilgrims</span></div>
          <div class="stat-card accent"><span class="big" id="aAlerts">—</span><span>Open Alerts</span></div>
          <div class="stat-card accent"><span class="big" id="aLostFound">—</span><span>Lost &amp; Found</span></div>
          <div class="stat-card accent"><span class="big" id="aTotalChats">—</span><span>AI Chats</span></div>
          <div class="stat-card accent"><span class="big" id="aBookings">—</span><span>Bookings</span></div>
          <div class="stat-card accent"><span class="big" id="aFeedback">—</span><span>Feedback</span></div>
        </div>

        <div class="card">
          <h3>🚨 Recent Emergency Alerts</h3>
          <div style="overflow-x:auto;">
            <table>
              <thead><tr><th>#</th><th>Type</th><th>Description</th><th>Status</th><th>Time</th></tr></thead>
              <tbody id="alertsBody"><tr><td colspan="5">Loading…</td></tr></tbody>
            </table>
          </div>
        </div>
      `}
    </section>
  `;
  if (authToken && isAdmin) loadAdminData();
}

async function loadAdminData() {
  try {
    const stats = await API.authGet('admin/analytics');
    document.getElementById('aTotalPilgrims').textContent = stats.total_pilgrims;
    document.getElementById('aAlerts').textContent        = stats.emergency_alerts_open;
    document.getElementById('aLostFound').textContent     = stats.lost_found_open;
    document.getElementById('aTotalChats').textContent    = stats.total_chats;
    document.getElementById('aBookings').textContent      = stats.total_bookings;
    document.getElementById('aFeedback').textContent      = stats.total_feedback;

    const alerts = await API.authGet('admin/emergencies');
    const tbody = document.getElementById('alertsBody');
    tbody.innerHTML = alerts.length
      ? alerts.map(a => `
          <tr>
            <td>${a.id}</td>
            <td><strong>${a.alert_type}</strong></td>
            <td>${a.description || '—'}</td>
            <td><span style="color:${a.status==='open'?'var(--danger)':'var(--success)'};">${a.status}</span></td>
            <td>${new Date(a.created_at).toLocaleString()}</td>
          </tr>
        `).join('')
      : '<tr><td colspan="5">No alerts recorded.</td></tr>';
  } catch (err) {
    const tbody = document.getElementById('alertsBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="5">Could not load data.</td></tr>';
  }
}

// ── Expose navigate globally (used by onclick attrs) ──
window.navigate = navigate;
window.openFacilityChat = openFacilityChat;
window.openMapsDirections = openMapsDirections;

// ── Initial render ─────────────────────────────
navigate('home');
// Load hero queue stats
loadHeroStats();
