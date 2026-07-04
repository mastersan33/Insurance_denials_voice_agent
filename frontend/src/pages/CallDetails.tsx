import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, MessageSquare } from 'lucide-react';
import { callsApi } from '../services/endpoints';
import StatusBadge from '../components/StatusBadge';
import { Skeleton } from '../components/Skeleton';
import { format } from 'date-fns';

export default function CallDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: call, isLoading } = useQuery({
    queryKey: ['call', id],
    queryFn: () => callsApi.get(id!).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="rounded-xl border border-border bg-card p-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
        </div>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-muted-foreground">Call session not found</p>
        <button onClick={() => navigate(-1)} className="text-xs text-primary hover:underline">Go back</button>
      </div>
    );
  }

  function fmt(val: unknown) {
    if (val == null) return '—';
    return String(val);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="rounded-lg border border-border p-1.5 hover:bg-accent transition-colors"
        >
          <ArrowLeft className="h-4 w-4 text-muted-foreground" />
        </button>
        <h1 className="text-xl font-bold text-foreground">Call Details</h1>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 shadow-card">
        <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">
          {([
            ['Session ID', <span className="font-mono text-xs">{fmt(call.id)}</span>],
            ['Status', <StatusBadge status={call.status} size="sm" />],
            ['To Number', fmt(call.to_number)],
            ['From Number', fmt(call.from_number)],
            ['Phase', <span className="capitalize">{fmt(call.agent_phase)}</span>],
            ['Confidence', call.confidence_score != null ? `${Math.round(call.confidence_score * 100)}%` : '—'],
            ['Duration', call.duration_seconds != null ? `${call.duration_seconds}s` : 'Ongoing'],
            ['Outcome', fmt(call.outcome)],
            ['Started', call.started_at ? format(new Date(call.started_at), 'MMM d, yyyy HH:mm:ss') : '—'],
            ['Ended', call.ended_at ? format(new Date(call.ended_at), 'MMM d, yyyy HH:mm:ss') : '—'],
            ['Twilio SID', <span className="font-mono text-xs">{fmt(call.twilio_call_sid)}</span>],
            ['Error', fmt(call.error_message)],
          ] as [string, React.ReactNode][]).map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
              <dd className="mt-1 text-sm text-foreground">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {call.outcome_details && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Outcome Details</p>
          <p className="text-sm text-foreground whitespace-pre-wrap">{call.outcome_details}</p>
        </div>
      )}

      <button
        onClick={() => navigate(`/transcripts/${id}`)}
        className="flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2.5 text-sm font-medium text-primary hover:bg-primary/20 transition-colors"
      >
        <MessageSquare className="h-4 w-4" />
        View Transcript
      </button>
    </div>
  );
}
