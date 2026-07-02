import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000, // 30 s — abort hung requests rather than waiting forever
});

// --- Request interceptor: always inject the latest token from storage ---
api.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('auth-storage');
    if (stored) {
      const parsed = JSON.parse(stored);
      const token: string | undefined = parsed?.state?.token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  } catch {
    // Malformed storage — ignore and continue without token
  }
  return config;
});

// --- Response interceptor: handle auth expiry and network errors ---
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage');
      // Use replace so the browser back button doesn't loop back into a 401
      window.location.replace('/login');
    }
    // Surface network/timeout errors with a usable message
    if (!error.response) {
      error.message = error.code === 'ECONNABORTED'
        ? 'Request timed out. Please try again.'
        : 'Network error. Check your connection and try again.';
    }
    return Promise.reject(error);
  }
);
