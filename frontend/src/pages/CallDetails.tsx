import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { callsApi } from '../services/endpoints';
import StatusBadge from '../components/StatusBadge';

export default function CallDetails() {
  const { id } = useParams<{ id: string }>();
  const { data: call, isLoading } = useQuery({
    queryKey: ['call', id],
    queryFn: () => callsApi.get(id!).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  if (!call) {
    return <div className="text-center text-gray-500">Call not found</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Call Details</h2>
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-sm font-medium text-gray-500">Session ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1"><StatusBadge status={call.status} /></dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">To Number</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.to_number}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Phase</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.agent_phase || 'N/A'}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Duration</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.duration_seconds ? `${call.duration_seconds}s` : 'Ongoing'}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Outcome</dt>
            <dd className="mt-1 text-sm text-gray-900">{call.outcome || 'Pending'}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
