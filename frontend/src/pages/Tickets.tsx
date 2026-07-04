import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import { ticketsApi } from '../services/endpoints';
import StatusBadge from '../components/StatusBadge';
import { TableRowSkeleton } from '../components/Skeleton';
import { formatDistanceToNow } from 'date-fns';

const STATUS_OPTIONS = ['', 'open', 'in_progress', 'resolved', 'closed'];
const PRIORITY_OPTIONS = ['', 'low', 'medium', 'high', 'urgent'];
const PAGE_SIZE = 25;

interface Ticket {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  category: string | null;
  assigned_to: string | null;
  resolution: string | null;
  billing_case_id: string | null;
  call_session_id: string | null;
  created_at: string | null;
}

function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    urgent: 'bg-destructive/10 text-destructive',
    high: 'bg-warning/10 text-warning',
    medium: 'bg-info/10 text-info',
    low: 'bg-muted text-muted-foreground',
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${map[priority] ?? map.medium}`}>
      {priority}
    </span>
  );
}

export default function Tickets() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [skip, setSkip] = useState(0);
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newPriority, setNewPriority] = useState('medium');
  const [resolving, setResolving] = useState<string | null>(null);
  const [resolution, setResolution] = useState('');

  const { data, isLoading } = useQuery<{ items?: Ticket[]; total?: number } | Ticket[]>({
    queryKey: ['tickets', statusFilter, skip],
    queryFn: () =>
      ticketsApi.list({ status: statusFilter || undefined, skip, limit: PAGE_SIZE }).then((r) => r.data),
    staleTime: 15_000,
  });

  // API returns list directly or paginated — handle both
  const items: Ticket[] = Array.isArray(data) ? data : (data as { items?: Ticket[] })?.items ?? [];
  const total = Array.isArray(data) ? items.length : (data as { total?: number })?.total ?? items.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1;

  const createMutation = useMutation({
    mutationFn: () =>
      ticketsApi.create({ title: newTitle, description: newDesc || undefined, priority: newPriority }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tickets'] });
      setShowNew(false);
      setNewTitle('');
      setNewDesc('');
      setNewPriority('medium');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { status?: string; resolution?: string } }) =>
      ticketsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tickets'] });
      setResolving(null);
      setResolution('');
    },
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Tickets</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{total} total</p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          New Ticket
        </button>
      </div>

      {/* New ticket form */}
      {showNew && (
        <div className="rounded-xl border border-border bg-card p-4 shadow-card space-y-3">
          <p className="text-sm font-semibold text-foreground">New Ticket</p>
          <input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Title *"
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <textarea
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)"
            rows={2}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
          />
          <div className="flex items-center gap-2">
            <select
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value)}
              className="rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:outline-none"
            >
              {PRIORITY_OPTIONS.filter(Boolean).map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!newTitle.trim() || createMutation.isPending}
              className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground disabled:opacity-50 hover:bg-primary/90 transition-colors"
            >
              {createMutation.isPending ? 'Creating…' : 'Create'}
            </button>
            <button
              onClick={() => setShowNew(false)}
              className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setSkip(0); }}
          className="rounded-lg border border-border bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s || 'All statuses'}</option>)}
        </select>
        {statusFilter && (
          <button onClick={() => { setStatusFilter(''); setSkip(0); }} className="text-xs text-destructive hover:underline">
            Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Title</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Priority</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Created</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={5} />)
              : items.length === 0
              ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    No tickets found
                  </td>
                </tr>
              )
              : items.map((t) => (
                <>
                  <tr key={t.id} className="hover:bg-accent/50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-foreground">{t.title}</p>
                      {t.description && (
                        <p className="text-xs text-muted-foreground truncate max-w-xs mt-0.5">{t.description}</p>
                      )}
                    </td>
                    <td className="px-4 py-3"><PriorityBadge priority={t.priority} /></td>
                    <td className="px-4 py-3"><StatusBadge status={t.status} size="sm" /></td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {t.created_at ? formatDistanceToNow(new Date(t.created_at), { addSuffix: true }) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {t.status !== 'resolved' && t.status !== 'closed' && (
                        <button
                          onClick={() => setResolving(resolving === t.id ? null : t.id)}
                          className="text-xs text-primary hover:underline"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                  {resolving === t.id && (
                    <tr key={`${t.id}-resolve`} className="bg-muted/20">
                      <td colSpan={5} className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <input
                            value={resolution}
                            onChange={(e) => setResolution(e.target.value)}
                            placeholder="Resolution notes…"
                            className="flex-1 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                          />
                          <button
                            onClick={() => updateMutation.mutate({ id: t.id, data: { status: 'resolved', resolution: resolution || undefined } })}
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Page {currentPage} of {totalPages}</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
              disabled={skip === 0}
              className="rounded-lg border border-border p-1.5 hover:bg-accent disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setSkip(skip + PAGE_SIZE)}
              disabled={currentPage >= totalPages}
              className="rounded-lg border border-border p-1.5 hover:bg-accent disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
