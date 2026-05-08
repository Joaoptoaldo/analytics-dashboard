import type { ReactNode } from 'react'
import { Component } from 'react'

import { Button } from './ui/button'

type ErrorBoundaryProps = {
  children: ReactNode
}

type ErrorBoundaryState = {
  hasError: boolean
}

export class AppErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  override componentDidCatch(error: unknown) {
    console.error('Unhandled UI error', error)
    try {
      // Capture with Sentry if available (optional dependency)
      // @ts-ignore: optional dependency — import via Function to avoid bundler resolving optional package at build-time
      try {
        const dynImport = new Function('p', 'return import(p)')
        dynImport('@sentry/react')
          .then((Sentry: any) => {
            if (Sentry && typeof Sentry.captureException === 'function') {
              Sentry.captureException(error)
            }
          })
          .catch(() => { })
      } catch {
        // ignore
      }
    } catch {
      // ignore if dynamic import not supported
    }
  }

  private handleRetry = () => {
    this.setState({ hasError: false })
    window.location.reload()
  }

  override render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
          <div>
            <h1 className="text-2xl font-semibold">A interface encontrou um erro</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Atualize a página. Se o problema persistir, a aplicação precisa ser investigada.
            </p>
          </div>
          <Button onClick={this.handleRetry}>Recarregar</Button>
        </div>
      )
    }

    return this.props.children
  }
}