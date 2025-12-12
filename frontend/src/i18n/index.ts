export type Language = 'pt-BR' | 'en-US';

export interface Translations {
  // Header
  title: string;
  total: string;
  downloading: string;
  pending: string;
  completed: string;
  failed: string;

  // UrlInput
  urlsLabel: string;
  urlsPlaceholder: string;
  quality: string;
  addToQueue: string;
  autoDownload: string;

  // DownloadQueue
  emptyQueue: string;
  cancelAll: string;
  clearCompleted: string;
  clearAll: string;

  // DownloadItem
  cancel: string;
  retry: string;
  downloadMp3: string;

  // StatusBadge
  status: {
    pending: string;
    fetching: string;
    downloading: string;
    converting: string;
    completed: string;
    failed: string;
    cancelled: string;
    skipped: string;
  };
}

export const translations: Record<Language, Translations> = {
  'pt-BR': {
    title: 'YT-MP3 Downloader',
    total: 'Total',
    downloading: 'Baixando',
    pending: 'Pendente',
    completed: 'Concluído',
    failed: 'Falhas',
    urlsLabel: 'URLs do YouTube (uma por linha)',
    urlsPlaceholder: 'https://www.youtube.com/watch?v=...',
    quality: 'Qualidade',
    addToQueue: 'Adicionar à Fila',
    autoDownload: 'Download automático ao concluir',
    emptyQueue: 'Nenhum download na fila. Adicione URLs acima para começar.',
    cancelAll: 'Cancelar todos',
    clearCompleted: 'Limpar concluídos',
    clearAll: 'Limpar tudo',
    cancel: 'Cancelar',
    retry: 'Tentar novamente',
    downloadMp3: 'Baixar MP3',
    status: {
      pending: 'Pendente',
      fetching: 'Obtendo info',
      downloading: 'Baixando',
      converting: 'Convertendo',
      completed: 'Concluído',
      failed: 'Falhou',
      cancelled: 'Cancelado',
      skipped: 'Já existe',
    },
  },
  'en-US': {
    title: 'YT-MP3 Downloader',
    total: 'Total',
    downloading: 'Downloading',
    pending: 'Pending',
    completed: 'Completed',
    failed: 'Failed',
    urlsLabel: 'YouTube URLs (one per line)',
    urlsPlaceholder: 'https://www.youtube.com/watch?v=...',
    quality: 'Quality',
    addToQueue: 'Add to Queue',
    autoDownload: 'Auto download when complete',
    emptyQueue: 'No downloads in queue. Add URLs above to start.',
    cancelAll: 'Cancel all',
    clearCompleted: 'Clear completed',
    clearAll: 'Clear all',
    cancel: 'Cancel',
    retry: 'Retry',
    downloadMp3: 'Download MP3',
    status: {
      pending: 'Pending',
      fetching: 'Fetching info',
      downloading: 'Downloading',
      converting: 'Converting',
      completed: 'Completed',
      failed: 'Failed',
      cancelled: 'Cancelled',
      skipped: 'Already exists',
    },
  },
};
