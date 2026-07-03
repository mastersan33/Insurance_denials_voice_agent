import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Phone, Edit2, Save, X } from 'lucide-react';
import { useBillingCase, useUpdateBillingCase, useCallJobs, useCreateAndCall } from '../hooks/useQueries';
import StatusBadge from '../components/StatusBadge';
import { Skeleton } from '../components/Skeleton';
import { formatDistanceToNow, format } from 'date-fns';

const STATUS_OPTIONS = ['open', 'in_progress', 'appealing', 'resolved', 'closed'];
const PRIORITY_OPTIONS = ['low', 'normal', 'high', 'urgent'];

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border last:border-0">
      <span className="w-36 flex-shrink-0 text-xs text-muted-foreground">{label}</span>
      <span className="text-sm text-foreground">{value ?? <span className="text-muted-foreground/50">—</span>}</span>
    </div>
  );
}

export default function BillingCaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Record<string, string>>({});

  const { data: caseData, isLoading } = useBillingCase(id!);
  const { data: callJobsData } = useCallJobs(undefined);
  const updateMutation = useUpdateBillingCase();
  const callMutation = useCreateAndCall();

  const allJobs = Array.isArray(callJobsData) ? callJobsData : [];
  const caseJobs = (allJobs as { billing_case_id?: string }[]).filter((j) => j.billing_case_id === id);

  function startEdit() {
    if (!caseData) return;
    setEditData({
      status: caseData.status,
      priority: caseData.priority,
      notes: caseData.notes ?? '',
      denial_code: caseData.denial_code ?? '',
      denial_reason: caseData.denial_reason ?? '',
    });
    setEditing(true);
  }

  async function saveEdit() {
    if (!id) return;
    await updateMutation.mutateAsync({
      id,
      data: {
        status: editData.status || undefined,
        priority: editData.priority || undefined,
        notes: editData.notes || undefined,
        denial_code: editData.denial_code || undefined,
        denial_reason: editData.denial_reason || undefined,
      },
    });
    setEditing(false);
  }

  async function handleCall() {
    if (!caseData) return;
    if (!caseData.payer_phone) {
      alert('No payer phone number on this case. Update it before calling.');
      return;
    }
    await callMutation.mutateAsync({
      patient_name: caseData.patient_name,
      payer_name: caseData.payer_name,
      payer_phone: caseData.payer_phone,
      claim_number: caseData.claim_number,
      denial_code: caseData.denial_code ?? '',
      denial_reason: caseData.denial_reason ?? '',
      amount_billed: caseData.amount_billed ?? 0,
      provider_name: caseData.provider_name ?? '',
      provider_npi: caseData.provider_npi ?? '',
    });
    alert('Call queued successfully!');
  }

  const inputCls = 'w-full rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30';

  if (isLoading) {
    return (
      <div className="max-w-4xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="flex h-48 items-center justify-center">
        <p className="text-muted-foreground">Case not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/billing-cases')}
            className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-foreground">{caseData.patient_name}</h1>
            <p className="text-xs text-muted-foreground mt-0.5 font-mono">{caseData.claim_number}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <button
                onClick={() => setEditing(false)}
                className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <X className="h-3.5 w-3.5" /> Cancel
              </button>
              <button
                onClick={saveEdit}
                disabled={updateMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Save className="h-3.5 w-3.5" />
                {updateMutation.isPending ? 'Saving…' : 'Save'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={startEdit}
                className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <Edit2 className="h-3.5 w-3.5" /> Edit
              </button>
              <button
                onClick={handleCall}
                disabled={callMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Phone className="h-3.5 w-3.5" />
                {callMutation.isPending ? 'Queuing…' : 'Start Call'}
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: case details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status + Priority (editable) */}
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Status & Priority</h2>
            {editing ? (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-muted-foreground">Status</label>
                  <select
                    value={editData.status}
                    onChange={(e) => setEditData((p) => ({ ...p, status: e.target.value }))}
                    className={inputCls}
                  >
                    {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-muted-foreground">Priority</label>
                  <select
                    value={editData.priority}
                    onChange={(e) => setEditData((p) => ({ ...p, priority: e.target.value }))}
                    className={inputCls}
                  >
                    {PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <StatusBadge status={caseData.status} dot />
                <span className="text-xs text-muted-foreground">•</span>
                <span className="text-xs font-semibold capitalize text-foreground">{caseData.priority} priority</span>
              </div>
            )}
          </section>

          {/* Patient & Payer */}
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Patient & Payer</h2>
            <InfoRow label="Patient Name" value={caseData.patient_name} />
            <InfoRow label="Date of Birth" value={caseData.patient_dob} />
            <InfoRow label="Subscriber ID" value={caseData.subscriber_id} />
            <InfoRow label="Payer" value={caseData.payer_name} />
            <InfoRow label="Payer Phone" value={caseData.payer_phone} />
          </section>

          {/* Claim details */}
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Claim Details</h2>
            <InfoRow label="Claim Number" value={<span className="font-mono text-xs">{caseData.claim_number}</span>} />
            <InfoRow label="Service Date" value={caseData.service_date} />
            <InfoRow label="CPT Codes" value={caseData.cpt_codes} />
            <InfoRow label="ICD-10 Codes" value={caseData.icd10_codes} />
            <InfoRow label="Amount Billed" value={caseData.amount_billed != null ? `$${caseData.amount_billed.toLocaleString()}` : null} />
            <InfoRow label="Provider" value={caseData.provider_name} />
            <InfoRow label="Provider NPI" value={caseData.provider_npi} />
          </section>

          {/* Denial info (editable) */}
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Denial Information</h2>
            {editing ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Denial Code</label>
                  <input
                    value={editData.denial_code}
                    onChange={(e) => setEditData((p) => ({ ...p, denial_code: e.target.value }))}
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Denial Reason</label>
                  <textarea
                    value={editData.denial_reason}
                    onChange={(e) => setEditData((p) => ({ ...p, denial_reason: e.target.value }))}
                    rows={3}
                    className={inputCls}
                  />
                </div>
              </div>
            ) : (
              <>
                <InfoRow label="Denial Code" value={caseData.denial_code} />
                <InfoRow label="Denial Reason" value={caseData.denial_reason} />
              </>
            )}
          </section>

          {/* Notes (editable) */}
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Notes</h2>
            {editing ? (
              <textarea
                value={editData.notes}
                onChange={(e) => setEditData((p) => ({ ...p, notes: e.target.value }))}
                rows={4}
                className={inputCls}
                placeholder="Add notes…"
              />
            ) : (
              <p className="text-sm text-foreground whitespace-pre-wrap">
                {caseData.notes || <span className="text-muted-foreground/50">No notes</span>}
              </p>
            )}
          </section>
        </div>

        {/* Right: call history */}
        <div className="space-y-4">
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Call History</h2>
            {caseJobs.length === 0 ? (
              <p className="text-xs text-muted-foreground">No calls yet</p>
            ) : (
              <div className="space-y-3">
                {(caseJobs as { id: string; status: string; outcome?: string | null; created_at?: string | null }[]).map((job) => (
                  <div
                    key={job.id}
                    onClick={() => navigate(`/calls/${job.id}`)}
                    className="rounded-lg border border-border p-3 hover:bg-accent cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <StatusBadge status={job.status} size="sm" />
                      {job.outcome && (
                        <span className="text-[10px] text-muted-foreground capitalize">{job.outcome.replace(/_/g, ' ')}</span>
                      )}
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      {job.created_at ? format(new Date(job.created_at), 'MMM d, yyyy HH:mm') : '—'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Meta */}
          <section className="rounded-xl border border-border bg-card p-5 shadow-card">
            <h2 className="text-sm font-semibold text-foreground mb-3">Meta</h2>
            <InfoRow
              label="Created"
              value={caseData.created_at ? formatDistanceToNow(new Date(caseData.created_at), { addSuffix: true }) : null}
            />
            <InfoRow
              label="Updated"
              value={caseData.updated_at ? formatDistanceToNow(new Date(caseData.updated_at), { addSuffix: true }) : null}
            />
          </section>
        </div>
      </div>
    </div>
  );
}
