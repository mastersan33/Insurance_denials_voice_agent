import { useNavigate } from 'react-router-dom';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import { useCallJobs } from '../hooks/useQueries';

export default function CallQueue() {
  const { data: jobs, isLoading } = useCallJobs();
  const navigate = useNavigate();

  const columns = [
    { key: 'id', header: 'ID', render: (row: Record<string, unknown>) => (row.id as string).slice(0, 8) },
    { key: 'phone_number', header: 'Phone' },
    { key: 'status', header: 'Status', render: (row: Record<string, unknown>) => <StatusBadge status={row.status as string} /> },
    { key: 'priority', header: 'Priority' },
    { key: 'attempt_count', header: 'Attempts' },
    { key: 'created_at', header: 'Created' },
  ];

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Call Queue</h2>
      </div>
      <DataTable
        columns={columns}
        data={jobs || []}
        onRowClick={(row) => navigate(`/calls/${row.id}`)}
        emptyMessage="No call jobs in queue"
      />
    </div>
  );
}
