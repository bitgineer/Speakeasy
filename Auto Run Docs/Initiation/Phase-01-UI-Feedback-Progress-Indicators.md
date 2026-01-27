# Phase 01: UI Feedback & Progress Indicators

This phase delivers visible, tangible improvements to the user experience by adding responsive feedback throughout the application. By the end of this phase, users will see save status indicators, loading states for all async operations, and general UI responsiveness improvements - making the application feel significantly more polished and reliable.

## Tasks

- [ ] Add save status feedback to settings page:
  - Create `SaveStatusIndicator.tsx` component with three states: unsaved, saving, and saved
  - Add a visual checkmark indicator that appears when settings are successfully saved (auto-fades after 3 seconds)
  - Add "unsaved changes" warning when navigating away with pending changes
  - Update the save button to show loading spinner during save operation

- [ ] Add loading states to all model operations:
  - Update `ModelSelector.tsx` to show loading overlay while models are being fetched
  - Add loading state to model load operation with "Loading model..." message
  - Update `useSettingsStore.ts` to track `isLoadingModel` state
  - Add disabled state styling to model dropdowns during loading

- [ ] Add async operation feedback to app store:
  - Extend `app-store.ts` with new states: `isTranscribing`, `isSaving`
  - Add `lastOperationStatus` property to track success/failure of operations
  - Update `RecordingIndicator.tsx` to show "Transcribing..." state after recording stops
  - Add success toast notification when transcription completes

- [ ] Add loading skeletons to history page:
  - Create `HistoryItemSkeleton.tsx` component matching the history item layout
  - Update `Dashboard.tsx` to show skeleton loaders during initial fetch
  - Add skeleton animation to search results loading state
  - Ensure skeletons match the exact layout of actual history items

- [ ] Add progress feedback to device operations:
  - Update `DeviceSelector.tsx` to show loading state while switching devices
  - Add "Connecting..." indicator when device is being changed
  - Add error boundary for device connection failures

- [ ] Implement toast notification system:
  - Create `ToastProvider.tsx` context component for managing notifications
  - Create `Toast.tsx` component with success/error/warning variants
  - Add `useToast.ts` hook for triggering notifications from any component
  - Integrate toast notifications into: settings save, model load, device change, transcription errors
  - Add toasts to `App.tsx` as a fixed overlay in top-right corner

- [ ] Add responsive feedback throughout history operations:
  - Update `HistoryItem.tsx` to show loading state during delete operation
  - Add "All changes saved" indicator after delete operations
  - Add loading spinner to "load more" button at bottom of history
  - Update search to show "Searching..." indicator during debounced queries

- [ ] Add operation status to backend connection:
  - Update `useBackendStatus.ts` hook to show connection state more prominently
  - Add "Reconnecting..." indicator when backend connection is lost
  - Add visual indicator in status bar when backend is disconnected
  - Implement automatic reconnection with visual feedback

- [ ] Test all UI feedback states:
  - Manually trigger each async operation and verify feedback appears
  - Test save status indicator appears and fades correctly
  - Verify loading states appear on model operations, device changes
  - Confirm toast notifications appear for all error conditions
  - Test that "unsaved changes" warning appears when appropriate

- [ ] Add keyboard shortcuts for common actions:
  - Add Ctrl/Cmd+S shortcut to save settings (from any page)
  - Add Escape key to close modals/toasts
  - Add visual indicator when shortcut is triggered
  - Document shortcuts in an accessible help tooltip
