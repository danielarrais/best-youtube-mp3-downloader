import { DownloadItem as DownloadItemType } from '../types';
import { DownloadItem } from './DownloadItem';
import { useTranslation } from '../hooks/useTranslation';

interface DownloadQueueProps {
  downloads: DownloadItemType[];
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
  onClearCompleted: () => void;
  onCancelAll: () => void;
  onClearAll: () => void;
}

export function DownloadQueue({ downloads, onCancel, onRetry, onClearCompleted, onCancelAll, onClearAll }: DownloadQueueProps) {
  const { t } = useTranslation();
  const hasCompleted = downloads.some(d => d.status === 'completed' || d.status === 'skipped');
  const hasPending = downloads.some(d => ['pending', 'fetching', 'downloading', 'converting'].includes(d.status));

  if (downloads.length === 0) {
    return (
      <div className="text-center text-gray-400 py-12">
        {t.emptyQueue}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end gap-4">
        {hasPending && (
          <button
            onClick={onCancelAll}
            className="text-sm text-red-400 hover:text-red-300 transition-colors"
          >
            {t.cancelAll}
          </button>
        )}
        {hasCompleted && (
          <button
            onClick={onClearCompleted}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            {t.clearCompleted}
          </button>
        )}
        <button
          onClick={onClearAll}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          {t.clearAll}
        </button>
      </div>

      <div className="space-y-3">
        {downloads.map(item => (
          <DownloadItem
            key={item.id}
            item={item}
            onCancel={onCancel}
            onRetry={onRetry}
          />
        ))}
      </div>
    </div>
  );
}
