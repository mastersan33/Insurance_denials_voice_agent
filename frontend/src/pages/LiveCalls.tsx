import { useNavigate } from 'react-router-dom';
import { Radio } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { useActiveCalls } from '../hooks/useQueries';
import { formatDistanceToNow } from 'date-fns';

export default function LiveCalls() {
  const { data: calls, isLoading } = useActiveCalls();
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Live Calls</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Refreshes every 10s</p>
        </div>
        {calls && calls.length > 0 ? (
          <span className="flex items-center gap-2 rounded-full bg-success/10 px-3 py-1 text-xs font-semibold text-success">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
            </span>
            {calls.length} active
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">No active calls</span>
        )}
      </div>

      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Session</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">To</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Phase</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Confidence</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Started</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((__, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </td>
                    ))}
                  </tr>
                ))
              : !calls || calls.length === 0
              ? (
                <tr>
                  <td colSpan={7} className="px-4 py-16 text-center">
                    <Radio className="h-8 w-8 mx-auto mb-2 text-muted-foreground/30" />
                    <p className="text-sm text-muted-foreground">No active calls right now</p>
                  </td>
                </tr>
              )
              : calls.map((call: Record<string, unknown>) => (
                <tr
                  key={call.id as string}
                  onClick={() => navigate(`/calls/${call.id}`)}
                  className="hover:bg-accent/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-foreground">
                    {(call.id as string).slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3 text-foreground">{call.to_number as string || '—'}</td>
                  <td className="px-4 py-3"><StatusBadge status={call.status as string} size="sm" /></td>
                  <td className="px-4 py-3 text-sm text-foreground capitalize">{call.agent_phase as string || '—'}</td>
                  <td className="px-4 py-3 text-sm text-foreground">
                    {call.confidence_score != null
                      ? `${Math.round((call.confidence_score as number) * 100)}%`
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {call.started_at
                      ? formatDistanceToNow(new Date(call.started_at as string), { addSuffix: true })
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/transcripts/${call.id}`); }}
                      className="text-xs text-primary hover:underline"
                    >
                      Transcript
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
