import { Header } from './components/Header';
import { UrlInput } from './components/UrlInput';
import { DownloadQueue } from './components/DownloadQueue';
import { useDownloads } from './hooks/useDownloads';

function App() {
  const { downloads, stats, addDownloads, cancelDownload, retryDownload, clearCompleted, cancelAll, clearAll, autoDownload, setAutoDownload } = useDownloads();

  return (
    <div className="min-h-screen bg-gray-900">
      <Header stats={stats} />
      
      <main className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        <UrlInput 
          onSubmit={addDownloads}
          autoDownload={autoDownload}
          onAutoDownloadChange={setAutoDownload}
        />
        
        <DownloadQueue
          downloads={downloads}
          onCancel={cancelDownload}
          onRetry={retryDownload}
          onClearCompleted={clearCompleted}
          onCancelAll={cancelAll}
          onClearAll={clearAll}
        />
      </main>
    </div>
  );
}

export default App;
