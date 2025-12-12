export type DownloadStatus =
  | 'pending'
  | 'fetching'
  | 'downloading'
  | 'converting'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'skipped';

export interface DownloadProgress {
  percent: number;
  downloaded_bytes: number;
  total_bytes: number;
  speed: string;
  eta: string;
}

export interface DownloadItem {
  id: string;
  url: string;
  title: string | null;
  status: DownloadStatus;
  progress: DownloadProgress;
  quality: string;
  file_path: string | null;
  file_size: number | null;
  error: string | null;
  created_at: string;
}

export interface QueueStats {
  total: number;
  pending: number;
  downloading: number;
  completed: number;
  failed: number;
}
