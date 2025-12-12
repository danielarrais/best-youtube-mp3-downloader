import { useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../services/api';
import { DownloadItem, QueueStats } from '../types';

interface WebSocketMessage {
  type: 'download:update' | 'queue:stats';
  data: DownloadItem | QueueStats;
}

interface UseWebSocketProps {
  onItemUpdate: (item: DownloadItem) => void;
  onStatsUpdate: (stats: QueueStats) => void;
}

export function useWebSocket({ onItemUpdate, onStatsUpdate }: UseWebSocketProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      if (message.type === 'download:update') {
        onItemUpdate(message.data as DownloadItem);
      } else if (message.type === 'queue:stats') {
        onStatsUpdate(message.data as QueueStats);
      }
    };

    ws.onclose = () => {
      // Reconectar após 3 segundos
      reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [onItemUpdate, onStatsUpdate]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);
}
