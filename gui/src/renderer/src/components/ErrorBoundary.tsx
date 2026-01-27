import React, { Component, ErrorInfo, ReactNode } from 'react'

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
        <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-6 text-center select-none">
          <div className="max-w-md w-full space-y-8">
            {/* Icon / Visual */}
            <div className="relative mx-auto w-24 h-24 flex items-center justify-center">
              <div className="absolute inset-0 bg-red-500/10 rounded-full animate-pulse"></div>
              <div className="absolute inset-0 border border-red-500/20 rounded-full"></div>
              <svg 
                className="w-10 h-10 text-red-500 relative z-10" 
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
              <h2 className="text-2xl font-semibold text-white tracking-tight">
                System Malfunction
              </h2>
              <p className="text-gray-400 text-base leading-relaxed">
                The application encountered a critical error and needs to restart.
              </p>
            </div>

            {/* Technical Details */}
            {this.state.error && (
              <div className="bg-black/40 rounded-lg p-4 text-left overflow-hidden border border-gray-800/50 backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                  <p className="text-red-400/80 font-mono text-xs uppercase tracking-wider">Error Trace</p>
                </div>
                <code className="text-gray-500 font-mono text-xs block whitespace-pre-wrap break-words opacity-80">
                  {this.state.error.toString()}
                </code>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
              <button
                onClick={this.handleTryAgain}
                className="px-6 py-2.5 rounded-lg bg-gray-800 text-gray-200 font-medium text-sm hover:bg-gray-700 hover:text-white transition-all duration-200 border border-gray-700 hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500/50 focus:ring-offset-2 focus:ring-offset-gray-900"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="px-6 py-2.5 rounded-lg bg-red-500/10 text-red-400 font-medium text-sm hover:bg-red-500/20 hover:text-red-300 transition-all duration-200 border border-red-500/20 hover:border-red-500/30 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:ring-offset-2 focus:ring-offset-gray-900"
              >
                Reload System
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
