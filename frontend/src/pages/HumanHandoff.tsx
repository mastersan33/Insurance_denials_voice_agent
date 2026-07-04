import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PhoneForwarded, CheckCircle, User } from 'lucide-react';
import { humanHandoffApi } from '../services/endpoints';
import StatusBadge from '../components/StatusBadge';
import { TableRowSkeleton } from '../components/Skeleton';
import { formatDistanceToNow } from 'date-fns';

interface Handoff {
  id: string;
  call_session_id: string;
  reason: string;
  context_summary: string | null;
  agent_phase: string | null;
  confidence_at_handoff: string | null;
  assigned_to: string | null;
  status: string;
  resolution_notes: string | null;
  created_at: string | null;
}

const STATUS_OPTIONS = ['', 'pending', 'assigned', 'resolved'];

export default function HumanHandoff() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('pending');
  const [resolving, setResolving] = useState<string | null>(null);
  const [notes, setNotes] = useState('');

  const { data: items = [], isLoading } = useQuery<Handoff[]>({
    queryKey: ['handoffs', statusFilter],
    queryFn: () =>
      humanHandoffApi.list({ status: statusFilter || undefined }).then((r) => r.data as Handoff[]),
    refetchInterval: 15_000,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof humanHandoffApi.update>[1] }) =>
      humanHandoffApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['handoffs'] });
      setResolving(null);
      setNotes('');
    },
  });

  const pendingCount = items.filter((h) => h.status === 'pending').length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Human Handoff</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Calls escalated by the AI agent requiring human review
          </p>
        </div>
        {pendingCount > 0 && (
          <span className="flex items-center gap-1.5 rounded-full bg-destructive/10 px-3 py-1 text-xs font-semibold text-destructive">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-destructive" />
            </span>
            {pendingCount} pending
          </span>
        )}
      </div>

      {/* Status filter */}
      <div className="flex items-center gap-2">
        {STATUS_OPTIONS.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-primary text-primary-foreground'
                : 'border border-border bg-card text-muted-foreground hover:text-foreground'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Reason</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Phase</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Confidence</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Time</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 4 }).map((_, i) => <TableRowSkeleton key={i} cols={6} />)
              : items.length === 0
              ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    <PhoneForwarded className="h-8 w-8 mx-auto mb-2 text-muted-foreground/40" />
                    No handoffs {statusFilter ? `with status "${statusFilter}"` : ''}
                  </td>
                </tr>
              )
              : items.map((h) => (
                <>
                  <tr key={h.id} className="hover:bg-accent/50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-foreground text-sm">{h.reason}</p>
                      {h.context_summary && (
                        <p className="text-xs text-muted-foreground mt-0.5 max-w-xs truncate">{h.context_summary}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-foreground">{h.agent_phase ?? '—'}</td>
                    <td className="px-4 py-3 text-sm text-foreground">
                      {h.confidence_at_handoff ? `${h.confidence_at_handoff}` : '—'}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={h.status} size="sm" /></td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {h.created_at ? formatDistanceToNow(new Date(h.created_at), { addSuffix: true }) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {h.status === 'pending' && (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => updateMutation.mutate({ id: h.id, data: { status: 'assigned' } })}
                            disabled={updateMutation.isPending}
                            className="flex items-center gap-1 text-xs text-info hover:underline disabled:opacity-50"
                          >
                            <User className="h-3 w-3" />
                            Assign to me
                          </button>
                          <button
                            onClick={() => setResolving(resolving === h.id ? null : h.id)}
                            className="flex items-center gap-1 text-xs text-success hover:underline"
                          >
                            <CheckCircle className="h-3 w-3" />
                            Resolve
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                  {resolving === h.id && (
                    <tr key={`${h.id}-resolve`} className="bg-muted/20">
                      <td colSpan={6} className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <input
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            placeholder="Resolution notes…"
                            className="flex-1 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                          <button
                            onClick={() => updateMutation.mutate({ id: h.id, data: { status: 'resolved', resolution_notes: notes || undefined } })}
                            disabled={updateMutation.isPending}
                            className="rounded-lg bg-success px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50 hover:bg-success/90 transition-colors"
                          >
                            {updateMutation.isPending ? 'Saving…' : 'Mark Resolved'}
                          </button>
                          <button onClick={() => setResolving(null)} className="text-xs text-muted-foreground hover:text-foreground">
                            Cancel
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
