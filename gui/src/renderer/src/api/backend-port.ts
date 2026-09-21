/**
 * Points the API and WebSocket clients at the backend port chosen by the main
 * process. Safe to call from any renderer window; the work runs once.
 */

import { apiClient } from './client'
import wsClient from './websocket'

const DEFAULT_PORT = 8765

let configured: Promise<number> | null = null

export function configureBackendPort(): Promise<number> {
  if (!configured) {
    configured = Promise.resolve(window.api?.getBackendPort?.() ?? DEFAULT_PORT)
      .catch(() => DEFAULT_PORT)
      .then((port) => {
        apiClient.setPort(port)
        wsClient.setPort(port)
        return port
      })
  }
  return configured
}

export default configureBackendPort
