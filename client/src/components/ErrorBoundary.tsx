// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(error: unknown): State {
    const message = error instanceof Error ? error.message : 'An unexpected error occurred.'
    return { hasError: true, message }
  }

  componentDidCatch(error: unknown, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center p-8">
          <div className="max-w-md space-y-4 text-center">
            <h1 className="text-xl font-semibold">Something went wrong</h1>
            <p className="text-muted-foreground text-sm">{this.state.message}</p>
            <button
              className="text-primary text-sm underline"
              onClick={() => this.setState({ hasError: false, message: '' })}
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
