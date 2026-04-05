'use client';

import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { tradeService, getErrorMessage } from '@/lib/api-service';
import { useToast } from '@/components/ui/toast';

const tradeTypeOptions = [
  { value: 'BUY', label: 'Buy' },
  { value: 'SELL', label: 'Sell' },
  { value: 'SHORT', label: 'Short' },
  { value: 'CLOSE', label: 'Close' },
];

const initialForm = {
  symbol: '',
  quantity: '1',
  entry_price: '',
  trade_type: 'BUY',
  notes: '',
};

export function QuickTradePanel({
  isOpen,
  onClose,
  onTradeCreated,
}: {
  isOpen: boolean;
  onClose: () => void;
  onTradeCreated?: () => Promise<void> | void;
}) {
  const { showToast } = useToast();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const validationMessage = useMemo(() => {
    if (!form.symbol.trim()) return 'Symbol is required.';
    if (!/^[A-Za-z.]{1,10}$/.test(form.symbol.trim())) return 'Enter a valid stock symbol.';
    if (Number(form.quantity) <= 0) return 'Quantity must be greater than zero.';
    if (Number(form.entry_price) <= 0) return 'Entry price must be greater than zero.';
    return '';
  }, [form.entry_price, form.quantity, form.symbol]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (validationMessage) {
      setError(validationMessage);
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      await tradeService.create({
        symbol: form.symbol.trim().toUpperCase(),
        quantity: Number(form.quantity),
        entry_price: Number(form.entry_price),
        trade_type: form.trade_type,
        notes: form.notes.trim() || undefined,
      });
      showToast({
        title: 'Trade placed',
        description: `${form.trade_type} order for ${form.symbol.trim().toUpperCase()} was submitted successfully.`,
        variant: 'success',
      });
      setForm(initialForm);
      await onTradeCreated?.();
      onClose();
    } catch (err) {
      const message = getErrorMessage(err, 'Unable to place trade.');
      setError(message);
      showToast({ title: 'Trade failed', description: message, variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={() => (submitting ? null : onClose())} title="Quick Trade">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input
          label="Symbol"
          placeholder="AAPL"
          value={form.symbol}
          onChange={(event) => setForm((current) => ({ ...current, symbol: event.target.value }))}
          disabled={submitting}
        />
        <div className="grid gap-4 md:grid-cols-2">
          <Input
            label="Quantity"
            type="number"
            min="1"
            step="1"
            value={form.quantity}
            onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))}
            disabled={submitting}
          />
          <Input
            label="Entry Price"
            type="number"
            min="0"
            step="0.01"
            value={form.entry_price}
            onChange={(event) => setForm((current) => ({ ...current, entry_price: event.target.value }))}
            disabled={submitting}
          />
        </div>
        <Select
          label="Trade Type"
          value={form.trade_type}
          onChange={(event) => setForm((current) => ({ ...current, trade_type: event.target.value }))}
          options={tradeTypeOptions}
        />
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-slate-300">Notes</span>
          <textarea
            value={form.notes}
            onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
            rows={3}
            disabled={submitting}
            className="w-full rounded-xl border border-slate-700/80 bg-slate-900/60 px-4 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-emerald-500/80 focus:ring-2 focus:ring-emerald-500/20"
            placeholder="Optional trade note"
          />
        </label>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <div className="flex gap-3">
          <Button type="button" variant="outline" onClick={onClose} disabled={submitting} fullWidth>
            Cancel
          </Button>
          <Button type="submit" isLoading={submitting} disabled={!!validationMessage && !error} fullWidth>
            Submit Trade
          </Button>
        </div>
      </form>
    </Modal>
  );
}
