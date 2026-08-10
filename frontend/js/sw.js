/**
 * sw.js – OURS TTD Service Worker
 * Offline-first strategy: cache static assets, network-first for API calls.
 */
'use strict';

const CACHE_NAME = 'ours-ttd-v3';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/css/responsive.css',
  '/js/api.js',
  '/js/app.js',
  '/js/chatbot.js',
  '/js/queue.js',
  '/js/sos.js',
  '/js/voice.js',
  '/js/language.js',
  '/js/navigation.js',
  '/js/health.js',
  '/js/notifications.js',
  '/js/admin.js',
  '/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Network-first for API calls
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
    e.respondWith(fetch(e.request).catch(() => new Response(
      JSON.stringify({ error: 'You appear to be offline. Please reconnect.' }),
      { headers: { 'Content-Type': 'application/json' } }
    )));
    return;
  }

  // Cache-first for static assets
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      if (res.ok) {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      }
      return res;
    }))
  );
});
