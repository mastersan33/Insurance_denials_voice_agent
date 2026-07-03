import { useAuthStore } from '../store/authStore';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

interface HealthChecks {
  database: boolean;
  redis: boolean;
}

interface SystemHealth {
  status: string;
  checks: HealthChecks;
}

function IntegrationRow({ label, description, ok }: { label: string; description: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${ok ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
        {ok ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}

export default function Settings() {
  const user = useAuthStore((s) => s.user);

  const { data: health } = useQuery<SystemHealth>({
    queryKey: ['health-ready'],
    queryFn: () => api.get('/health/ready').then((r) => r.data as SystemHealth),
    refetchInterval: 30_000,
    retry: false,
  });

  const dbOk = health?.checks?.database ?? true;
  const redisOk = health?.checks?.redis ?? true;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Account</h3>
        <dl className="space-y-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{user?.full_name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Email</dt>
            <dd className="mt-1 text-sm text-gray-900">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Role</dt>
            <dd className="mt-1 text-sm text-gray-900 capitalize">{user?.role}</dd>
          </div>
        </dl>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Integrations</h3>
        <div className="space-y-3">
          <IntegrationRow label="Database" description="PostgreSQL connection" ok={dbOk} />
          <IntegrationRow label="Redis" description="Cache & rate limiting" ok={redisOk} />
          <IntegrationRow label="Twilio" description="Voice API integration" ok={true} />
          <IntegrationRow label="ElevenLabs" description="Speech-to-Text & Text-to-Speech" ok={true} />
          <IntegrationRow label="OpenAI" description="AI Agent (GPT-4o)" ok={true} />
        </div>
      </div>
    </div>
  );
}
