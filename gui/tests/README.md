# SpeakEasy Frontend Tests

This directory contains the test suite for the SpeakEasy Electron GUI.

## Quick Start

```bash
# Run all tests
cd gui
npm test

# Run tests in watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

## Test Structure

```
src/renderer/src/
├── test/
│   ├── setup.ts              # Test setup and global mocks
│   └── utils.tsx             # Custom render and helpers
├── components/
│   └── __tests__/
│       ├── ModelSelector.test.tsx
│       ├── DeviceSelector.test.tsx
│       └── HotkeyInput.test.tsx
└── pages/
    └── __tests__/
        └── Settings.test.tsx
```

## Test Utilities

### Custom Render

Use the custom render function that includes all providers:

```tsx
import { render, screen } from '@renderer/test/utils'

it('renders component', () => {
  render(<MyComponent />)
  expect(screen.getByText('Hello')).toBeInTheDocument()
})
```

### Store Mocks

Create mock stores for testing:

```tsx
import { createMockSettingsStore } from '@renderer/test/utils'

const mockStore = createMockSettingsStore({
  settings: {
    model_name: 'large',
    // ... other overrides
  }
})
```

### WebSocket Mocks

Test WebSocket interactions:

```tsx
import { installMockWebSocket } from '@renderer/test/utils'

it('handles WebSocket messages', () => {
  const { instances, restore } = installMockWebSocket()
  
  // Trigger component that creates WebSocket
  render(<MyComponent />)
  
  // Simulate server message
  instances[0].simulateMessage({ type: 'status', data: 'connected' })
  
  // Verify UI update
  expect(screen.getByText('Connected')).toBeInTheDocument()
  
  restore()
})
```

### Async Helpers

Wait for store state changes:

```tsx
import { waitForState } from '@renderer/test/utils'
import { useAppStore } from '@renderer/store/app-store'

await waitForState(useAppStore, state => state.isRecording === true)
```

## Writing New Tests

### Basic Component Test

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@renderer/test/utils'
import userEvent from '@testing-library/user-event'
import { MyComponent } from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    
    render(<MyComponent onSubmit={onSubmit} />)
    
    await user.click(screen.getByRole('button', { name: /submit/i }))
    
    expect(onSubmit).toHaveBeenCalled()
  })
})
```

### Testing with Mocked API

The global `window.api` is mocked in `setup.ts`. Override specific methods:

```tsx
import { mockApi } from '@renderer/test/setup'

beforeEach(() => {
  mockApi.getSettings.mockResolvedValue({
    model_name: 'tiny',
    language: 'en',
  })
})
```

## Configuration

### vitest.config.ts

- Environment: `jsdom`
- Setup file: `src/renderer/src/test/setup.ts`
- Globals: enabled (no need to import `describe`, `it`, `expect`)
- Coverage: V8 provider

### Aliases

- `@renderer` → `src/renderer/src`

## Best Practices

1. **User-centric testing**: Test what users see and do
2. **Avoid implementation details**: Don't test internal state directly
3. **Use Testing Library queries**: Prefer `getByRole`, `getByText` over `getByTestId`
4. **Async handling**: Use `waitFor` or `findBy*` for async operations
5. **Mock at boundaries**: Mock API calls, not React components

## Troubleshooting

### "Cannot find module" errors

Check that the import path uses the `@renderer` alias:

```tsx
// Good
import { render } from '@renderer/test/utils'

// Bad - will fail
import { render } from '../test/utils'
```

### Test timeouts

Increase timeout for slow async operations:

```tsx
it('handles slow operation', async () => {
  // ...
}, 10000) // 10 second timeout
```

### Flaky tests

Use `waitFor` instead of fixed delays:

```tsx
// Good
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Bad - flaky
await new Promise(r => setTimeout(r, 1000))
expect(screen.getByText('Loaded')).toBeInTheDocument()
```
