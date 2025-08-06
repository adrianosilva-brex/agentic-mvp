import React, { useState, useEffect, useCallback } from 'react';
import { SyncButton } from './components/SyncButton';
import { EmbeddedModal } from './components/EmbeddedModal';
import { PROVIDERS } from './services/providers';
import './App.css';

type MigrationStatus = 'IN_PROGRESS' | 'COMPLETE' | 'FAILED' | null;

function App() {
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [modalUrl, setModalUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [migrationId, setMigrationId] = useState<string | null>(null);
  const [migrationStatus, setMigrationStatus] = useState<MigrationStatus>(null);


  const checkMigrationStatus = useCallback(async (id: string) => {
    try {
      const response = await fetch(`https://worker.anon.com/api/v1/migrations/${id}`, {
        headers: {
          'Authorization': `Bearer ${process.env.REACT_APP_ANON_API_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch migration status');
      
      const data = await response.json();
      setMigrationStatus(data.status);
      
      if (data.status === 'COMPLETE') {
        setModalUrl(null);
        setMigrationId(null);
      } else if (data.status === 'FAILED') {
        setError('Migration failed. Please try again.');
        setModalUrl(null);
        setMigrationId(null);
      }
    } catch (err) {
      console.error('Error checking migration status:', err);
    }
  }, []);

  useEffect(() => {
    const handleModalMessage = (event: MessageEvent) => {
      // Verify event source
      if (event.data?.source !== "anon_modal") return;

      const modalEvent = event.data.event;
      if (!modalEvent) return;

      switch (modalEvent.type) {
        case "migration_modal.opened":
          console.log('Modal opened - Welcome step');
          break;
        case "migration_modal.completed":
          console.log('Migration started');
          setMigrationStatus('IN_PROGRESS');
          break;
        case "migration_modal.closed":
          console.log('Modal closed');
          setModalUrl(null);
          setMigrationId(null);
          break;
        case "migration_modal.failed":
          console.log('Migration failed:', modalEvent.data.error_message);
          setError(modalEvent.data.error_message || 'Migration failed');
          setModalUrl(null);
          setMigrationId(null);
          break;
        case "migration_modal_step.started":
          console.log('Step started:', modalEvent.data.modal_step);
          break;
        case "migration_modal_step.failed":
          console.log('Step failed:', modalEvent.data.error_message);
          setError(modalEvent.data.error_message || 'Step failed');
          break;
      }
    };

    window.addEventListener("message", handleModalMessage);
    return () => window.removeEventListener("message", handleModalMessage);
  }, []);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;

    if (migrationId && migrationStatus === 'IN_PROGRESS') {
      pollInterval = setInterval(() => {
        checkMigrationStatus(migrationId);
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [migrationId, migrationStatus, checkMigrationStatus]);

  const handleSync = async (providerId: string) => {
    setActiveProvider(providerId);
    setError(null);
    setMigrationStatus(null);
    
    try {
      const provider = PROVIDERS.find(p => p.id === providerId);
      if (!provider) throw new Error('Provider not found');
      
      const url = await provider.getEmbedUrl();
      const response = await fetch(`https://worker.anon.com/api/v1/migration-modal`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.REACT_APP_ANON_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: 'adriano.silva@brex.com',
        })
      });

      if (!response.ok) throw new Error('Failed to initialize migration');
      
      const { url: modalUrl, migration_id } = await response.json();
      setModalUrl(modalUrl);
      setMigrationId(migration_id);
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setActiveProvider(null);
    }
  };

  const handleModalClose = () => {
    setModalUrl(null);
    setMigrationId(null);
    setMigrationStatus(null);
  };

  return (
    <div className="app">
      <h1 className="app-title">Agentic TMC Data Gatherer Exploration</h1>
      
      <div className="providers-grid">
        <SyncButton
          isLoading={!!activeProvider}
          onClick={() => handleSync(PROVIDERS[0].id)}
          disabled={migrationStatus === 'IN_PROGRESS'}
        />
      </div>
      
      {error && <p className="error">{error}</p>}
      {migrationStatus === 'IN_PROGRESS' && (
        <div className="migration-status">
          <p>Migration in progress...</p>
        </div>
      )}
      {migrationStatus === 'COMPLETE' && (
        <div className="migration-status success">
          <p>Migration completed successfully!</p>
        </div>
      )}
      {modalUrl && <EmbeddedModal url={modalUrl} onClose={handleModalClose} />}
    </div>
  );
}

export default App;