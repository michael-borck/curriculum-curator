import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Top-level error boundary. A render/runtime error in any child would
 * otherwise unmount the whole tree and leave a blank white screen; this
 * catches it and shows a recoverable fallback instead.
 */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error('Unhandled UI error:', error, info.componentStack);
  }

  private handleReload = (): void => {
    this.setState({ error: null });
    window.location.reload();
  };

  override render(): ReactNode {
    if (this.state.error) {
      return (
        <div className='min-h-screen flex items-center justify-center bg-gray-50 p-6'>
          <div className='max-w-md w-full bg-white rounded-lg shadow p-6 text-center'>
            <h1 className='text-lg font-semibold text-gray-900 mb-2'>
              Something went wrong
            </h1>
            <p className='text-sm text-gray-600 mb-4'>
              The page hit an unexpected error. Reloading usually fixes it. If
              it keeps happening, please report it.
            </p>
            <p className='text-xs text-gray-400 mb-4 break-words'>
              {this.state.error.message}
            </p>
            <button
              type='button'
              onClick={this.handleReload}
              className='inline-flex items-center justify-center rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700'
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
