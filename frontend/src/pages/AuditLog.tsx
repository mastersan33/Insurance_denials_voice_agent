import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../services/endpoints';
import { formatDistanceToNow } from 'date-fns';
import { TableRowSkeleton } from '../components/Skeleton';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface AuditEntry {
  id: string;
  actor_id: string | null;
  actor_email: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  status: string;
  detail: string | null;
  created_at: string | null;
}

const ACTION_COLOR: Record<string, string> = {
  'billing_case.create': 'bg-success/10 text-success',
  'billing_case.delete': 'bg-destructive/10 text-destructive',
  'report.export': 'bg-info/10 text-info',
  success: 'bg-success/10 text-success',
  failure: 'bg-destructive/10 text-destructive',
};

const PAGE_SIZE = 50;

export default function AuditLog() {
  const [skip, setSkip] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState('');

  const { data, isLoading } = useQuery<{ items: AuditEntry[]; total: number }>({
    queryKey: ['audit-log', skip, actionFilter, resourceTypeFilter],
    queryFn: () =>
      auditApi
        .list({ action: actionFilter || undefined, resource_type: resourceTypeFilter || undefined, skip, limit: PAGE_SIZE })
        .then((r) => r.data as { items: AuditEntry[]; total: number }),
    staleTime: 30_000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Audit Log</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{total} entries</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setSkip(0); }}
            placeholder="Filter by action…"
            className="rounded-lg border border-border bg-card pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <input
          value={resourceTypeFilter}
          onChange={(e) => { setResourceTypeFilter(e.target.value); setSkip(0); }}
          placeholder="Resource type…"
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        {(actionFilter || resourceTypeFilter) && (
          <button onClick={() => { setActionFilter(''); setResourceTypeFilter(''); setSkip(0); }} className="text-xs text-destructive hover:underline">
            Clear
          </button>
        )}
      </div>

      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Time</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Actor</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Resource</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">IP</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 10 }).map((_, i) => <TableRowSkeleton key={i} cols={6} />)
              : items.length === 0
              ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-sm text-muted-foreground">
                    No audit entries found
                  </td>
                </tr>
              )
              : items.map((entry) => (
                <tr key={entry.id} className="hover:bg-accent/30 transition-colors">
                  <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                    {entry.created_at
                      ? formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-foreground">
                    {entry.actor_email ?? entry.actor_id ?? 'system'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${ACTION_COLOR[entry.action] ?? 'bg-muted text-muted-foreground'}`}>
                      {entry.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {entry.resource_type ? `${entry.resource_type}${entry.resource_id ? ` / ${entry.resource_id.slice(0, 8)}` : ''}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-muted-foreground">{entry.ip_address ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${entry.status === 'success' ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'}`}>
                      {entry.status}
                    </span>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{total} total entries</span>
          <div className="flex items-center gap-1">
            <button
              disabled={skip === 0}
              onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
              className="rounded p-1 hover:bg-accent disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-2">Page {currentPage} of {totalPages}</span>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setSkip(skip + PAGE_SIZE)}
              className="rounded p-1 hover:bg-accent disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
