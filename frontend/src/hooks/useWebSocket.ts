import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';

const BASE_WS_URL = import.meta.env.VITE_WS_URL || '';

// Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (cap)
const BACKOFF_BASE_MS = 1_000;
const BACKOFF_MAX_MS = 30_000;
const PING_INTERVAL_MS = 25_000;

function getWsBase(): string {
  if (BASE_WS_URL) return BASE_WS_URL;
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.host}`;
}

/**
 * Connects to /ws/dashboard and updates the 'dashboard-stats' React Query
 * cache whenever the server pushes new stats.
 *
 * Reconnect strategy: exponential backoff (1s → 2s → 4s … 30s cap).
 * Connection is dropped + re-established when the auth token changes.
 */
export function useDashboardWebSocket() {
  const token = useAuthStore((s) => s.token);
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);
  const attemptRef = useRef(0);   // tracks consecutive failures for backoff

  const clearTimers = () => {
    if (reconnectTimer.current) { clearTimeout(reconnectTimer.current); reconnectTimer.current = null; }
    if (pingTimer.current) { clearInterval(pingTimer.current); pingTimer.current = null; }
  };

  const connect = useCallback(() => {
    if (!token || !mountedRef.current) return;

    const url = `${getWsBase()}/ws/dashboard?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      attemptRef.current = 0;  // reset backoff on successful connection

      // Heartbeat — keeps the connection alive through load balancers
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        if (msg.type === 'stats' && msg.data) {
          qc.setQueryData(['dashboard-stats'], msg.data);
        }
        // pong — no action needed (just keeps the connection alive)
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = (ev) => {
      clearTimers();
      if (!mountedRef.current) return;
      // Don't reconnect on clean auth failure (4001/4003)
      if (ev.code === 4001 || ev.code === 4003) return;

      attemptRef.current += 1;
      const delay = Math.min(
        BACKOFF_BASE_MS * 2 ** (attemptRef.current - 1),
        BACKOFF_MAX_MS,
      );
      reconnectTimer.current = setTimeout(() => {
        if (mountedRef.current) connect();
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [token, qc]);

  useEffect(() => {
    mountedRef.current = true;
    attemptRef.current = 0;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimers();
      wsRef.current?.close();
    };
  }, [connect]);
}
