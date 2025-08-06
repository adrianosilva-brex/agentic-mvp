import React from 'react';

interface SyncButtonProps {
  isLoading: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function SyncButton({ isLoading, onClick, disabled }: SyncButtonProps) {
  return (
    <button 
      onClick={onClick}
      disabled={isLoading || disabled}
      className="sync-button"
    >
      {isLoading ? "Syncing with external TMCs..." : "Sync with external TMCs"}
    </button>
  );
}