import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';

const BASE_WS_URL = import.meta.env.VITE_WS_URL || '';

function getWsBase(): string {
  if (BASE_WS_URL) return BASE_WS_URL;
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.host}`;
}

/**
 * Connects to /ws/dashboard and updates the 'dashboard-stats' React Query
 * cache whenever the server pushes new stats. Auto-reconnects on disconnect.
 */
export function useDashboardWebSocket() {
  const token = useAuthStore((s) => s.token);
  const qc = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!token || !mountedRef.current) return;

    const url = `${getWsBase()}/ws/dashboard?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        if (msg.type === 'stats' && msg.data) {
          qc.setQueryData(['dashboard-stats'], msg.data);
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      // Reconnect after 5 seconds
      reconnectTimer.current = setTimeout(() => {
        if (mountedRef.current) connect();
      }, 5_000);
    };

    ws.onerror = () => {
      ws.close();
    };

    // Send ping every 30s to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30_000);

    return () => clearInterval(pingInterval);
  }, [token, qc]);

  useEffect(() => {
    mountedRef.current = true;
    const cleanup = connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      cleanup?.();
    };
  }, [connect]);
}
