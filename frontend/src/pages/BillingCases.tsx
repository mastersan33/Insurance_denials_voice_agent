import { useState, useRef, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Search, Upload, Trash2, ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react';
import { useBillingCases, useDeleteBillingCase, useBulkImportBillingCases } from '../hooks/useQueries';
import StatusBadge from '../components/StatusBadge';
import { TableRowSkeleton } from '../components/Skeleton';
import { formatDistanceToNow } from 'date-fns';

const STATUS_OPTIONS = ['', 'open', 'in_progress', 'appealing', 'resolved', 'closed'];
const PRIORITY_OPTIONS = ['', 'urgent', 'high', 'normal', 'low'];
const PAGE_SIZE = 25;

function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    urgent: 'bg-destructive/10 text-destructive',
    high: 'bg-warning/10 text-warning',
    normal: 'bg-muted text-muted-foreground',
    low: 'bg-muted/50 text-muted-foreground/60',
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${map[priority] ?? map.normal}`}>
      {priority}
    </span>
  );
}

interface CaseRowProps {
  c: import('../types/billingCase').BillingCase;
  onNavigate: (id: string) => void;
  onDelete: (id: string, name: string) => void;
  deleteIsPending: boolean;
}

const CaseRow = memo(function CaseRow({ c, onNavigate, onDelete, deleteIsPending }: CaseRowProps) {
  return (
    <tr
      onClick={() => onNavigate(c.id)}
      className="hover:bg-accent/50 cursor-pointer transition-colors"
    >
      <td className="px-4 py-3 font-medium text-foreground">{c.patient_name}</td>
      <td className="px-4 py-3 text-muted-foreground truncate max-w-[140px]">{c.payer_name}</td>
      <td className="px-4 py-3 font-mono text-xs text-foreground">{c.claim_number}</td>
      <td className="px-4 py-3 text-foreground">
        {c.amount_billed != null ? `$${c.amount_billed.toLocaleString()}` : '—'}
      </td>
      <td className="px-4 py-3"><PriorityBadge priority={c.priority} /></td>
      <td className="px-4 py-3"><StatusBadge status={c.status} size="sm" /></td>
      <td className="px-4 py-3 text-xs text-muted-foreground">
        {c.created_at ? formatDistanceToNow(new Date(c.created_at), { addSuffix: true }) : '—'}
      </td>
      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={() => onDelete(c.id, c.patient_name)}
          disabled={deleteIsPending}
          className="rounded p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
          title="Delete"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </td>
    </tr>
  );
});

export default function BillingCases() {
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [skip, setSkip] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useBillingCases({
    q: debouncedQ || undefined,
    status: status || undefined,
    priority: priority || undefined,
    skip,
    limit: PAGE_SIZE,
  });

  const deleteMutation = useDeleteBillingCase();
  const importMutation = useBulkImportBillingCases();

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1;

  function handleSearch(value: string) {
    setQ(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      setDebouncedQ(value);
      setSkip(0);
    }, 350);
  }

  function handleFilterChange(field: 'status' | 'priority', value: string) {
    if (field === 'status') setStatus(value);
    else setPriority(value);
    setSkip(0);
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete billing case for "${name}"? This cannot be undone.`)) return;
    await deleteMutation.mutateAsync(id);
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const result = await importMutation.mutateAsync(file) as { created: number; errors: string[] };
    const msg = `Imported ${result.created} cases.${result.errors.length ? `\n${result.errors.slice(0, 5).join('\n')}` : ''}`;
    alert(msg);
    e.target.value = '';
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Billing Cases</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{total} total</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importMutation.isPending}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors disabled:opacity-50"
          >
            <Upload className="h-3.5 w-3.5" />
            {importMutation.isPending ? 'Importing…' : 'Import CSV'}
          </button>
          <button
            onClick={() => navigate('/billing-cases/new')}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            New Case
          </button>
        </div>
      </div>

      {/* Search + Filter bar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search patient, payer, or claim number…"
            className="w-full rounded-lg border border-border bg-card pl-9 pr-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <button
          onClick={() => setShowFilters((p) => !p)}
          className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${showFilters ? 'border-primary bg-primary/5 text-primary' : 'border-border bg-card text-muted-foreground hover:text-foreground hover:bg-accent'}`}
        >
          <SlidersHorizontal className="h-3.5 w-3.5" />
          Filters
        </button>
      </div>

      {/* Expandable filters */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="flex items-center gap-3 overflow-hidden"
        >
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground whitespace-nowrap">Status:</label>
            <select
              value={status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="rounded-lg border border-border bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s || 'All'}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground whitespace-nowrap">Priority:</label>
            <select
              value={priority}
              onChange={(e) => handleFilterChange('priority', e.target.value)}
              className="rounded-lg border border-border bg-card px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              {PRIORITY_OPTIONS.map((p) => (
                <option key={p} value={p}>{p || 'All'}</option>
              ))}
            </select>
          </div>
          {(status || priority || debouncedQ) && (
            <button
              onClick={() => { setQ(''); setDebouncedQ(''); setStatus(''); setPriority(''); setSkip(0); }}
              className="text-xs text-destructive hover:underline"
            >
              Clear all
            </button>
          )}
        </motion.div>
      )}

      {/* Table */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Patient</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Payer</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Claim #</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Amount</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Priority</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Created</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => <TableRowSkeleton key={i} cols={8} />)
              : items.length === 0
              ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    No billing cases found
                  </td>
                </tr>
              )
              : items.map((c) => (
                <CaseRow
                  key={c.id}
                  c={c}
                  onNavigate={(id) => navigate(`/billing-cases/${id}`)}
                  onDelete={handleDelete}
                  deleteIsPending={deleteMutation.isPending}
                />
              ))
            }
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Showing {skip + 1}–{Math.min(skip + PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
              disabled={skip === 0}
              className="rounded-lg border border-border p-1.5 hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <span className="px-3">Page {currentPage} / {totalPages}</span>
            <button
              onClick={() => setSkip(skip + PAGE_SIZE)}
              disabled={skip + PAGE_SIZE >= total}
              className="rounded-lg border border-border p-1.5 hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
