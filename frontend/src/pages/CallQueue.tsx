import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, Plus, X, RefreshCw, Ban, Pause, Play, RotateCcw } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { TableRowSkeleton } from '../components/Skeleton';
import {
  useCallJobs, useTriggerCall, useCancelCallJob, useCreateAndCall,
  usePauseQueue, useResumeQueue, useCancelAllQueue, useRetryFailed,
  type NewCallPayload,
} from '../hooks/useQueries';
import { formatDistanceToNow } from 'date-fns';

const DENIAL_CODES = ['CO-97', 'CO-4', 'CO-16', 'CO-50', 'CO-22'];
const STATUS_TABS = ['all', 'pending', 'in_progress', 'completed', 'failed', 'cancelled'];

const EMPTY_FORM: NewCallPayload = {
  patient_name: '',
  payer_name: '',
  payer_phone: '',
  claim_number: '',
  denial_code: 'CO-97',
  denial_reason: '',
  amount_billed: 0,
  provider_name: '',
  provider_npi: '',
};

function priorityLabel(p: number) {
  if (p >= 10) return { text: 'Urgent', cls: 'text-destructive' };
  if (p >= 5) return { text: 'High', cls: 'text-warning' };
  if (p >= 1) return { text: 'Normal', cls: 'text-foreground' };
  return { text: 'Low', cls: 'text-muted-foreground' };
}

type Job = {
  id: string;
  phone_number: string;
  status: string;
  priority: number;
  attempt_count: number;
  max_attempts: number;
  outcome: string | null;
  scheduled_at: string | null;
  created_at: string | null;
  billing_case_id: string;
};

export default function CallQueue() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<NewCallPayload>(EMPTY_FORM);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data: jobs, isLoading, refetch, isFetching } = useCallJobs(activeTab === 'all' ? undefined : activeTab);
  const trigger = useTriggerCall();
  const cancelJob = useCancelCallJob();
  const createAndCall = useCreateAndCall();
  const pauseQ = usePauseQueue();
  const resumeQ = useResumeQueue();
  const cancelAllQ = useCancelAllQueue();
  const retryQ = useRetryFailed();

  const allJobs: Job[] = Array.isArray(jobs) ? jobs as Job[] : [];

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === 'amount_billed' ? parseFloat(value) || 0 : value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      await createAndCall.mutateAsync(form);
      setShowModal(false);
      setForm(EMPTY_FORM);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message || 'Failed to place call.');
    }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === allJobs.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(allJobs.map((j) => j.id)));
    }
  }

  const inputCls = 'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30';

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Call Queue</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{allJobs.length} jobs</p>
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <span className="text-xs text-muted-foreground">
              {selected.size} selected
            </span>
          )}
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => { if (confirm('Pause all pending jobs?')) pauseQ.mutate(); }}
            disabled={pauseQ.isPending}
            title="Pause queue"
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-warning hover:bg-accent disabled:opacity-50 transition-colors"
          >
            <Pause className="h-3.5 w-3.5" /> Pause
          </button>
          <button
            onClick={() => resumeQ.mutate()}
            disabled={resumeQ.isPending}
            title="Resume paused jobs"
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-success hover:bg-accent disabled:opacity-50 transition-colors"
          >
            <Play className="h-3.5 w-3.5" /> Resume
          </button>
          <button
            onClick={() => { if (confirm('Cancel ALL pending jobs? This cannot be undone.')) cancelAllQ.mutate(); }}
            disabled={cancelAllQ.isPending}
            title="Cancel all pending"
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-destructive hover:bg-accent disabled:opacity-50 transition-colors"
          >
            <Ban className="h-3.5 w-3.5" /> Cancel All
          </button>
          <button
            onClick={() => { if (confirm('Retry all failed jobs?')) retryQ.mutate(); }}
            disabled={retryQ.isPending}
            title="Retry failed"
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-info hover:bg-accent disabled:opacity-50 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Retry Failed
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            New Call
          </button>
        </div>
      </div>

      {/* Status tabs */}
      <div className="flex items-center gap-1 border-b border-border">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => { setActiveTab(tab); setSelected(new Set()); }}
            className={`px-3 py-2 text-xs font-medium capitalize transition-colors border-b-2 -mb-px ${
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab === 'all' ? 'All' : tab.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 w-8">
                <input
                  type="checkbox"
                  checked={allJobs.length > 0 && selected.size === allJobs.length}
                  onChange={toggleAll}
                  className="rounded border-border"
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Phone</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Priority</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Attempts</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Outcome</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Queued</th>
              <th className="px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wide text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => <TableRowSkeleton key={i} cols={8} />)
              : allJobs.length === 0
              ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    No call jobs found
                  </td>
                </tr>
              )
              : allJobs.map((job) => {
                const pl = priorityLabel(job.priority);
                return (
                  <tr
                    key={job.id}
                    onClick={() => navigate(`/calls/${job.id}`)}
                    className="hover:bg-accent/50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected.has(job.id)}
                        onChange={() => toggleSelect(job.id)}
                        className="rounded border-border"
                      />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-foreground">{job.phone_number}</td>
                    <td className="px-4 py-3"><StatusBadge status={job.status} size="sm" dot /></td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold ${pl.cls}`}>{pl.text}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {job.attempt_count} / {job.max_attempts}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground capitalize">
                      {job.outcome ? job.outcome.replace(/_/g, ' ') : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {job.created_at ? formatDistanceToNow(new Date(job.created_at), { addSuffix: true }) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1">
                        {(job.status === 'pending' || job.status === 'failed') && (
                          <button
                            onClick={() => trigger.mutate(job.id)}
                            disabled={trigger.isPending}
                            className="flex items-center gap-1 rounded-lg bg-primary/10 px-2.5 py-1.5 text-[10px] font-semibold text-primary hover:bg-primary/20 disabled:opacity-50 transition-colors"
                            title="Trigger call"
                          >
                            <Phone className="h-3 w-3" />
                            {trigger.isPending ? '…' : 'Call'}
                          </button>
                        )}
                        {job.status === 'failed' && job.attempt_count < job.max_attempts && (
                          <button
                            onClick={() => trigger.mutate(job.id)}
                            disabled={trigger.isPending}
                            className="flex items-center gap-1 rounded-lg bg-warning/10 px-2.5 py-1.5 text-[10px] font-semibold text-warning hover:bg-warning/20 disabled:opacity-50 transition-colors"
                            title="Retry"
                          >
                            <RefreshCw className="h-3 w-3" />
                            Retry
                          </button>
                        )}
                        {job.status === 'pending' && (
                          <button
                            onClick={() => cancelJob.mutate(job.id)}
                            disabled={cancelJob.isPending}
                            className="flex items-center gap-1 rounded-lg bg-destructive/10 px-2.5 py-1.5 text-[10px] font-semibold text-destructive hover:bg-destructive/20 disabled:opacity-50 transition-colors"
                            title="Cancel"
                          >
                            <Ban className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {/* New Call Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card shadow-dialog">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <h3 className="text-base font-semibold text-foreground">New Outbound Call</h3>
              <button
                onClick={() => { setShowModal(false); setError(''); }}
                className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { name: 'patient_name', label: 'Patient Name', type: 'text', required: true },
                  { name: 'payer_name', label: 'Payer Name', type: 'text', required: true },
                  { name: 'payer_phone', label: 'Payer Phone', type: 'tel', placeholder: '+1 800 555 0100', required: true },
                  { name: 'claim_number', label: 'Claim Number', type: 'text', required: true },
                  { name: 'amount_billed', label: 'Amount Billed ($)', type: 'number', required: true },
                  { name: 'provider_name', label: 'Provider Name', type: 'text', required: true },
                  { name: 'provider_npi', label: 'Provider NPI', type: 'text', required: true },
                ].map((field) => (
                  <div key={field.name}>
                    <label className="block text-xs font-medium text-foreground mb-1">
                      {field.label}{field.required && <span className="text-destructive ml-0.5">*</span>}
                    </label>
                    <input
                      name={field.name}
                      type={field.type}
                      placeholder={field.placeholder}
                      value={String((form as unknown as Record<string, unknown>)[field.name] ?? '')}
                      onChange={handleChange}
                      required={field.required}
                      className={inputCls}
                    />
                  </div>
                ))}
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">Denial Code</label>
                  <select name="denial_code" value={form.denial_code} onChange={handleChange} className={inputCls}>
                    {DENIAL_CODES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Denial Reason <span className="text-destructive">*</span>
                </label>
                <input name="denial_reason" value={form.denial_reason} onChange={handleChange} required className={inputCls} />
              </div>
              {error && <p className="text-xs text-destructive">{error}</p>}
              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setError(''); }}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createAndCall.isPending}
                  className="flex items-center gap-1.5 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Phone className="h-3.5 w-3.5" />
                  {createAndCall.isPending ? 'Placing…' : 'Place Call'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
