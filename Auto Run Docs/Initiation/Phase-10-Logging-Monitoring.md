# Phase 10: Structured Logging and Monitoring

This phase implements comprehensive logging and monitoring to provide visibility into application behavior, facilitate debugging, and enable proactive issue detection. Structured logs make it easier to diagnose problems in production, while health metrics help ensure the application is running optimally.

## Tasks

- [ ] Set up structured logging on backend:
  - Install `python-logstash` or `structlog` for structured logging
  - Create `backend/speakeasy/utils/logging.py` module
  - Configure JSON-formatted logs with consistent fields (timestamp, level, module, message)
  - Add request ID tracking for correlating logs across async operations
  - Configure log levels: DEBUG for dev, INFO for production
  - Add log rotation to prevent disk space issues

- [ ] Add logging to critical paths:
  - Add logging to `transcriber.py`: state changes, model load, recording events
  - Add logging to `server.py`: API requests, errors, WebSocket events
  - Add logging to `history.py`: database operations, search queries
  - Add logging to `settings.py`: config changes
  - Add performance logging for slow operations (>1 second)

- [ ] Create frontend logging system:
  - Create `gui/src/renderer/src/utils/logging.ts` module
  - Implement remote log forwarding to backend
  - Add console.log interception for production builds
  - Add error boundary logging
  - Add user action logging (settings changes, recording start/stop)

- [ ] Add health metrics collection:
  - Create `backend/speakeasy/utils/metrics.py` module
  - Track: transcription count, total audio duration, error rates
  - Track: model load times, transcription times
  - Track: memory usage, CPU usage
  - Store metrics in SQLite for historical analysis
  - Add metrics retention policy (e.g., 30 days)

- [ ] Create health monitoring endpoints:
  - Add `GET /api/health/detailed` endpoint with system info
  - Add `GET /api/metrics` endpoint returning current metrics
  - Add `GET /api/metrics/history` with date range
  - Add `GET /api/logs` endpoint for retrieving recent logs
  - Add log level filtering to logs endpoint

- [ ] Create metrics dashboard UI:
  - Create `MetricsPage.tsx` new route
  - Display transcription statistics (count, total duration, avg accuracy)
  - Display system health (CPU, memory, disk usage)
  - Display error rate chart
  - Display model performance metrics
  - Add date range filter for historical data

- [ ] Add error tracking and alerting:
  - Create error aggregation service in backend
  - Track error frequency and types
  - Detect error spikes and potential issues
  - Add "Recent Errors" section to metrics dashboard
  - Add error notification toast for critical errors

- [ ] Add diagnostic tools:
  - Create `GET /api/diagnostics` endpoint
  - Return: Python version, dependency versions, GPU info, audio devices
  - Return: config values (sanitized), log file path, database path
  - Add "Download Diagnostics" button to Settings
  - Generate zip file with logs and diagnostics for support

- [ ] Implement log viewer UI:
  - Create `LogViewer.tsx` component
  - Add real-time log streaming via WebSocket
  - Add log level filtering
  - Add search across logs
  - Add timestamp highlighting
  - Add export logs functionality

- [ ] Add performance profiling:
  - Add cProfile-based profiling endpoint for development
  - Add memory profiling using `memory_profiler`
  - Add transcription timing breakdowns (recording, processing, inference)
  - Add slow query detection for database operations
  - Create performance report endpoint

- [ ] Configure production logging:
  - Set up log file in user data directory
  - Configure appropriate log levels for production
  - Add log cleanup/rotation to prevent disk fill
  - Add crash detection and reporting
  - Implement "safe mode" that starts with minimal features after crash

- [ ] Test logging and monitoring:
  - Verify logs are written correctly in all scenarios
  - Test log rotation works properly
  - Verify metrics are accurate
  - Test diagnostic export produces valid output
  - Verify log viewer shows real-time updates
  - Test performance overhead of logging is minimal

- [ ] Document logging and monitoring:
  - Create `docs/logging.md` explaining log architecture
  - Document log format and fields
  - Document how to enable debug logging
  - Document how to use metrics for troubleshooting
  - Add monitoring setup guide for power users
