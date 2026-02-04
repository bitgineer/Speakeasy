import { render as rtlRender, screen, waitFor, fireEvent, act, RenderOptions, RenderResult } from '@testing-library/react'
import { ReactElement } from 'react'

// Re-export everything from testing-library
export { screen, waitFor, fireEvent, act }

// Custom render that can wrap with providers if needed
function render(ui: ReactElement, options?: RenderOptions): RenderResult {
  return rtlRender(ui, { ...options })
}

export { render }
