import React, { useEffect } from 'react';

interface EmbeddedModalProps {
  url: string;
  onClose: () => void;
}

export function EmbeddedModal({ url, onClose }: EmbeddedModalProps) {
  useEffect(() => {
    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;border:0;z-index:9999';
    iframe.setAttribute('allow', 'clipboard-read; clipboard-write');
    
    // Create close button
    const closeButton = document.createElement('button');
    closeButton.innerText = '✕';
    closeButton.style.cssText = 'position:fixed;top:20px;right:20px;z-index:10000;padding:8px 12px;background:#fff;border:1px solid #ddd;border-radius:4px;cursor:pointer;';
    closeButton.onclick = () => {
      iframe.remove();
      closeButton.remove();
      onClose();
    };

    // Add elements to DOM
    document.body.appendChild(iframe);
    document.body.appendChild(closeButton);

    // Cleanup on unmount
    return () => {
      iframe.remove();
      closeButton.remove();
    };
  }, [url, onClose]);

  return null;
}