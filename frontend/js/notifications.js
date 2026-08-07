/**
 * notifications.js – Notification bell panel toggle and unread badge.
 */
'use strict';

const notifToggle = document.getElementById('notifToggle');
const notifPanel  = document.getElementById('notifPanel');
const notifClose  = document.getElementById('notifClose');
const notifBadge  = document.getElementById('notifBadge');

// Toggle panel
notifToggle?.addEventListener('click', e => {
  e.stopPropagation();
  notifPanel.hidden = !notifPanel.hidden;
});
notifClose?.addEventListener('click', () => { notifPanel.hidden = true; });

// Close on outside click
document.addEventListener('click', e => {
  if (!notifPanel.hidden && !notifPanel.contains(e.target) && e.target !== notifToggle) {
    notifPanel.hidden = true;
  }
});

// Load notifications from API if logged in
async function loadNotifications() {
  const token = localStorage.getItem('authToken');
  if (!token) return;
  try {
    const items = await API.authGet('notifications');
    const unread = items.filter(n => !n.read);
    if (unread.length) {
      notifBadge.hidden = false;
      notifBadge.textContent = unread.length;
    }
    const list = document.getElementById('notifList');
    if (list && items.length) {
      list.innerHTML = items.map(n => `
        <div class="notif-item ${n.read ? '' : 'unread'}">
          <h4>${n.title}</h4>
          <p>${n.body}</p>
        </div>
      `).join('');
    }
  } catch { /* silent */ }
}

// Load after a small delay to let auth settle
setTimeout(loadNotifications, 1500);
