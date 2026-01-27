/**
 * History Store - Transcription history management
 * 
 * Manages the list of past transcriptions with search and pagination.
 */

import { create } from 'zustand'
import { apiClient } from '../api/client'
import type { TranscriptionRecord, HistoryStats } from '../api/types'

interface HistoryStore {
  // Data
  items: TranscriptionRecord[]
  total: number
  stats: HistoryStats | null
  
  // Pagination
  limit: number
  offset: number
  hasMore: boolean
  
  // Search
  searchQuery: string
  
  // Loading state
  isLoading: boolean
  isLoadingMore: boolean
  error: string | null
  
  // Actions
  fetchHistory: (reset?: boolean) => Promise<void>
  loadMore: () => Promise<void>
  
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
  
  searchQuery: '',
  
  isLoading: false,
  isLoadingMore: false,
  error: null,
  
  // Actions
  fetchHistory: async (reset = true) => {
    const { limit, searchQuery } = get()
    
    if (reset) {
      set({ isLoading: true, offset: 0, error: null })
    }
    
    try {
      const response = await apiClient.getHistory({
        limit,
        offset: reset ? 0 : get().offset,
        search: searchQuery || undefined
      })
      
      set({
        items: reset ? response.items : [...get().items, ...response.items],
        total: response.total,
        hasMore: response.items.length === limit,
        offset: reset ? response.items.length : get().offset + response.items.length,
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
    const { hasMore, isLoadingMore } = get()
    if (!hasMore || isLoadingMore) return
    
    set({ isLoadingMore: true })
    
    try {
      const { limit, offset, searchQuery, items } = get()
      const response = await apiClient.getHistory({
        limit,
        offset,
        search: searchQuery || undefined
      })
      
      set({
        items: [...items, ...response.items],
        total: response.total,
        hasMore: response.items.length === limit,
        offset: offset + response.items.length,
        isLoadingMore: false
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load more history',
        isLoadingMore: false
      })
    }
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
    searchQuery: '',
    isLoading: false,
    isLoadingMore: false,
    error: null
  })
}))

export default useHistoryStore
