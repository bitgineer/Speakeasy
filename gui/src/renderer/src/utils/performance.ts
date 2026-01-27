/**
 * Performance Monitoring Utilities
 * 
 * Provides dev-mode-only performance measurement using the Performance API.
 * Includes marking, measuring, and memory tracking capabilities.
 * 
 * All functionality is guarded by import.meta.env.DEV to ensure zero overhead in production.
 */

interface MeasureResult {
  name: string
  duration: number
  startTime: number
}

interface MemoryInfo {
  usedJSHeapSize: number
  totalJSHeapSize: number
  jsHeapSizeLimit: number
}

/**
 * Performance monitoring utility for development mode
 * 
 * Usage:
 * ```
 * perfMonitor.markStart('history-fetch')
 * // ... do work ...
 * perfMonitor.markEnd('history-fetch')
 * console.log(perfMonitor.getMeasure('history-fetch')) // { duration: 123, ... }
 * ```
 */
class PerformanceMonitor {
  private measures: Map<string, MeasureResult> = new Map()
  private isDevMode = (import.meta as any).env?.DEV ?? false

  /**
   * Mark the start of an operation
   */
  markStart(name: string): void {
    if (!this.isDevMode) return

    const markName = `${name}-start`
    performance.mark(markName)
  }

  /**
   * Mark the end of an operation and create a measurement
   */
  markEnd(name: string): MeasureResult | null {
    if (!this.isDevMode) return null

    const startMarkName = `${name}-start`
    const endMarkName = `${name}-end`

    try {
      performance.mark(endMarkName)
      performance.measure(name, startMarkName, endMarkName)

      const measure = performance.getEntriesByName(name, 'measure')[0] as PerformanceMeasure
      const result: MeasureResult = {
        name,
        duration: measure.duration,
        startTime: measure.startTime,
      }

      this.measures.set(name, result)
      return result
    } catch (error) {
      console.warn(`Failed to measure ${name}:`, error)
      return null
    }
  }

  /**
   * Get a specific measurement by name
   */
  getMeasure(name: string): MeasureResult | undefined {
    if (!this.isDevMode) return undefined
    return this.measures.get(name)
  }

  /**
   * Get all measurements
   */
  getAllMeasures(): MeasureResult[] {
    if (!this.isDevMode) return []
    return Array.from(this.measures.values())
  }

  /**
   * Log all measurements to console as a table
   */
  logMeasures(): void {
    if (!this.isDevMode) return

    const measures = this.getAllMeasures()
    if (measures.length === 0) {
      console.log('No performance measurements recorded')
      return
    }

    console.table(
      measures.map((m) => ({
        Operation: m.name,
        'Duration (ms)': m.duration.toFixed(2),
        'Start Time (ms)': m.startTime.toFixed(2),
      }))
    )
  }

  /**
   * Get current memory usage (Chrome/Chromium only)
   */
  getMemoryInfo(): MemoryInfo | null {
    if (!this.isDevMode) return null

    const perf = performance as any
    if (!perf.memory) {
      console.warn('performance.memory not available (Chrome/Chromium only)')
      return null
    }

    return {
      usedJSHeapSize: perf.memory.usedJSHeapSize,
      totalJSHeapSize: perf.memory.totalJSHeapSize,
      jsHeapSizeLimit: perf.memory.jsHeapSizeLimit,
    }
  }

  /**
   * Log memory usage to console
   */
  logMemory(): void {
    if (!this.isDevMode) return

    const memory = this.getMemoryInfo()
    if (!memory) return

    const usedMB = (memory.usedJSHeapSize / 1024 / 1024).toFixed(2)
    const totalMB = (memory.totalJSHeapSize / 1024 / 1024).toFixed(2)
    const limitMB = (memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)

    console.log(
      `Memory: ${usedMB}MB used / ${totalMB}MB allocated / ${limitMB}MB limit`
    )
  }

  /**
   * Clear all measurements
   */
  clear(): void {
    if (!this.isDevMode) return

    this.measures.clear()
    performance.clearMarks()
    performance.clearMeasures()
  }

  /**
   * Check if dev mode is enabled
   */
  isEnabled(): boolean {
    return this.isDevMode
  }
}

// Export singleton instance
export const perfMonitor = new PerformanceMonitor()

// Export type for external use
export type { MeasureResult, MemoryInfo }
