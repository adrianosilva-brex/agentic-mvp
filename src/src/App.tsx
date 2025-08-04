import React, { useState } from 'react';
import { SyncButton } from './components/SyncButton';
import { EmbeddedModal } from './components/EmbeddedModal';
import { PROVIDERS } from './services/providers';
import './App.css';

function App() {
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [modalUrl, setModalUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSync = async (providerId: string) => {
    setActiveProvider(providerId);
    setError(null);
    
    try {
      const provider = PROVIDERS.find(p => p.id === providerId);
      if (!provider) throw new Error('Provider not found');
      
      const url = await provider.getEmbedUrl();
      setModalUrl(url);
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setActiveProvider(null);
    }
  };

  const handleModalClose = () => {
    setModalUrl(null);
  };

  return (
    <div className="app">
      <h1 className="app-title">Agentic TMC Data Gatherer Exploration</h1>
      
      <div className="providers-grid">
        {PROVIDERS.map(provider => (
          <SyncButton
            key={provider.id}
            provider={provider.name}
            isLoading={activeProvider === provider.id}
            onClick={() => handleSync(provider.id)}
          />
        ))}
      </div>
      
      {error && <p className="error">{error}</p>}
      {modalUrl && <EmbeddedModal url={modalUrl} onClose={handleModalClose} />}
    </div>
  );
}

export default App;