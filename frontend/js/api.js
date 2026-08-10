/**
 * api.js – Full API client with auth token support, error handling, and retry.
 * Must be loaded BEFORE app.js.
 */
'use strict';

const API = (() => {
  const getApiBase = () => {
    if (typeof window !== 'undefined' && (window.location.protocol === 'file:' || window.location.port === '5500' || window.location.port === '5501')) {
      return 'http://localhost:8000/api/';
    }
    return '/api/';
  };
  const BASE = getApiBase();


  function token() {
    return localStorage.getItem('authToken');
  }

  function headers(json = true) {
    const h = {};
    if (json) h['Content-Type'] = 'application/json';
    const t = token();
    if (t) h['Authorization'] = `Bearer ${t}`;
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

  return {
    get: (path) => fetch(BASE + clean(path), { headers: headers(false) }).then(handle),

    post: (path, body) => fetch(BASE + clean(path), {
      method: 'POST',
      headers: headers(),
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
