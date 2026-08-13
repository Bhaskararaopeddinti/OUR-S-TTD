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
  transport:  renderTransport,
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
document.getElementById('themeToggle')?.addEventListener('click', () => {
  setTheme(!document.documentElement.classList.contains('dark'));
});
// Init theme
const savedTheme = localStorage.getItem('theme');
setTheme(savedTheme ? savedTheme === 'dark' : false);

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
let isResetMode   = false;

// ── Auth Tab Switching ─────────────────────────
function switchAuthTab(tab) {
  const tabPilgrim  = document.getElementById('tabPilgrim');
  const tabAdmin    = document.getElementById('tabAdmin');
  const panelPilgrim = document.getElementById('panelPilgrim');
  const panelAdmin   = document.getElementById('panelAdmin');

  if (tab === 'admin') {
    tabAdmin.classList.add('active');
    tabAdmin.setAttribute('aria-selected', 'true');
    tabPilgrim.classList.remove('active');
    tabPilgrim.setAttribute('aria-selected', 'false');
    panelAdmin.hidden = false;
    panelPilgrim.hidden = true;
  } else {
    tabPilgrim.classList.add('active');
    tabPilgrim.setAttribute('aria-selected', 'true');
    tabAdmin.classList.remove('active');
    tabAdmin.setAttribute('aria-selected', 'false');
    panelPilgrim.hidden = false;
    panelAdmin.hidden = true;
  }
}

document.getElementById('tabPilgrim')?.addEventListener('click', () => switchAuthTab('pilgrim'));
document.getElementById('tabAdmin')?.addEventListener('click',   () => switchAuthTab('admin'));


function formatAuthError(err) {
  if (!err) return 'An unexpected error occurred. Please try again.';
  if (typeof err === 'string') return err;
  
  if (err instanceof TypeError || (err.message && err.message.includes('Failed to fetch'))) {
    return 'Server unavailable. Please check if backend is running.';
  }

  const detail = err.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(item => item.msg || JSON.stringify(item)).join('; ');
  }
  if (err.message) return err.message;
  return 'Authentication failed. Please check your inputs.';
}

function resetAuthModalView() {
  isRegistering = false;
  isResetMode = false;
  if (nameLabel) nameLabel.hidden = true;
  const emailLabel = document.getElementById('emailLabel');
  const passwordLabel = document.getElementById('passwordLabel');
  const resetFields = document.getElementById('resetFields');
  const forgotPwdWrapper = document.getElementById('forgotPwdWrapper');
  const submitBtn = document.getElementById('authSubmit');

  if (emailLabel) emailLabel.hidden = false;
  if (passwordLabel) passwordLabel.hidden = false;
  if (resetFields) resetFields.hidden = true;
  if (forgotPwdWrapper) forgotPwdWrapper.hidden = false;
  if (submitBtn) {
    submitBtn.hidden = false;
    submitBtn.disabled = false;
    submitBtn.textContent = 'Login as Pilgrim';
  }
  if (authTitle) authTitle.textContent = 'Login to Your Journey';
  if (authSwitch) {
    authSwitch.hidden = false;
    authSwitch.textContent = 'New pilgrim? Create an account';
  }
  if (authStatus) {
    authStatus.className = 'status';
    authStatus.textContent = '';
  }
}

authBtn?.addEventListener('click', () => {
  if (authToken) { 
    logout(); 
    return; 
  }
  // Show login dialog for guests
  resetAuthModalView();
  if (authDialog) {
    authDialog.showModal();
  }
});
document.getElementById('authClose')?.addEventListener('click', () => authDialog?.close());

authSwitch?.addEventListener('click', () => {
  isRegistering = !isRegistering;
  if (nameLabel) nameLabel.hidden = !isRegistering;
  if (authTitle) authTitle.textContent = isRegistering ? 'Create Your Account' : 'Login to Your Journey';
  const submitBtn = document.getElementById('authSubmit');
  if (submitBtn) submitBtn.textContent = isRegistering ? 'Create Account' : 'Login';
  if (authSwitch) authSwitch.textContent = isRegistering ? 'Already registered? Login' : 'New pilgrim? Create an account';
  if (authStatus) {
    authStatus.className = 'status';
    authStatus.textContent = '';
  }
});

document.getElementById('forgotPasswordBtn')?.addEventListener('click', async () => {
  const emailInput = document.getElementById('authEmail');
  const email = emailInput ? emailInput.value.trim() : '';
  if (!email) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = 'Please enter your email address above to reset password.';
    }
    return;
  }
  if (authStatus) {
    authStatus.className = 'status';
    authStatus.textContent = '⏳ Requesting password reset...';
  }
  try {
    const res = await API.publicPost('auth/forgot-password', { email });
    if (authStatus) {
      authStatus.className = 'status success';
      authStatus.textContent = res.message || 'Password reset instructions sent!';
    }
    const resetFields = document.getElementById('resetFields');
    if (resetFields) {
      resetFields.hidden = false;
      if (res.dev_reset_token) {
        const tokenInput = document.getElementById('resetToken');
        if (tokenInput) tokenInput.value = res.dev_reset_token;
      }
    }
  } catch (err) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = formatAuthError(err);
    }
  }
});

document.getElementById('submitResetBtn')?.addEventListener('click', async () => {
  const token = document.getElementById('resetToken')?.value.trim();
  const newPassword = document.getElementById('newPassword')?.value;
  const confirmPassword = document.getElementById('confirmPassword')?.value;

  if (!token) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = 'Please enter the reset token.';
    }
    return;
  }
  if (!newPassword || newPassword.length < 8) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = 'New password must be at least 8 characters long.';
    }
    return;
  }
  if (newPassword !== confirmPassword) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = 'New password and confirmation password do not match.';
    }
    return;
  }

  if (authStatus) {
    authStatus.className = 'status';
    authStatus.textContent = '⏳ Updating password...';
  }

  try {
    const res = await API.publicPost('auth/reset-password', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword
    });
    if (authStatus) {
      authStatus.className = 'status success';
      authStatus.textContent = res.message || 'Password reset successfully! You can now log in.';
    }
    setTimeout(() => {
      resetAuthModalView();
    }, 1800);
  } catch (err) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = formatAuthError(err);
    }
  }
});

authForm?.addEventListener('submit', async e => {
  e.preventDefault();
  if (authStatus) {
    authStatus.className = 'status';
    authStatus.textContent = '';
  }

  const emailVal = document.getElementById('authEmail')?.value.trim();
  const passwordVal = document.getElementById('authPassword')?.value;

  if (!emailVal) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = 'Please enter your email address.';
    }
    return;
  }
  if (!passwordVal) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = 'Please enter your password.';
    }
    return;
  }

  const submit = document.getElementById('authSubmit');
  if (submit) {
    submit.disabled = true;
    submit.innerHTML = '<span class="spinner"></span> Please wait…';
  }

  try {
    const body = { email: emailVal, password: passwordVal };
    if (isRegistering) {
      const nameVal = document.getElementById('authName')?.value.trim();
      if (!nameVal) {
        throw { detail: 'Please enter your full name.' };
      }
      body.name = nameVal;
    }
    const endpoint = isRegistering ? 'auth/register' : 'auth/login';
    const data = await API.publicPost(endpoint, body);
    authToken = data.access_token;
    localStorage.setItem('authToken', authToken);
    if (authStatus) {
      authStatus.className = 'status success';
      authStatus.textContent = '✓ Signed in! Welcome.';
    }
    if (submit) submit.textContent = 'Done';
    setTimeout(async () => {
      if (authDialog) authDialog.close();
      await onAuthSuccess(true);
    }, 500);
  } catch (err) {
    if (authStatus) {
      authStatus.className = 'status error';
      authStatus.textContent = formatAuthError(err);
    }
    if (submit) {
      submit.disabled = false;
      submit.textContent = isRegistering ? 'Create Account' : 'Login';
    }
  }
});

async function onAuthSuccess(redirect = false) {
  const authBtn = document.getElementById('authBtn');

  if (!authToken) {
    logout();
    return;
  }

  try {
    const profile = await API.authGet('profile');
    authUser = profile;

    const userName = document.querySelector('.user-name');
    const userRole = document.querySelector('.user-role');
    if (userName) userName.textContent = profile.name || 'Pilgrim';
    if (userRole) userRole.textContent = profile.role || 'Pilgrim';

    const adminNavItem = document.querySelector('.admin-only-item');
    if (adminNavItem) {
      if (profile.role === 'admin' || profile.role === 'super_admin') {
        adminNavItem.style.display = 'flex';
      } else {
        adminNavItem.style.display = 'none';
      }
    }

    if (authBtn) {
      authBtn.textContent = 'Logout';
      authBtn.classList.add('logged-in');
    }

    if (redirect) {
      navigate(['admin', 'super_admin'].includes(profile.role) ? 'admin' : 'dashboard');
    } else if (currentPage === 'admin') {
      renderAdmin();
    }
    return profile;
  } catch (err) {
    console.warn('Auth token verification failed:', err);
    logout();
  }
}

function logout() {
  authToken = null;
  authUser  = null;

  // Notify backend to record OUT time (fire-and-forget)
  try {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      fetch('/api/admin/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${storedToken}`, 'Content-Type': 'application/json' }
      }).catch(() => {}); // silently ignore if not admin
    }
  } catch (_) {}

  localStorage.removeItem('authToken');
  localStorage.removeItem('adminSessionId');

  const authBtn = document.getElementById('authBtn');
  if (authBtn) {
    authBtn.textContent = 'Login';
    authBtn.classList.remove('logged-in');
  }

  const adminNavItem = document.querySelector('.admin-only-item');
  if (adminNavItem) adminNavItem.style.display = 'none';

  const userName = document.querySelector('.user-name');
  const userRole = document.querySelector('.user-role');
  if (userName) userName.textContent = 'Pilgrim';
  if (userRole) userRole.textContent = 'Guest';

  navigate('home');

  // Don't automatically show auth dialog on logout - let user choose when to login
  if (authDialog && typeof authDialog.close === 'function') {
    authDialog.close();
  }
  resetAuthModalView();
  switchAuthTab('pilgrim');
}

// ── Admin Auth Form Submit ─────────────────────
const adminAuthForm = document.getElementById('adminAuthForm');
adminAuthForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const adminEmail    = document.getElementById('adminEmail')?.value.trim();
  const adminPassword = document.getElementById('adminPassword')?.value;
  const adminStatus   = document.getElementById('adminAuthStatus');
  const adminBtn      = document.getElementById('adminAuthSubmit');

  if (!adminEmail || !adminPassword) {
    if (adminStatus) { adminStatus.className = 'status error'; adminStatus.textContent = 'Please enter both email and password.'; }
    return;
  }

  if (adminBtn) { adminBtn.disabled = true; adminBtn.innerHTML = '<span class="spinner"></span> Verifying…'; }
  if (adminStatus) { adminStatus.className = 'status'; adminStatus.textContent = ''; }

  try {
    const data = await API.publicPost('auth/login', { email: adminEmail, password: adminPassword });

    // Verify server returned admin role — NEVER trust frontend role check alone
    if (!data.user || !['admin', 'super_admin'].includes(data.user.role)) {
      throw { detail: '403 Forbidden: This account does not have admin privileges.' };
    }

    authToken = data.access_token;
    localStorage.setItem('authToken', authToken);

    if (adminStatus) { adminStatus.className = 'status success'; adminStatus.textContent = '✓ Admin authenticated. Redirecting…'; }
    if (adminBtn) adminBtn.textContent = 'Access Granted';

    setTimeout(async () => {
      if (authDialog) authDialog.close();
      await onAuthSuccess(false);
      navigate('admin');
    }, 600);

  } catch (err) {
    if (adminStatus) { adminStatus.className = 'status error'; adminStatus.textContent = formatAuthError(err); }
    if (adminBtn) { adminBtn.disabled = false; adminBtn.textContent = '🛡️ Admin Login'; }
  }
});

// ── HOME PAGE ─────────────────────────────────
function renderHome() {
  const root = document.getElementById('appRoot');
  root.innerHTML = `
    <section class="entry-screen" aria-labelledby="entryTitle">
      <div class="entry-brand"><span class="om">ॐ</span> OURS TTD</div>
      <p class="entry-tagline">AI Smart Pilgrim Companion</p>
      <div class="entry-welcome">
        <h1 id="entryTitle">Welcome to OURS TTD</h1>
        <p>Choose how you want to continue.</p>
      </div>
      <div class="entry-options">
        <article class="entry-option pilgrim-option">
          <div class="entry-icon">👤</div>
          <h2>Pilgrim</h2>
          <p>Login as a pilgrim to access your personal dashboard and journey tools.</p>
          <button type="button" class="btn-primary entry-button" id="entryPilgrimLogin">User Login</button>
        </article>
        <article class="entry-option admin-option">
          <div class="entry-icon">🛡️</div>
          <h2>Admin</h2>
          <p>Authorized personnel can access the protected Admin Portal.</p>
          <button type="button" class="btn-primary entry-button" id="entryAdminLogin">Admin Login</button>
        </article>
      </div>
    </section>`;

  document.getElementById('entryPilgrimLogin')?.addEventListener('click', () => {
    resetAuthModalView();
    switchAuthTab('pilgrim');
    authDialog?.showModal();
  });
  document.getElementById('entryAdminLogin')?.addEventListener('click', () => {
    resetAuthModalView();
    switchAuthTab('admin');
    authDialog?.showModal();
  });
}

// ── DASHBOARD PAGE ───────────────────────────
function renderDashboard() {
  console.log('Rendering dashboard page...');
  fetch('pages/dashboard.html')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.text();
    })
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      console.log('Dashboard HTML loaded');
      
      // Load dashboard data with a small delay to ensure DOM is ready
      setTimeout(() => {
        if (typeof window.loadDashboard === 'function') {
          console.log('Calling loadDashboard...');
          window.loadDashboard();
        } else if (typeof loadDashboard === 'function') {
          console.log('Calling loadDashboard (global)...');
          loadDashboard();
        } else {
          console.error('loadDashboard function not available');
        }
      }, 100);
    })
    .catch(error => {
      console.error('Failed to load dashboard page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load dashboard page: ' + error.message + '</p>';
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
      const root = document.getElementById('appRoot');
      root.innerHTML = html;
      // Give the DOM a tick to settle before attaching events
      setTimeout(() => {
        if (typeof initChatbot === 'function') {
          initChatbot();
        }
        // Ensure sendBtn and Enter key always work regardless of module load order
        const sendBtn  = document.getElementById('sendBtn');
        const chatInput = document.getElementById('chatInput');
        if (sendBtn && !sendBtn._bound) {
          sendBtn._bound = true;
          sendBtn.addEventListener('click', () => {
            if (typeof sendMessage === 'function') sendMessage();
          });
        }
        if (chatInput && !chatInput._bound) {
          chatInput._bound = true;
          chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (typeof sendMessage === 'function') sendMessage();
            }
          });
        }
      }, 50);
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

// ── TRAVEL & TRANSPORT PAGE ───────────────────
function renderTransport() {
  fetch('pages/transport.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initTransport === 'function') {
        initTransport();
      }
    })
    .catch(error => {
      console.error('Failed to load transport page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load transport page.</p>';
    });
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
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.text();
    })
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      console.log('Queue page HTML loaded');
      
      // Load queue intelligence data with a small delay to ensure DOM is ready
      setTimeout(() => {
        if (typeof loadQueueIntelligence === 'function') {
          console.log('Calling loadQueueIntelligence...');
          loadQueueIntelligence();
        } else {
          console.error('loadQueueIntelligence function not available');
        }
      }, 100);
    })
    .catch(error => {
      console.error('Failed to load queue page:', error);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load queue page: ' + error.message + '</p>';
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

// ── TRANSPORT PAGE ────────────────────────────
function renderTransport() {
  fetch('pages/transport.html')
    .then(res => res.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      if (typeof initTransport === 'function') {
        initTransport();
      }
    })
    .catch(err => {
      console.error('Failed to load transport page:', err);
      document.getElementById('appRoot').innerHTML = '<p class="error">Failed to load transport page.</p>';
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
  const isAdmin = authUser && (authUser.role === 'admin' || authUser.role === 'super_admin');
  fetch('pages/admin.html')
    .then(res => res.text())
    .then(html => {
      document.getElementById('appRoot').innerHTML = html;
      const notice = document.getElementById('adminAuthNotice');
      const content = document.getElementById('adminContent');
      if (!authToken || !isAdmin) {
        if (notice) {
          notice.hidden = false;
          notice.innerHTML = '⛔ <strong>403 Forbidden</strong>: Administrator credentials required. Normal users cannot access admin pages.';
        }
        if (content) content.hidden = true;
      } else {
        if (notice) notice.hidden = true;
        if (content) content.hidden = false;
        loadAdminData();
        if (typeof window.initAdminModule === 'function') {
          window.initAdminModule();
        }
        if (typeof window.loadAdminTransportRoutes === 'function') {
          window.loadAdminTransportRoutes();
        }
      }
    })
    .catch(err => {
      console.error('Failed to load admin template:', err);
    });
}

async function loadAdminData() {
  try {
    const stats = await API.authGet('admin/analytics');
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val ?? '—'; };
    setEl('aTotalPilgrims', stats.total_pilgrims);
    setEl('aAlerts',        stats.emergency_alerts_open);
    setEl('aLostFound',     stats.lost_found_open);
    setEl('aTotalChats',    stats.total_chats);
  } catch (err) {
    if (err && (err.status === 403 || err.detail?.includes('Forbidden') || err.detail?.includes('Administrator'))) {
      const notice = document.getElementById('adminAuthNotice');
      const content = document.getElementById('adminContent');
      if (notice) {
        notice.hidden = false;
        notice.innerHTML = '⛔ <strong>403 Forbidden</strong>: Backend verification failed. Administrator credentials required.';
      }
      if (content) content.hidden = true;
    }
  }

  try {
    const alerts = await API.authGet('admin/emergencies');
    const tbody = document.getElementById('alertsBody');
    if (!tbody) return;
    tbody.innerHTML = alerts.length
      ? alerts.map(a => `
          <tr>
            <td>${a.id}</td>
            <td><strong>${a.alert_type}</strong></td>
            <td><span style="color:${a.status==='open'?'var(--danger)':'var(--success)'}">${a.status}</span></td>
            <td>${new Date(a.created_at).toLocaleString()}</td>
          </tr>
        `).join('')
      : '<tr><td colspan="4">No alerts recorded.</td></tr>';
  } catch (err) {
    const tbody = document.getElementById('alertsBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="4">Could not load alerts.</td></tr>';
  }
}

// ── Expose navigate globally (used by onclick attrs) ──
window.navigate = navigate;
window.openFacilityChat = openFacilityChat;
window.openMapsDirections = openMapsDirections;
// fetchAndRenderRoutes is defined in transport.js which loads after app.js
// We expose a safe wrapper that delegates to transport.js once loaded
window.fetchAndRenderRoutes = function(fromLoc, toLoc, mode) {
  if (typeof fetchAndRenderRoutes === 'function' && window._transportReady) {
    return window._fetchAndRenderRoutesImpl(fromLoc, toLoc, mode);
  }
  // Silently wait — transport.js will override this once loaded
  console.debug('[app.js] fetchAndRenderRoutes called before transport.js ready, queuing...');
};

// ── Initial render ─────────────────────────────
// Verify a restored session with the backend before showing a dashboard.
// Guests always begin at the two-option welcome screen.
if (authToken) {
  onAuthSuccess(true);
} else {
  // Ensure guest state is properly set on page load
  const authBtn = document.getElementById('authBtn');
  if (authBtn) {
    authBtn.textContent = 'Login';
    authBtn.classList.remove('logged-in');
  }
  
  const userName = document.querySelector('.user-name');
  const userRole = document.querySelector('.user-role');
  if (userName) userName.textContent = 'Pilgrim';
  if (userRole) userRole.textContent = 'Guest';
  
  navigate('home');
}
// Load hero queue stats
loadHeroStats();

// ── Global Real-Time WebSocket Connection ─────────────────────
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host || 'localhost:8000';
  try {
    window.ws = new WebSocket(`${protocol}//${host}/ws/live`);

    window.ws.onopen = () => {
      console.log('✅ WebSocket Connected to /ws/live');
    };

    window.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('📥 Update received:', msg.type || msg);

        if (msg.type === 'facility_update') {
          const el = document.getElementById(`facility-${msg.id}`);
          if (el) {
            el.textContent = msg.status;
            el.classList.add('update-animation');
          }
          if (window.showToast) {
            window.showToast(`Facility #${msg.id} updated to ${msg.status}`, 'info');
          }
        } else if (msg.type === 'queue_update') {
          if (typeof loadQueueIntelligence === 'function') loadQueueIntelligence();
          if (typeof loadDashboardQueueIntelligence === 'function') loadDashboardQueueIntelligence();
          if (typeof loadQueueStatus === 'function') loadQueueStatus();
          if (typeof loadHeroStats === 'function') loadHeroStats();
          if (window.showToast) {
            window.showToast('📥 Live queue update received from Admin', 'info');
          }
        }
      } catch (err) {
        console.error('Error handling WebSocket message:', err);
      }
    };

    window.ws.onerror = (err) => {
      console.warn('WebSocket connection error, retrying...');
    };

    window.ws.onclose = () => {
      console.log('WebSocket connection closed, reconnecting in 5s...');
      setTimeout(initWebSocket, 5000);
    };
  } catch (e) {
    console.error('Failed to initialize WebSocket:', e);
  }
}

if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initWebSocket();
} else {
  document.addEventListener('DOMContentLoaded', initWebSocket);
}
