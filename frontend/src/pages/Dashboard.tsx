import { PhoneCall, CheckCircle, XCircle, Clock, FileText, AlertTriangle } from 'lucide-react';
import StatsCard from '../components/StatsCard';
import { useDashboardStats } from '../hooks/useQueries';

export default function Dashboard() {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Calls"
          value={stats?.total_calls ?? 0}
          icon={<PhoneCall className="h-5 w-5" />}
        />
        <StatsCard
          title="Active Calls"
          value={stats?.active_calls ?? 0}
          icon={<Clock className="h-5 w-5" />}
        />
        <StatsCard
          title="Completed"
          value={stats?.completed_calls ?? 0}
          icon={<CheckCircle className="h-5 w-5" />}
        />
        <StatsCard
          title="Failed"
          value={stats?.failed_calls ?? 0}
          icon={<XCircle className="h-5 w-5" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatsCard
          title="Billing Cases"
          value={stats?.total_billing_cases ?? 0}
          icon={<FileText className="h-5 w-5" />}
        />
        <StatsCard
          title="Open Tickets"
          value={stats?.open_tickets ?? 0}
          icon={<AlertTriangle className="h-5 w-5" />}
        />
        <StatsCard
          title="Resolution Rate"
          value={`${stats?.resolution_rate ?? 0}%`}
          subtitle={`Avg duration: ${Math.round(stats?.average_call_duration ?? 0)}s`}
        />
      </div>
    </div>
  );
}
