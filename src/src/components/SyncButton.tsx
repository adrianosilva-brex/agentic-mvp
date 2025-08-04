import React from 'react';

interface SyncButtonProps {
  provider: string;
  isLoading: boolean;
  onClick: () => void;
}

export function SyncButton({ provider, isLoading, onClick }: SyncButtonProps) {
  return (
    <button 
      onClick={onClick}
      disabled={isLoading}
      className="sync-button"
    >
      {isLoading ? `Syncing with ${provider}...` : `Sync with ${provider}`}
    </button>
  );
}