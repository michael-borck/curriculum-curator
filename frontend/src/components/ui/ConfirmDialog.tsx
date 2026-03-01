import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
} from 'react';
import { AlertTriangle, Trash2, Info } from 'lucide-react';
import { Modal } from './Modal';

// ─── Types ───────────────────────────────────────────────────────────────────

type Variant = 'danger' | 'warning' | 'info';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel?: string | undefined;
  cancelLabel?: string | undefined;
  variant?: Variant | undefined;
}

// ─── Context ─────────────────────────────────────────────────────────────────

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmDialogContext = createContext<ConfirmFn | null>(null);

/**
 * Promise-based confirmation dialog hook.
 *
 * @example
 * const confirm = useConfirmDialog();
 * const ok = await confirm({ title: 'Delete?', message: 'This cannot be undone.' });
 * if (!ok) return;
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useConfirmDialog(): ConfirmFn {
  const fn = useContext(ConfirmDialogContext);
  if (!fn) {
    throw new Error(
      'useConfirmDialog must be used within a ConfirmDialogProvider'
    );
  }
  return fn;
}

// ─── Variant styling ─────────────────────────────────────────────────────────

const VARIANT_CONFIG: Record<
  Variant,
  { icon: typeof Trash2; iconBg: string; iconColor: string; btnColor: string }
> = {
  danger: {
    icon: Trash2,
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    btnColor:
      'bg-red-600 hover:bg-red-700 focus:ring-red-500 disabled:bg-red-400',
  },
  warning: {
    icon: AlertTriangle,
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    btnColor:
      'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500 disabled:bg-amber-400',
  },
  info: {
    icon: Info,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    btnColor:
      'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-400',
  },
};

// ─── Provider ────────────────────────────────────────────────────────────────

export function ConfirmDialogProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, setState] = useState<
    (ConfirmOptions & { open: boolean }) | null
  >(null);
  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  const confirm: ConfirmFn = useCallback((options: ConfirmOptions) => {
    return new Promise<boolean>(resolve => {
      resolveRef.current = resolve;
      setState({ ...options, open: true });
    });
  }, []);

  const handleClose = useCallback((result: boolean) => {
    resolveRef.current?.(result);
    resolveRef.current = null;
    setState(null);
  }, []);

  const variant = state?.variant ?? 'danger';
  const cfg = VARIANT_CONFIG[variant];
  const Icon = cfg.icon;

  return (
    <ConfirmDialogContext.Provider value={confirm}>
      {children}
      <Modal
        isOpen={state?.open ?? false}
        onClose={() => handleClose(false)}
        size='sm'
        showCloseButton={false}
        closeOnBackdrop={false}
      >
        {state && (
          <div className='flex flex-col items-center text-center'>
            <div
              className={`w-12 h-12 rounded-full ${cfg.iconBg} flex items-center justify-center mb-4`}
            >
              <Icon className={`w-6 h-6 ${cfg.iconColor}`} />
            </div>
            <h3 className='text-lg font-semibold text-gray-900 mb-2'>
              {state.title}
            </h3>
            <p className='text-sm text-gray-600 whitespace-pre-line mb-6'>
              {state.message}
            </p>
            <div className='flex gap-3 w-full'>
              <button
                type='button'
                onClick={() => handleClose(false)}
                className='flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400'
              >
                {state.cancelLabel ?? 'Cancel'}
              </button>
              <button
                type='button'
                onClick={() => handleClose(true)}
                className={`flex-1 px-4 py-2 text-sm font-medium text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 ${cfg.btnColor}`}
              >
                {state.confirmLabel ?? 'Confirm'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </ConfirmDialogContext.Provider>
  );
}
