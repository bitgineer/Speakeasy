/**
 * useBackendStatus Hook
 * 
 * Polls backend health endpoint for status updates.
 */

import { useEffect, useCallback } from 'react'
import { useAppStore } from '../store'

interface UseBackendStatusOptions {
  pollInterval?: number
  enabled?: boolean
}

export function useBackendStatus(options: UseBackendStatusOptions = {}): {
  isConnected: boolean
  modelLoaded: boolean
  refresh: () => Promise<void>
} {
  const { pollInterval = 5000, enabled = true } = options
  
  const { 
    backendConnected, 
    modelLoaded,
    fetchHealth 
  } = useAppStore()
  
  // Initial fetch
  useEffect(() => {
    if (!enabled) return
    
    fetchHealth()
  }, [enabled, fetchHealth])
  
  // Polling
  useEffect(() => {
    if (!enabled) return
    
    const interval = setInterval(() => {
      fetchHealth()
    }, pollInterval)
    
    return () => clearInterval(interval)
  }, [enabled, pollInterval, fetchHealth])
  
  const refresh = useCallback(async () => {
    await fetchHealth()
  }, [fetchHealth])
  
  return {
    isConnected: backendConnected,
    modelLoaded,
    refresh
  }
}

export default useBackendStatus
