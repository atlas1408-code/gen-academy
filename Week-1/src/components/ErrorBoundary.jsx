import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="rounded-xl p-6 text-center"
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--danger)',
          }}
        >
          <h3
            className="text-lg font-bold mb-2"
            style={{ color: 'var(--danger)' }}
          >
            Something went wrong
          </h3>
          <p
            className="text-sm mb-4"
            style={{ color: 'var(--text-secondary)' }}
          >
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer"
            style={{
              backgroundColor: 'var(--accent)',
              color: '#fff',
            }}
          >
            Try Again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
