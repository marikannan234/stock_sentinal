'use client';

export function LoadingState({ label = 'Loading data...' }: { label?: string }) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center gap-4 rounded-2xl border border-white/5 bg-[#201f22]">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-[#adc6ff] border-t-transparent" />
      <p className="text-sm text-on-surface-variant">{label}</p>
    </div>
  );
}

export function ErrorState({
  title = 'Unable to load data',
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-6">
      <h3 className="text-sm font-semibold text-red-200">{title}</h3>
      <p className="mt-2 text-sm text-red-100/80">{message}</p>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-4 rounded-xl border border-red-300/20 px-4 py-2 text-sm font-medium text-red-100 transition hover:bg-red-500/10"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title: string;
  message: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/5 bg-[#201f22] p-8 text-center">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm text-on-surface-variant">{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
