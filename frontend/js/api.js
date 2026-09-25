/**
 * api.js – Full API client with auth token support, error handling, and retry.
 * Must be loaded BEFORE app.js.
 */
'use strict';

const API = (() => {
  const getApiBase = () => {
    if (typeof window !== 'undefined' && window.location) {
      const { hostname, port, protocol } = window.location;
      // If served directly from the backend on port 8000
      if (port === '8000') {
        return '/api/';
      }
      // If opened via local dev servers (5500, 3000, 5173, etc.) or file://
      if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.') || hostname.startsWith('172.') || protocol === 'file:') {
        return 'http://127.0.0.1:8000/api/';
      }
      // In production
      return '/api/';
    }
    return '/api/';
  };
  let BASE = getApiBase();

  function token() {
    return localStorage.getItem('authToken');
  }

  function headers(json = true, withAuth = true) {
    const h = {};
    if (json) h['Content-Type'] = 'application/json';
    const t = token();
    if (withAuth && t) h['Authorization'] = `Bearer ${t}`;
    return h;
  }

  async function handle(res) {
    if (res.ok) return res.json().catch(() => ({}));
    let err;
    try { err = await res.json(); } catch { err = { detail: `HTTP ${res.status}` }; }
    if (res.status === 401) {
      localStorage.removeItem('authToken');
      // Don't redirect, just reject
    }
    return Promise.reject(err);
  }

  function clean(path) {
    return path.startsWith('/') ? path.slice(1) : path;
  }

  // Resilient fetch with fallback URL on network failure
  async function resilientFetch(urlPath, options) {
    const primaryUrl = BASE + clean(urlPath);
    try {
      return await fetch(primaryUrl, options);
    } catch (netErr) {
      // If primary failed (e.g. 127.0.0.1 blocked or port mismatch), try fallback
      const fallbacks = [];
      if (BASE !== '/api/') fallbacks.push('/api/' + clean(urlPath));
      if (BASE !== 'http://localhost:8000/api/') fallbacks.push('http://localhost:8000/api/' + clean(urlPath));
      if (BASE !== 'http://127.0.0.1:8000/api/') fallbacks.push('http://127.0.0.1:8000/api/' + clean(urlPath));

      for (const fallbackUrl of fallbacks) {
        try {
          const res = await fetch(fallbackUrl, options);
          if (res) {
            // Update BASE for future calls if this fallback succeeded
            if (fallbackUrl.startsWith('http')) {
              const u = new URL(fallbackUrl);
              BASE = `${u.origin}/api/`;
            } else {
              BASE = '/api/';
            }
            return res;
          }
        } catch (_) {}
      }
      throw netErr;
    }
  }

  return {
    // Public GET does not send auth headers by default, avoiding 401 from stale tokens
    get: (path) => resilientFetch(path, { headers: { 'Accept': 'application/json' } }).then(handle),

    post: (path, body) => fetch(BASE + clean(path), {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(body)
    }).then(handle),

    // Unauthenticated POST (for login/register/forgot-password)
    publicPost: (path, body) => fetch(BASE + clean(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(handle),

    put: (path, body) => fetch(BASE + clean(path), {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify(body)
    }).then(handle),

    // Authenticated wrappers (include Bearer token)
    authGet: (path) => fetch(BASE + clean(path), {
      headers: { 'Content-Type': 'application/json', ...({ Authorization: `Bearer ${token()}` }) }
    }).then(handle),

    authPost: (path, body) => fetch(BASE + clean(path), {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(body)
    }).then(handle),

    authPut: (path, body) => fetch(BASE + clean(path), {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify(body)
    }).then(handle),

    authDelete: (path) => fetch(BASE + clean(path), {
      method: 'DELETE',
      headers: headers(false)
    }).then(handle),
  };
})();
