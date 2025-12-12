import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';
import { DownloadItem, QueueStats } from '../types';

export function useDownloads() {
  const [downloads, setDownloads] = useState<Map<string, DownloadItem>>(new Map());
  const [stats, setStats] = useState<QueueStats>({
    total: 0,
    pending: 0,
    downloading: 0,
    completed: 0,
    failed: 0
  });
  const [autoDownload, setAutoDownload] = useState(false);
  const downloadedIds = useRef<Set<string>>(new Set());
  const ignoredIds = useRef<Set<string>>(new Set());

  // Carregar downloads iniciais
  useEffect(() => {
    api.getDownloads().then((items: DownloadItem[]) => {
      const map = new Map<string, DownloadItem>();
      items.forEach(item => map.set(item.id, item));
      setDownloads(map);
    });

    api.getStats().then(setStats);
  }, []);

  // Atualizar item via WebSocket
  const handleItemUpdate = useCallback((item: DownloadItem) => {
    // Ignorar itens que foram cancelados/removidos
    if (ignoredIds.current.has(item.id)) {
      return;
    }

    setDownloads(prev => {
      const newMap = new Map(prev);
      newMap.set(item.id, item);
      return newMap;
    });

    // Download automático quando concluir
    if (autoDownload && (item.status === 'completed' || item.status === 'skipped') && item.file_path) {
      if (!downloadedIds.current.has(item.id)) {
        downloadedIds.current.add(item.id);
        const filename = item.file_path.split('/').pop() || '';
        const link = document.createElement('a');
        link.href = api.getFileUrl(filename);
        link.download = filename;
        link.click();
      }
    }
  }, [autoDownload]);

  // Atualizar stats via WebSocket
  const handleStatsUpdate = useCallback((newStats: QueueStats) => {
    setStats(newStats);
  }, []);

  // Conectar WebSocket
  useWebSocket({
    onItemUpdate: handleItemUpdate,
    onStatsUpdate: handleStatsUpdate
  });

  // Adicionar downloads
  const addDownloads = useCallback(async (urls: string[], quality: string) => {
    const items = await api.addDownloads(urls, quality);
    items.forEach((item: DownloadItem) => {
      setDownloads(prev => {
        const newMap = new Map(prev);
        newMap.set(item.id, item);
        return newMap;
      });
    });
  }, []);

  // Cancelar download
  const cancelDownload = useCallback(async (id: string) => {
    await api.cancelDownload(id);
    setDownloads(prev => {
      const newMap = new Map(prev);
      newMap.delete(id);
      return newMap;
    });
  }, []);

  // Retentar download
  const retryDownload = useCallback(async (id: string) => {
    const item = await api.retryDownload(id);
    setDownloads(prev => {
      const newMap = new Map(prev);
      newMap.set(item.id, item);
      return newMap;
    });
  }, []);

  // Limpar concluídos
  const clearCompleted = useCallback(async () => {
    await api.clearCompleted();
    setDownloads(prev => {
      const newMap = new Map(prev);
      for (const [id, item] of newMap) {
        if (item.status === 'completed' || item.status === 'skipped') {
          newMap.delete(id);
        }
      }
      return newMap;
    });
  }, []);

  // Cancelar todos pendentes
  const cancelAll = useCallback(async () => {
    setDownloads(prev => {
      const newMap = new Map(prev);
      for (const [id, item] of newMap) {
        if (['pending', 'fetching', 'downloading', 'converting'].includes(item.status)) {
          ignoredIds.current.add(id);
          newMap.delete(id);
        }
      }
      return newMap;
    });
    await api.cancelAll();
  }, []);

  // Limpar tudo
  const clearAll = useCallback(async () => {
    setDownloads(prev => {
      for (const id of prev.keys()) {
        ignoredIds.current.add(id);
      }
      return new Map();
    });
    downloadedIds.current.clear();
    await api.clearAll();
  }, []);

  return {
    downloads: Array.from(downloads.values()),
    stats,
    addDownloads,
    cancelDownload,
    retryDownload,
    clearCompleted,
    cancelAll,
    clearAll,
    autoDownload,
    setAutoDownload
  };
}
