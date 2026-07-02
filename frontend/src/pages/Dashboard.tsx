import { PhoneCall, CheckCircle, XCircle, Clock, FileText, AlertTriangle, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import StatsCard from '../components/StatsCard';
import StatusBadge from '../components/StatusBadge';
import { useDashboardStats, useAllTranscripts, useActiveCalls } from '../hooks/useQueries';

export default function Dashboard() {
  const { data: stats, isLoading } = useDashboardStats();
  const { data: transcripts } = useAllTranscripts();
  const { data: activeCalls } = useActiveCalls();
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>

      {/* Stats row 1 */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Total Calls" value={stats?.total_calls ?? 0} icon={<PhoneCall className="h-5 w-5" />} />
        <StatsCard title="Active Calls" value={stats?.active_calls ?? 0} icon={<Clock className="h-5 w-5" />} />
        <StatsCard title="Completed" value={stats?.completed_calls ?? 0} icon={<CheckCircle className="h-5 w-5" />} />
        <StatsCard title="Failed" value={stats?.failed_calls ?? 0} icon={<XCircle className="h-5 w-5" />} />
      </div>

      {/* Stats row 2 */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatsCard title="Billing Cases" value={stats?.total_billing_cases ?? 0} icon={<FileText className="h-5 w-5" />} />
        <StatsCard title="Open Tickets" value={stats?.open_tickets ?? 0} icon={<AlertTriangle className="h-5 w-5" />} />
        <StatsCard
          title="Resolution Rate"
          value={`${stats?.resolution_rate ?? 0}%`}
          subtitle={`Avg duration: ${Math.round(stats?.average_call_duration ?? 0)}s`}
        />
      </div>

      {/* Live calls */}
      {activeCalls && activeCalls.length > 0 && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-4">
          <h3 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            {activeCalls.length} Active Call{activeCalls.length > 1 ? 's' : ''}
          </h3>
          <div className="space-y-2">
            {activeCalls.map((call: Record<string, unknown>) => (
              <div key={call.id as string} className="flex items-center justify-between bg-white rounded-lg px-4 py-2 text-sm">
                <span className="font-mono text-gray-600">{call.to_number as string}</span>
                <StatusBadge status={call.status as string} />
                <span className="text-gray-500">{call.agent_phase as string || 'in progress'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent transcripts */}
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <MessageSquare className="h-4 w-4" /> Recent Conversation Turns
        </h3>
        {!transcripts || transcripts.length === 0 ? (
          <p className="text-sm text-gray-400">No transcripts yet — trigger a call to see conversations here.</p>
        ) : (
          <div className="space-y-2">
            {transcripts.slice(0, 10).map((t: Record<string, unknown>) => (
              <div
                key={t.id as string}
                className="flex gap-3 cursor-pointer hover:bg-gray-50 rounded px-2 py-1"
                onClick={() => navigate(`/transcripts/${t.call_session_id}`)}
              >
                <span className={`shrink-0 text-xs font-semibold mt-0.5 w-12 ${t.speaker === 'agent' ? 'text-indigo-600' : 'text-gray-500'}`}>
                  {(t.speaker as string).toUpperCase()}
                </span>
                <span className="text-sm text-gray-700 truncate">{t.content as string}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
