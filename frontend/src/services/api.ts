const API_URL = import.meta.env.VITE_API_URL || '';

async function handleResponse(response: Response) {
  if (!response.ok && response.status !== 404) {
    throw new Error(`HTTP error: ${response.status}`);
  }
  return response.json();
}

export const api = {
  addDownloads: async (urls: string[], quality: string) => {
    const response = await fetch(`${API_URL}/api/downloads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls, quality })
    });
    return handleResponse(response);
  },

  getDownloads: async () => {
    const response = await fetch(`${API_URL}/api/downloads`);
    return handleResponse(response);
  },

  cancelDownload: async (id: string) => {
    const response = await fetch(`${API_URL}/api/downloads/${id}`, { method: 'DELETE' });
    if (response.status === 404) return { message: 'Já removido' };
    return response.json();
  },

  retryDownload: async (id: string) => {
    const response = await fetch(`${API_URL}/api/downloads/${id}/retry`, { method: 'POST' });
    return response.json();
  },

  getStats: async () => {
    const response = await fetch(`${API_URL}/api/queue/stats`);
    return response.json();
  },

  clearCompleted: async () => {
    const response = await fetch(`${API_URL}/api/queue/clear`, { method: 'POST' });
    return response.json();
  },

  cancelAll: async () => {
    const response = await fetch(`${API_URL}/api/queue/cancel-all`, { method: 'POST' });
    return response.json();
  },

  clearAll: async () => {
    const response = await fetch(`${API_URL}/api/queue/clear-all`, { method: 'POST' });
    return response.json();
  },

  getFileUrl: (filename: string) => `${API_URL}/api/files/${encodeURIComponent(filename)}`,

  deleteAllFiles: async () => {
    const response = await fetch(`${API_URL}/api/files`, { method: 'DELETE' });
    return handleResponse(response);
  },
};

export const WS_URL = `ws://${window.location.host}/ws`;
