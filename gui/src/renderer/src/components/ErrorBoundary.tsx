import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Uncaught error:', error, errorInfo)
    this.setState({ errorInfo })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  handleTryAgain = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-surface-canvas flex flex-col items-center justify-center p-6 text-center select-none">
          <div className="max-w-md w-full space-y-8">
            {/* Icon / Visual */}
            <div className="relative mx-auto w-24 h-24 flex items-center justify-center">
              <div className="absolute inset-0 bg-danger-muted rounded-full animate-pulse"></div>
              <div className="absolute inset-0 border border-danger-border rounded-full"></div>
              <svg 
                className="w-10 h-10 text-danger-text relative z-10" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={1.5} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                />
              </svg>
            </div>

            {/* Text Content */}
            <div className="space-y-3">
              <h2 className="text-page font-semibold text-content-primary tracking-tight">
                Something went wrong
              </h2>
              <p className="text-content-secondary text-body leading-relaxed">
                The app hit a critical error. Reload it to continue.
              </p>
            </div>

            {/* Technical Details */}
            {this.state.error && (
              <div className="bg-surface-sunken rounded-panel p-4 text-left overflow-hidden border border-edge-subtle">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-danger-text"></div>
                  <p className="text-danger-text font-mono text-caption uppercase tracking-wider">Error details</p>
                </div>
                <code className="text-content-muted font-mono text-caption block whitespace-pre-wrap break-words opacity-80">
                  {this.state.error.toString()}
                </code>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
              <button
                onClick={this.handleTryAgain}
                className="px-6 py-2.5 rounded-control bg-surface-raised text-content-primary font-medium text-ui border border-edge-control hover:bg-surface-selected transition-colors duration-fast ease-standard"
              >
                Try again
              </button>
              <button
                onClick={this.handleReload}
                className="px-6 py-2.5 rounded-control bg-danger-muted text-danger-text font-medium text-ui border border-danger-border hover:opacity-90 transition-opacity duration-fast ease-standard"
              >
                Reload app
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
