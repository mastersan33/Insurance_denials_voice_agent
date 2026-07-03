/// <reference types="vite/client" />
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
  withCredentials: true,  // Send HttpOnly refresh_token cookie on all requests
});

// --- Request interceptor: inject latest JWT access token ---
api.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('auth-storage');
    if (stored) {
      const token: string | undefined = JSON.parse(stored)?.state?.token;
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
  } catch { /* malformed storage */ }
  return config;
});

// --- Refresh token rotation ---
let _isRefreshing = false;
let _failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null) {
  _failedQueue.forEach(({ resolve, reject }) => (token ? resolve(token) : reject(error)));
  _failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      if (_isRefreshing) {
        return new Promise((resolve, reject) => {
          _failedQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }

      original._retry = true;
      _isRefreshing = true;

      try {
        // Cookie is sent automatically (withCredentials: true) — no body needed
        const { data } = await axios.post(
          `${BASE_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true },
        );

        // Update persisted store (access token only — refresh lives in cookie)
        const current = JSON.parse(localStorage.getItem('auth-storage') || '{}');
        current.state = { ...current.state, token: data.access_token, user: data.user, isAuthenticated: true };
        localStorage.setItem('auth-storage', JSON.stringify(current));

        processQueue(null, data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('auth-storage');
        window.location.replace('/login');
        return Promise.reject(refreshError);
      } finally {
        _isRefreshing = false;
      }
    }

    if (!error.response) {
      error.message =
        error.code === 'ECONNABORTED'
          ? 'Request timed out. Please try again.'
          : 'Network error. Check your connection and try again.';
    }

    return Promise.reject(error);
  }
);
