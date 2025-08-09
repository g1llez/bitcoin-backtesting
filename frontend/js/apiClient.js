// API client minimal – ne définit aucun fallback; exige window.API_BASE
(() => {
  if (!window.API_BASE) {
    throw new Error('API_BASE non défini. Définissez window.API_BASE dans index.html.');
  }

  async function apiFetch(path, options = {}) {
    const url = `${window.API_BASE}${path}`;
    const response = await fetch(url, options);
    if (!response.ok) {
      const text = await response.text().catch(() => '');
      const err = new Error(`Requête API échouée: ${response.status} ${response.statusText}`);
      err.status = response.status;
      err.body = text;
      throw err;
    }
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) return response.json();
    return response.text();
  }

  window.apiClient = {
    get: (path) => apiFetch(path),
    post: (path, body) => apiFetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }),
    put: (path, body) => apiFetch(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }),
    del: (path) => apiFetch(path, { method: 'DELETE' })
  };
})();


