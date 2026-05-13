const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Wrap réponse pour supporter à la fois { data } destructuring (style Axios)
// ET accès direct (style fetch). Si c'est un object, on injecte .data = self via Proxy.
function wrap<T>(result: T): T {
  if (result === null || typeof result !== 'object') return result;
  return new Proxy(result as any, {
    get: (target, prop) => (prop === 'data' ? target : target[prop]),
  });
}

class ApiClient {
  private accessToken: string | null = null;

  constructor() {
    this.accessToken = localStorage.getItem('access_token');
  }

  setToken(token: string) {
    this.accessToken = token;
    localStorage.setItem('access_token', token);
  }

  clearToken() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  private async request<T = unknown>(method: string, path: string, body?: unknown, isRetry = false): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.accessToken) headers['Authorization'] = `Bearer ${this.accessToken}`;
    const response = await fetch(`${API_BASE}${path}`, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
    if (response.status === 401 && !isRetry) {
      const refreshed = await this.tryRefresh();
      if (refreshed) return this.request<T>(method, path, body, true);
      this.clearToken();
      window.location.href = '/login';
      throw new ApiError(401, 'Session expirée');
    }
    if (!response.ok) {
      let errorMsg = `HTTP ${response.status}`;
      try { const errData = await response.json(); errorMsg = errData.detail || errData.message || errorMsg; } catch { }
      throw new ApiError(response.status, errorMsg);
    }
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) return null as T;
    const text = await response.text();
    if (!text) return null as T;
    try { return wrap(JSON.parse(text)) as T; } catch { return text as unknown as T; }
  }

  private async tryRefresh(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) });
      if (!response.ok) return false;
      const data = await response.json();
      if (data.access_token) {
        this.setToken(data.access_token);
        if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
        return true;
      }
    } catch { }
    return false;
  }

  get<T = unknown>(path: string): Promise<T> { return this.request<T>('GET', path); }
  post<T = unknown>(path: string, body?: unknown): Promise<T> { return this.request<T>('POST', path, body); }
  put<T = unknown>(path: string, body?: unknown): Promise<T> { return this.request<T>('PUT', path, body); }
  patch<T = unknown>(path: string, body?: unknown): Promise<T> { return this.request<T>('PATCH', path, body); }
  delete<T = unknown>(path: string): Promise<T> { return this.request<T>('DELETE', path); }

  async getBlob(path: string): Promise<Blob> {
    const headers: Record<string, string> = {};
    if (this.accessToken) headers['Authorization'] = `Bearer ${this.accessToken}`;
    const response = await fetch(`${API_BASE}${path}`, { headers });
    if (!response.ok) throw new ApiError(response.status, `Download failed: ${response.status}`);
    return response.blob();
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
    if (!response.ok) throw new ApiError(response.status, 'Identifiants invalides');
    const data = await response.json();
    if (data.access_token) {
      this.setToken(data.access_token);
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
    }
    return data;
  }

  logout() { this.clearToken(); }
  isAuthenticated(): boolean { return !!this.accessToken; }
}

export const apiClient = new ApiClient();
export { ApiError };
