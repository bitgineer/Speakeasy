/**
 * Main Entry Point - React 18 createRoot
 */

import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { configureBackendPort } from './api/backend-port'
import './styles/globals.css'

// Get the root element
const container = document.getElementById('root')

if (!container) {
  throw new Error('Root element not found')
}

// Point the clients at the configured backend port before anything fetches
configureBackendPort()

// Create root and render
const root = createRoot(container)
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
