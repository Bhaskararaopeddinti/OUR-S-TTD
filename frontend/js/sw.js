/**
 * sw.js – OURS TTD Service Worker (PWA)
 * Offline-first strategy for static assets, network-first for API calls.
 * Uses safe individual resource caching to prevent install failures.
 */
'use strict';

const CACHE_NAME = 'ours-ttd-v4';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/favicon.svg',
  '/manifest.json',
  '/css/style.css',
  '/css/responsive.css',
  '/css/components.css',
  '/css/dashboard.css',
  '/css/admin-portal.css',
  '/js/api.js',
  '/js/app.js',
  '/js/dashboard.js',
  '/js/chatbot.js',
  '/js/chatbot-page.js',
  '/js/queue.js',
  '/js/sos.js',
  '/js/emergency.js',
  '/js/voice.js',
  '/js/language.js',
  '/js/navigation.js',
  '/js/health.js',
  '/js/notifications.js',
  '/js/admin.js',
  '/js/booking.js',
  '/js/maps.js',
  '/js/transport.js',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/pages/dashboard.html',
  '/pages/queue.html',
  '/pages/food.html',
  '/pages/medical.html',
  '/pages/emergency.html',
  '/pages/accommodation.html',
  '/pages/chatbot.html',
  '/pages/transport.html',
  '/pages/admin.html',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(async cache => {
        for (const url of STATIC_ASSETS) {
          try {
            await cache.add(url);
          } catch (err) {
            console.warn('[SW] Could not cache static asset:', url, err);
          }
        }
      })
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith('ours-ttd-') && k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip non-GET requests and API/WebSocket routes (network-only or network-first)
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
    event.respondWith(
      fetch(event.request).catch(() => new Response(
        JSON.stringify({ error: 'You appear to be offline. Please reconnect.' }),
        { headers: { 'Content-Type': 'application/json' } }
      ))
    );
    return;
  }

  // Cache-first strategy with network fallback for static assets
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).then(res => {
      if (res.ok && res.type === 'basic') {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
      }
      return res;
    }))
  );
});
