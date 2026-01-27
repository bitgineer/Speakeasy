# Phase 07: Performance Optimization

This phase improves application responsiveness and efficiency through caching, virtual scrolling, and optimized data fetching. Performance issues like slow history loading and UI sluggishness are addressed with proven techniques that make the app feel snappy and professional.

## Tasks

- [ ] Implement response caching in API client:
  - Add `cache` option to `apiClient` methods in `client.ts`
  - Implement in-memory cache with TTL for GET requests
  - Cache `/api/models` responses for 5 minutes
  - Cache `/api/settings` responses for 1 minute
  - Cache `/api/devices` responses for 2 minutes
  - Invalidate cache on relevant mutations (settings update, device change)

- [ ] Add virtual scrolling to history list:
  - Install `@tanstack/react-virtual` or similar virtualization library
  - Update `Dashboard.tsx` to use virtual list for history items
  - Configure item height estimation and measurement
  - Ensure infinite scroll still works with virtualization
  - Test performance with 1000+ history items

- [ ] Optimize history API queries:
  - Add database indexes to history SQLite tables (created_at, text)
  - Implement efficient search with FULLTEXT search if needed
  - Add `fields` parameter to allow partial record fetching
  - Implement projection to reduce payload size for list views
  - Add pagination cursor support for efficient deep pagination

- [ ] Debounce search input:
  - Update `Dashboard.tsx` search input with proper debounce
  - Use 300ms delay before triggering search
  - Cancel pending search queries on new input
  - Show "Searching..." indicator during debounce delay
  - Clear search results immediately on input clear

- [ ] Optimize WebSocket message handling:
  - Add message throttling to high-frequency WebSocket updates
  - Batch multiple updates into single messages when possible
  - Add message priority for critical vs. informational updates
  - Implement message queue with flush interval

- [ ] Lazy load route components:
  - Update `App.tsx` to use React.lazy() for page components
  - Add Suspense boundaries with loading fallbacks
  - Lazy load Settings page, Dashboard
  - Preload critical routes during idle time

- [ ] Optimize audio processing:
  - Review audio callback in `transcriber.py` for performance bottlenecks
  - Reduce audio buffer copy operations where possible
  - Consider processing audio in chunks for very long recordings
  - Add progress reporting during transcription for long audio

- [ ] Add code splitting:
  - Configure Vite to split vendor chunks
  - Split by route for faster initial load
  - Analyze bundle size with rollup-plugin-visualizer
  - Lazy load non-critical components (ModelSelector, DeviceSelector)

- [ ] Optimize renders with React.memo:
  - Add React.memo to `HistoryItem.tsx` to prevent unnecessary re-renders
  - Add React.memo to `ModelSelector.tsx`
  - Add React.memo to `DeviceSelector.tsx`
  - Use useCallback for all event handlers passed to children
  - Verify memo effectiveness with React DevTools Profiler

- [ ] Add performance monitoring:
  - Add performance.mark() for key operations (model load, transcription)
  - Log timing for critical user flows
  - Add memory usage tracking in development mode
  - Create performance dashboard endpoint for debugging

- [ ] Performance test and validate:
  - Test with 1000+ history items - should render smoothly
  - Test search on large dataset - should return <500ms
  - Test model switching - should feel responsive
  - Profile memory usage during extended use - should not grow unbounded
  - Measure and record baseline performance metrics
