'use client';

import { useEffect, useState } from 'react';

import { AppShell } from '@/components/dashboard/AppShell';
import { ProtectedShell } from '@/components/dashboard/ProtectedShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/dashboard/States';
import { SurfaceCard } from '@/components/dashboard/SurfaceCard';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { useToast } from '@/components/ui/toast';
import { getErrorMessage, supportService } from '@/lib/api-service';
import { formatDateTime } from '@/lib/format';
import type { SupportTicket } from '@/lib/types';

export default function SupportPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ subject: '', message: '', priority: 'medium' });

  async function loadTickets() {
    try {
      setLoading(true);
      setError('');
      setTickets(await supportService.list());
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load support tickets.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTickets();
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.subject.trim() || !form.message.trim()) {
      showToast({ title: 'Support ticket incomplete', description: 'Subject and message are required.', variant: 'error' });
      return;
    }

    try {
      setSubmitting(true);
      await supportService.create({
        subject: form.subject.trim(),
        message: form.message.trim(),
        priority: form.priority,
      });
      setForm({ subject: '', message: '', priority: 'medium' });
      showToast({ title: 'Ticket submitted', description: 'Support request created successfully.', variant: 'success' });
      await loadTickets();
    } catch (err) {
      showToast({ title: 'Unable to submit ticket', description: getErrorMessage(err), variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ProtectedShell>
      <AppShell currentPage="support" title="Support" description="Submit support tickets and review responses from the backend support flow.">
        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <SurfaceCard>
            <h2 className="text-xl font-bold text-white">New Ticket</h2>
            <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
              <Input label="Subject" value={form.subject} onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))} />
              <Select
                label="Priority"
                value={form.priority}
                onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}
                options={[
                  { value: 'low', label: 'Low' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'high', label: 'High' },
                ]}
              />
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-slate-300">Message</span>
                <textarea
                  value={form.message}
                  onChange={(event) => setForm((current) => ({ ...current, message: event.target.value }))}
                  rows={6}
                  className="w-full rounded-xl border border-slate-700/80 bg-slate-900/60 px-4 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-emerald-500/80 focus:ring-2 focus:ring-emerald-500/20"
                />
              </label>
              <Button type="submit" isLoading={submitting}>Submit Ticket</Button>
            </form>
          </SurfaceCard>

          {loading ? (
            <LoadingState label="Loading tickets..." />
          ) : error ? (
            <ErrorState message={error} onRetry={() => void loadTickets()} />
          ) : !tickets.length ? (
            <EmptyState title="No tickets yet" message="Your submitted support requests will appear here." />
          ) : (
            <SurfaceCard>
              <h2 className="text-xl font-bold text-white">Ticket History</h2>
              <div className="mt-5 space-y-3">
                {tickets.map((ticket) => (
                  <div key={ticket.id} className="rounded-2xl border border-white/5 bg-[#17161a] p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="font-semibold text-white">{ticket.subject}</p>
                        <p className="mt-1 text-sm text-on-surface-variant">{ticket.message}</p>
                        <p className="mt-2 text-xs text-on-surface-variant">Created {formatDateTime(ticket.created_at)}</p>
                      </div>
                      <div className="text-sm">
                        <p className="font-semibold text-white">{ticket.status.toUpperCase()}</p>
                        <p className="mt-1 text-on-surface-variant">Priority {ticket.priority}</p>
                      </div>
                    </div>
                    {ticket.response ? <p className="mt-3 rounded-xl bg-[#121215] px-3 py-2 text-sm text-slate-200">{ticket.response}</p> : null}
                  </div>
                ))}
              </div>
            </SurfaceCard>
          )}
        </div>
      </AppShell>
    </ProtectedShell>
  );
}
