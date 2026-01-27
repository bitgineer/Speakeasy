# Phase 03: Security & Memory Leak Fixes

This phase addresses critical technical debt that affects security and stability. The insecure CORS configuration allows any origin to connect, memory leaks in audio processing can cause crashes over time, and input validation gaps create security vulnerabilities. Fixing these issues improves application reliability and security posture.

## Tasks

- [ ] Fix insecure CORS configuration:
  - Update `server.py` to use specific allowed origins instead of wildcard
  - Read allowed origins from environment variable or config file
  - For development mode, allow localhost on dynamic ports
  - For production, restrict to app:// protocol (Electron)
  - Add CORS origin validation middleware

- [ ] Fix audio buffer memory leak:
  - Add try-finally block in `start_recording()` to cleanup buffer on error
  - Ensure `_audio_buffer` is cleared when recording is cancelled
  - Add cleanup in `stop_recording()` even if an exception occurs
  - Add `cleanup()` method that explicitly clears the audio buffer
  - Add unit tests verifying buffer is cleared in all code paths

- [ ] Fix scroll event listener memory leak in Dashboard:
  - Update `Dashboard.tsx` to store the scroll handler reference in a useRef
  - Add useEffect cleanup function to remove event listener on unmount
  - Verify the listener is properly removed when navigating away

- [ ] Fix hotkey debouncing race condition:
  - Update `hotkey.ts` to add debouncing with proper lock mechanism
  - Add `isProcessing` flag to prevent multiple simultaneous recordings
  - Add minimum time between hotkey triggers (500ms)
  - Test rapid keypresses no longer trigger multiple recordings

- [ ] Add input validation to API endpoints:
  - Add Pydantic models for all request bodies with validation rules
  - Add string length validation (max lengths) for text inputs
  - Add range validation for numeric parameters (limit, offset, etc.)
  - Add regex validation for hotkey format
  - Return 400 Bad Request with clear error messages for invalid input

- [ ] Add rate limiting to API endpoints:
  - Install `slowapi` or implement simple rate limiting middleware
  - Add rate limit to transcription endpoints (max 10 per minute)
  - Add rate limit to settings updates (max 20 per minute)
  - Add rate limit to model loading (max 5 per minute)
  - Return 429 Too Many Requests with Retry-After header

- [ ] Fix temp file cleanup in Voxtral model:
  - Review `models.py` for temp file creation
  - Add proper temp file cleanup using tempfile.TemporaryDirectory or context manager
  - Add atexit handler to cleanup temp files on abnormal termination
  - Ensure all temp files use platform-appropriate temp directory

- [ ] Add request timeout handling:
  - Add timeout parameter to all async HTTP operations
  - Handle timeout exceptions gracefully with user-friendly error
  - Add WebSocket ping/pong with timeout detection
  - Reconnect WebSocket if no pong received within 30 seconds

- [ ] Fix global service pattern for testability:
  - Create dependency injection pattern for services
  - Add `ServiceContainer` class to manage service lifecycles
  - Update endpoints to receive services via dependency injection (FastAPI Depends)
  - Remove hardcoded global `transcriber`, `history`, `settings_service` references

- [ ] Add security headers:
  - Add `X-Content-Type-Options: nosniff` header
  - Add `X-Frame-Options: DENY` header
  - Add `Content-Security-Policy` header for WebSocket endpoint
  - Remove or disable unnecessary HTTP methods (TRACE, etc.)

- [ ] Add error boundary in React:
  - Create `ErrorBoundary.tsx` component wrapping the app
  - Show user-friendly error message with reload option
  - Log error details for debugging (not shown to user)
  - Add recovery suggestions based on error type

- [ ] Test all fixes:
  - Verify CORS rejects requests from unauthorized origins
  - Test audio buffer cleanup in error scenarios
  - Verify scroll event listener is removed on unmount
  - Test rapid hotkey presses are properly debounced
  - Test input validation rejects malformed requests
  - Test rate limiting triggers appropriately
