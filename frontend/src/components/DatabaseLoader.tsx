'use client';

import { useEffect, useState, useCallback } from 'react';
import api from '@/lib/api';
import LoadingScreen from './LoadingScreen';
import { AnimatePresence } from 'framer-motion';

interface DatabaseLoaderProps {
  children: React.ReactNode;
}

export default function DatabaseLoader({ children }: DatabaseLoaderProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [attempts, setAttempts] = useState(0);

  const checkConnection = useCallback(async () => {
    try {
      // Use centralized api instance
      const response = await api.get('/health', {
        timeout: 5000,
      });

      if (response.data.status === 'healthy') {
        setIsConnected(true);
      } else {
        setAttempts(prev => prev + 1);
      }
    } catch (error) {
      console.warn('Health check failed, retrying...', error);
      setAttempts(prev => prev + 1);
    }
  }, []);

  useEffect(() => {
    if (isConnected) return;

    const timer = setTimeout(() => {
      checkConnection();
    }, attempts === 0 ? 0 : 3000); // Wait 3 seconds between retries

    return () => clearTimeout(timer);
  }, [attempts, isConnected, checkConnection]);

  const handleManualRetry = useCallback(() => {
    setAttempts(0); // Reset attempts to trigger immediate check via useEffect
  }, []);

  return (
    <>
      <AnimatePresence mode="wait">
        {!isConnected && (
          <LoadingScreen
            attempts={attempts + 1}
            onRetry={handleManualRetry}
          />
        )}
      </AnimatePresence>
      {isConnected && children}
    </>
  );
}
