/**
 * sw.js – OURS TTD Service Worker (PWA)
 * Resilient static asset caching, offline fallback for navigation,
 * and live network pass-through for API and WebSocket endpoints.
 */
'use strict';

const CACHE_NAME = 'ours-ttd-v5';

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

// Install Event: Safely cache static assets individually without crashing
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      for (const asset of STATIC_ASSETS) {
        try {
          const response = await fetch(asset);
          if (response.ok) {
            await cache.put(asset, response);
            console.log('[SW] Cached:', asset);
          } else {
            console.warn('[SW] Skipped (non-200):', asset, response.status);
          }
        } catch (error) {
          console.warn('[SW] Could not cache:', asset, error);
        }
      }
      return self.skipWaiting();
    })
  );
});

// Activate Event: Clean up old OURS TTD caches and claim clients
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith('ours-ttd-') && k !== CACHE_NAME)
          .map(k => {
            console.log('[SW] Deleting obsolete cache:', k);
            return caches.delete(k);
          })
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch Event: Bypass SW for API & WebSocket; Cache-first with network fallback for static assets
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Exclude non-GET, API routes (/api/*), and WebSockets (/ws/*) from cache
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
    return; // Allow browser default network request
  }

  // Cache-first strategy with network fallback
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then(networkResponse => {
        if (networkResponse && networkResponse.ok && networkResponse.type === 'basic') {
          const clone = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return networkResponse;
      }).catch(err => {
        // If navigation request fails offline, serve cached /index.html
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html') || caches.match('/');
        }
        throw err;
      });
    })
  );
});
