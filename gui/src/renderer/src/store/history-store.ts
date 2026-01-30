/**
 * History Store - Transcription history management
 * 
 * Manages the list of past transcriptions with search and pagination.
 * Subscribes to WebSocket for real-time updates.
 */

import { create } from 'zustand'
import { apiClient } from '../api/client'
import wsClient from '../api/websocket'
import type { TranscriptionRecord, HistoryStats, TranscriptionEvent } from '../api/types'

interface HistoryStore {
  // Data
  items: TranscriptionRecord[]
  total: number
  stats: HistoryStats | null
  
  // Pagination
  limit: number
  offset: number
  hasMore: boolean
  currentPage: number
  totalPages: number
  
  // Search
  searchQuery: string
  
  // Loading state
  isLoading: boolean
  isLoadingMore: boolean
  error: string | null
  
  // Actions
  fetchHistory: (reset?: boolean) => Promise<void>
  loadMore: () => Promise<void>
  goToPage: (page: number) => Promise<void>
  setPageSize: (size: number) => Promise<void>
  
  setSearchQuery: (query: string) => void
  search: (query: string) => Promise<void>
  
  addItem: (item: TranscriptionRecord) => void
  deleteItem: (id: string) => Promise<boolean>
  
  fetchStats: () => Promise<void>
  
  setError: (error: string | null) => void
  clearError: () => void
  reset: () => void
}

const DEFAULT_LIMIT = 50

export const useHistoryStore = create<HistoryStore>((set, get) => ({
  // Initial state
  items: [],
  total: 0,
  stats: null,
  
  limit: DEFAULT_LIMIT,
  offset: 0,
  hasMore: false,
  currentPage: 1,
  totalPages: 1,
  
  searchQuery: '',
  
  isLoading: false,
  isLoadingMore: false,
  error: null,
  
  // Actions
  fetchHistory: async (reset = true) => {
    const { limit, searchQuery, currentPage } = get()
    const offset = reset ? 0 : (currentPage - 1) * limit
    
    if (reset) {
      set({ isLoading: true, offset: 0, currentPage: 1, error: null })
    }
    
    try {
      const response = await apiClient.getHistory({
        limit,
        offset,
        search: searchQuery || undefined
      })
      
      const totalPages = Math.max(1, Math.ceil(response.total / limit))
      
      set({
        items: response.items,
        total: response.total,
        hasMore: response.items.length === limit && offset + response.items.length < response.total,
        offset,
        totalPages,
        isLoading: false
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch history',
        isLoading: false
      })
    }
  },
  
  loadMore: async () => {
    const { hasMore, isLoadingMore, currentPage, totalPages } = get()
    if (!hasMore || isLoadingMore || currentPage >= totalPages) return
    
    // For infinite scroll, load next page
    await get().goToPage(currentPage + 1)
  },
  
  goToPage: async (page: number) => {
    const { limit, searchQuery, totalPages, isLoading } = get()
    if (isLoading || page < 1 || page > totalPages) return
    
    const offset = (page - 1) * limit
    set({ isLoading: true, error: null })
    
    try {
      const response = await apiClient.getHistory({
        limit,
        offset,
        search: searchQuery || undefined
      })
      
      const newTotalPages = Math.max(1, Math.ceil(response.total / limit))
      
      set({
        items: response.items,
        total: response.total,
        hasMore: offset + response.items.length < response.total,
        offset,
        currentPage: page,
        totalPages: newTotalPages,
        isLoading: false
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load page',
        isLoading: false
      })
    }
  },
  
  setPageSize: async (size: number) => {
    set({ limit: size, currentPage: 1, offset: 0 })
    await get().fetchHistory(true)
  },
  
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  search: async (query) => {
    set({ searchQuery: query, offset: 0 })
    await get().fetchHistory(true)
  },
  
  addItem: (item) => {
    const { items, total } = get()
    // Add to the beginning of the list
    set({
      items: [item, ...items],
      total: total + 1
    })
  },
  
  deleteItem: async (id) => {
    try {
      await apiClient.deleteHistoryItem(id)
      const { items, total } = get()
      set({
        items: items.filter(item => item.id !== id),
        total: Math.max(0, total - 1)
      })
      return true
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete item'
      })
      return false
    }
  },
  
  fetchStats: async () => {
    try {
      const stats = await apiClient.getHistoryStats()
      set({ stats })
    } catch (error) {
      // Stats are non-critical, don't show error
      console.error('Failed to fetch stats:', error)
    }
  },
  
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  
  reset: () => set({
    items: [],
    total: 0,
    offset: 0,
    hasMore: false,
    currentPage: 1,
    totalPages: 1,
    searchQuery: '',
    isLoading: false,
    isLoadingMore: false,
    error: null
  })
}))

// Subscribe to WebSocket transcription events for real-time updates
// This runs once when the module is loaded
let wsSubscribed = false

export function initHistoryWebSocket(): void {
  if (wsSubscribed) return
  wsSubscribed = true
  
  wsClient.onTranscription((event: TranscriptionEvent) => {
    // When a new transcription comes in via WebSocket, add it to the store
    const { items, searchQuery } = useHistoryStore.getState()
    
    // Create a TranscriptionRecord from the event data
    const record: TranscriptionRecord = {
      id: event.id,
      text: event.text,
      duration_ms: event.duration_ms,
      model_used: null,
      language: null,
      created_at: new Date().toISOString(),
      original_text: null,
      is_ai_enhanced: false
    }
    
    // Only add if not already in the list and no search filter is active
    const alreadyExists = items.some(item => item.id === record.id)
    
    if (!alreadyExists && !searchQuery) {
      useHistoryStore.getState().addItem(record)
    } else if (!alreadyExists && searchQuery) {
      // If search is active, we still increment total but don't add to visible items
      // User can clear search to see the new item
      useHistoryStore.setState(state => ({ total: state.total + 1 }))
    }
  })

  // Listen for updates (e.g. grammar correction)
  wsClient.onTranscriptionUpdate((event: TranscriptionEvent) => {
    const { items } = useHistoryStore.getState()
    const index = items.findIndex(item => item.id === event.id)
    
    if (index !== -1) {
      const updatedItems = [...items]
      // Update with new data (casting to any to access extra fields if needed)
      // The event from backend contains full record data
      const updateData = event as unknown as TranscriptionRecord
      
      updatedItems[index] = {
        ...updatedItems[index],
        text: event.text,
        original_text: updateData.original_text || updatedItems[index].original_text,
        is_ai_enhanced: updateData.is_ai_enhanced || updatedItems[index].is_ai_enhanced
      }
      
      useHistoryStore.setState({ items: updatedItems })
    }
  })
}

export default useHistoryStore
