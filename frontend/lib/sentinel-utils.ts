'use client';

export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ');
}

export function formatCurrency(value?: number | null, compact = false) {
  const safeValue = Number(value ?? 0);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 2,
    minimumFractionDigits: compact ? 0 : 2,
  }).format(safeValue);
}

export function formatPercent(value?: number | null) {
  const safeValue = Number(value ?? 0);
  const prefix = safeValue > 0 ? '+' : '';
  return `${prefix}${safeValue.toFixed(2)}%`;
}

export function formatCompactNumber(value?: number | null) {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(Number(value ?? 0));
}

export function formatDateLabel(value?: string | null) {
  if (!value) return 'Unknown';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatRelativeTime(value?: string | null) {
  if (!value) return 'Just now';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const deltaMinutes = Math.max(1, Math.round((Date.now() - date.getTime()) / 60000));
  if (deltaMinutes < 60) return `${deltaMinutes} min ago`;
  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours < 24) return `${deltaHours} hour${deltaHours === 1 ? '' : 's'} ago`;
  const deltaDays = Math.round(deltaHours / 24);
  return `${deltaDays} day${deltaDays === 1 ? '' : 's'} ago`;
}

export function getDeltaTone(value?: number | null) {
  if ((value ?? 0) > 0) return 'text-secondary';
  if ((value ?? 0) < 0) return 'text-tertiary';
  return 'text-on-surface-variant';
}

export function exportToCSV(data: any[], filename: string) {
  if (data.length === 0) return;
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
  ].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}
