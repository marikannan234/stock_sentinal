'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ProtectedScreen } from '@/components/sentinel/protected-screen';
import { SentinelShell } from '@/components/sentinel/shell';
import { SurfaceCard } from '@/components/sentinel/primitives';
import { marketService, supportService } from '@/lib/api-service';
import type { LiveQuote, SupportTicket } from '@/lib/types';
import { formatDateLabel } from '@/lib/sentinel-utils';

export default function SupportPage() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [ribbon, setRibbon] = useState<LiveQuote[]>([]);

  async function loadTickets() {
    const data = await supportService.list();
    setTickets(data);
  }

  useEffect(() => {
    Promise.allSettled([loadTickets(), marketService.getLiveRibbon()]).then(([_, ribbonResult]) => {
      if (ribbonResult.status === 'fulfilled') setRibbon(ribbonResult.value.stocks.slice(0, 8));
    });
  }, []);

  const activeTickets = useMemo(() => tickets.filter((ticket) => ticket.status !== 'resolved').length, [tickets]);
  const resolvedTickets = useMemo(() => tickets.filter((ticket) => ticket.status === 'resolved').length, [tickets]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await supportService.create({ subject, message, priority: 'medium' });
    setSubject('');
    setMessage('');
    await loadTickets();
  }

  return (
    <ProtectedScreen>
      <SentinelShell title="Help Center" subtitle="Our sentinels are on standby 24/7. Submit a ticket for technical issues, account inquiries, or trading platform support." ribbon={ribbon}>
        <div className="grid grid-cols-12 gap-6">
          <SurfaceCard className="col-span-12 p-8 lg:col-span-5">
            <h2 className="mb-8 text-2xl font-bold text-white">Open New Ticket</h2>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Inquiry Subject</label>
                <input value={subject} onChange={(event) => setSubject(event.target.value)} className="w-full rounded-xl border border-white/5 bg-[var(--surface-lowest)] px-4 py-4 text-white outline-none" placeholder="e.g. Portfolio sync latency" />
              </div>
              <div>
                <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Detailed Message</label>
                <textarea value={message} onChange={(event) => setMessage(event.target.value)} className="h-40 w-full rounded-xl border border-white/5 bg-[var(--surface-lowest)] px-4 py-4 text-white outline-none" placeholder="Describe your issue in detail..." />
              </div>
              <button className="w-full rounded-2xl bg-[linear-gradient(135deg,#adc6ff_0%,#4d8eff_100%)] px-5 py-4 text-sm font-black text-[var(--on-primary)]">Submit Ticket</button>
            </form>
          </SurfaceCard>

          <div className="col-span-12 space-y-6 lg:col-span-7">
            <div className="grid grid-cols-2 gap-4">
              <SurfaceCard className="p-6"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Active Tickets</p><p className="font-mono text-4xl text-white">{String(activeTickets).padStart(2, '0')}</p></SurfaceCard>
              <SurfaceCard className="p-6"><p className="text-[10px] font-black uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">Resolved</p><p className="font-mono text-4xl text-white">{String(resolvedTickets).padStart(2, '0')}</p></SurfaceCard>
            </div>
            <SurfaceCard className="overflow-hidden">
              <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
                <h3 className="text-sm font-bold uppercase tracking-[0.18em] text-white">History</h3>
                <span className="text-[10px] font-black uppercase tracking-[0.18em] text-secondary">System Operational</span>
              </div>
              <table className="w-full">
                <thead className="text-[10px] uppercase tracking-[0.22em] text-[var(--on-surface-variant)]">
                  <tr>
                    <th className="px-6 py-4 text-left">Ticket ID</th>
                    <th className="px-6 py-4 text-left">Date</th>
                    <th className="px-6 py-4 text-left">Subject</th>
                    <th className="px-6 py-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((ticket) => (
                    <tr key={ticket.id} className="border-t border-white/5">
                      <td className="px-6 py-5 font-mono text-xs text-[var(--primary)]">#ST-{ticket.id}</td>
                      <td className="px-6 py-5 text-sm text-[var(--on-surface-variant)]">{formatDateLabel(ticket.created_at)}</td>
                      <td className="px-6 py-5 text-sm font-semibold text-white">{ticket.subject}</td>
                      <td className="px-6 py-5 text-right">
                        <span className={ticket.status === 'resolved' ? 'rounded-full bg-secondary/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-secondary' : 'rounded-full bg-primary/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--primary)]'}>
                          {ticket.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </SurfaceCard>
          </div>
        </div>
      </SentinelShell>
    </ProtectedScreen>
  );
}
