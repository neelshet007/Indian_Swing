import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '6px', margin: '12px 0' }}>
          <h4 style={{ color: 'var(--accent-red)', margin: '0 0 8px 0', fontSize: '0.9rem' }}>Component Render Failed</h4>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0, fontFamily: 'var(--font-mono)' }}>
            {this.state.error?.message || 'An unexpected rendering exception was caught.'}
          </p>
        </div>
      )
    }
    return this.props.children
  }
}
