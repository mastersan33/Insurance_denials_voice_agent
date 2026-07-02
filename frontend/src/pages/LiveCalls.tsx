import { useNavigate } from 'react-router-dom';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import { useActiveCalls } from '../hooks/useQueries';

export default function LiveCalls() {
  const { data: calls, isLoading } = useActiveCalls();
  const navigate = useNavigate();

  const columns = [
    { key: 'id', header: 'Session ID', render: (row: Record<string, unknown>) => (row.id as string).slice(0, 8) },
    { key: 'to_number', header: 'To' },
    { key: 'status', header: 'Status', render: (row: Record<string, unknown>) => <StatusBadge status={row.status as string} /> },
    { key: 'agent_phase', header: 'Phase', render: (row: Record<string, unknown>) => row.agent_phase as string || '—' },
    {
      key: 'confidence_score',
      header: 'Confidence',
      render: (row: Record<string, unknown>) =>
        row.confidence_score ? `${Math.round((row.confidence_score as number) * 100)}%` : '—',
    },
    { key: 'started_at', header: 'Started' },
    {
      key: 'transcript',
      header: 'Transcript',
      render: (row: Record<string, unknown>) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/transcripts/${row.id}`); }}
          className="text-xs text-indigo-600 hover:underline"
        >
          View live
        </button>
      ),
    },
  ];

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Live Calls</h2>
        <span className="text-sm text-gray-500">
          {calls && calls.length > 0
            ? <span className="text-green-600 font-semibold">{calls.length} active</span>
            : 'No active calls'} — refreshes every 5s
        </span>
      </div>
      <DataTable
        columns={columns}
        data={calls || []}
        emptyMessage="No active calls right now"
      />
    </div>
  );
}
