import { useState } from 'react';
import { useTranslation } from '../hooks/useTranslation';

interface UrlInputProps {
  onSubmit: (urls: string[], quality: string) => void;
  autoDownload: boolean;
  onAutoDownloadChange: (value: boolean) => void;
}

export function UrlInput({ onSubmit, autoDownload, onAutoDownloadChange }: UrlInputProps) {
  const { t } = useTranslation();
  const [urls, setUrls] = useState('');
  const [quality, setQuality] = useState('192k');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const urlList = urls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (urlList.length > 0) {
      onSubmit(urlList, quality);
      setUrls('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-4 space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          {t.urlsLabel}
        </label>
        <textarea
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          placeholder={`${t.urlsPlaceholder}\n${t.urlsPlaceholder}`}
          className="w-full h-32 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
        />
      </div>

      <div className="flex items-center gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {t.quality}
          </label>
          <select
            value={quality}
            onChange={(e) => setQuality(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-red-500"
          >
            <option value="128k">128 kbps</option>
            <option value="192k">192 kbps</option>
            <option value="320k">320 kbps</option>
          </select>
        </div>

        <button
          type="submit"
          className="mt-6 bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
        >
          {t.addToQueue}
        </button>

        <label className="mt-6 flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autoDownload}
            onChange={(e) => onAutoDownloadChange(e.target.checked)}
            className="w-4 h-4 accent-red-500"
          />
          <span className="text-sm text-gray-300">{t.autoDownload}</span>
        </label>
      </div>
    </form>
  );
}
