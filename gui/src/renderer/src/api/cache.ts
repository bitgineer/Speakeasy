/**
 * API Response Cache
 * 
 * TTL-based in-memory cache for API responses.
 */

export interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

export interface Cache {
  get<T>(key: string): T | undefined
  set<T>(key: string, data: T, ttl: number): void
  invalidate(pattern: string): void
  clear(): void
}

export function createCache(): Cache {
  const store = new Map<string, CacheEntry<unknown>>()

  return {
    get<T>(key: string): T | undefined {
      const entry = store.get(key)
      if (!entry) return undefined

      const now = Date.now()
      const isExpired = now - entry.timestamp > entry.ttl

      if (isExpired) {
        store.delete(key)
        return undefined
      }

      return entry.data as T
    },

    set<T>(key: string, data: T, ttl: number): void {
      store.set(key, {
        data,
        timestamp: Date.now(),
        ttl
      })
    },

    invalidate(pattern: string): void {
      if (pattern.endsWith('*')) {
        const prefix = pattern.slice(0, -1)
        const keysToDelete: string[] = []

        for (const key of store.keys()) {
          if (key.startsWith(prefix)) {
            keysToDelete.push(key)
          }
        }

        keysToDelete.forEach(key => store.delete(key))
      } else {
        store.delete(pattern)
      }
    },

    clear(): void {
      store.clear()
    }
  }
}
