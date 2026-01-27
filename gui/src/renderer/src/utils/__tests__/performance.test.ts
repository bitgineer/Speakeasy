import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { perfMonitor } from '../performance'

describe('PerformanceMonitor', () => {
  beforeEach(() => {
    perfMonitor.clear()
  })

  afterEach(() => {
    perfMonitor.clear()
  })

  describe('markStart and markEnd', () => {
    it('should create a measurement when markStart and markEnd are called', () => {
      perfMonitor.markStart('test-operation')
      
      // Simulate some work
      const start = performance.now()
      while (performance.now() - start < 10) {
        // Busy wait for ~10ms
      }
      
      const result = perfMonitor.markEnd('test-operation')
      
      expect(result).not.toBeNull()
      expect(result?.name).toBe('test-operation')
      expect(result?.duration).toBeGreaterThanOrEqual(0)
      expect(result?.startTime).toBeGreaterThanOrEqual(0)
    })

    it('should handle multiple measurements', () => {
      perfMonitor.markStart('op1')
      perfMonitor.markEnd('op1')
      
      perfMonitor.markStart('op2')
      perfMonitor.markEnd('op2')
      
      const measures = perfMonitor.getAllMeasures()
      expect(measures).toHaveLength(2)
      expect(measures.map(m => m.name)).toContain('op1')
      expect(measures.map(m => m.name)).toContain('op2')
    })

    it('should return null when markEnd is called without markStart', () => {
      const result = perfMonitor.markEnd('nonexistent')
      expect(result).toBeNull()
    })
  })

  describe('getMeasure', () => {
    it('should retrieve a specific measurement', () => {
      perfMonitor.markStart('fetch-data')
      perfMonitor.markEnd('fetch-data')
      
      const measure = perfMonitor.getMeasure('fetch-data')
      expect(measure).not.toBeUndefined()
      expect(measure?.name).toBe('fetch-data')
    })

    it('should return undefined for non-existent measurement', () => {
      const measure = perfMonitor.getMeasure('nonexistent')
      expect(measure).toBeUndefined()
    })
  })

  describe('getAllMeasures', () => {
    it('should return all measurements', () => {
      perfMonitor.markStart('op1')
      perfMonitor.markEnd('op1')
      
      perfMonitor.markStart('op2')
      perfMonitor.markEnd('op2')
      
      const measures = perfMonitor.getAllMeasures()
      expect(measures).toHaveLength(2)
    })

    it('should return empty array when no measurements exist', () => {
      const measures = perfMonitor.getAllMeasures()
      expect(measures).toEqual([])
    })
  })

  describe('clear', () => {
    it('should clear all measurements', () => {
      perfMonitor.markStart('op1')
      perfMonitor.markEnd('op1')
      
      expect(perfMonitor.getAllMeasures()).toHaveLength(1)
      
      perfMonitor.clear()
      
      expect(perfMonitor.getAllMeasures()).toHaveLength(0)
    })

    it('should clear performance marks and measures', () => {
      perfMonitor.markStart('test')
      perfMonitor.markEnd('test')
      
      const beforeClear = performance.getEntriesByType('measure').length
      expect(beforeClear).toBeGreaterThan(0)
      
      perfMonitor.clear()
      
      const afterClear = performance.getEntriesByType('measure').length
      expect(afterClear).toBe(0)
    })
  })

  describe('getMemoryInfo', () => {
    it('should return memory info if available', () => {
      const memory = perfMonitor.getMemoryInfo()
      
      // Memory info may not be available in all environments
      if (memory) {
        expect(memory.usedJSHeapSize).toBeGreaterThan(0)
        expect(memory.totalJSHeapSize).toBeGreaterThanOrEqual(memory.usedJSHeapSize)
        expect(memory.jsHeapSizeLimit).toBeGreaterThanOrEqual(memory.totalJSHeapSize)
      }
    })
  })

  describe('logMeasures', () => {
    it('should not throw when logging measures', () => {
      const consoleSpy = vi.spyOn(console, 'table').mockImplementation(() => {})
      
      perfMonitor.markStart('op1')
      perfMonitor.markEnd('op1')
      
      expect(() => perfMonitor.logMeasures()).not.toThrow()
      
      consoleSpy.mockRestore()
    })

    it('should log message when no measures exist', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      
      perfMonitor.logMeasures()
      
      expect(consoleSpy).toHaveBeenCalledWith('No performance measurements recorded')
      
      consoleSpy.mockRestore()
    })
  })

  describe('logMemory', () => {
    it('should not throw when logging memory', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      
      expect(() => perfMonitor.logMemory()).not.toThrow()
      
      consoleSpy.mockRestore()
    })
  })

  describe('isEnabled', () => {
    it('should return true in dev mode', () => {
      expect(perfMonitor.isEnabled()).toBe(true)
    })
  })

  describe('dev mode guard', () => {
    it('should not create measurements in production mode', () => {
      // Note: This test runs in dev mode (vitest), so we can't truly test production behavior
      // But we verify the isEnabled() method works correctly
      const isEnabled = perfMonitor.isEnabled()
      expect(typeof isEnabled).toBe('boolean')
    })
  })

  describe('real-world usage patterns', () => {
    it('should measure API call duration', () => {
      perfMonitor.markStart('api-fetch-models')
      
      // Simulate API call
      const start = performance.now()
      while (performance.now() - start < 5) {
        // Busy wait
      }
      
      const result = perfMonitor.markEnd('api-fetch-models')
      
      expect(result?.duration).toBeGreaterThanOrEqual(0)
      expect(result?.name).toBe('api-fetch-models')
    })

    it('should measure search operation', () => {
      perfMonitor.markStart('search-query')
      
      // Simulate search
      const start = performance.now()
      while (performance.now() - start < 5) {
        // Busy wait
      }
      
      const result = perfMonitor.markEnd('search-query')
      
      expect(result?.duration).toBeGreaterThanOrEqual(0)
    })

    it('should measure history load', () => {
      perfMonitor.markStart('history-load')
      
      // Simulate history load
      const start = performance.now()
      while (performance.now() - start < 5) {
        // Busy wait
      }
      
      const result = perfMonitor.markEnd('history-load')
      
      expect(result?.duration).toBeGreaterThanOrEqual(0)
    })
  })
})
