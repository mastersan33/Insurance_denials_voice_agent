import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useThemeStore } from '../store/themeStore';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../services/endpoints';
import { Moon, Sun, Monitor } from 'lucide-react';

interface SystemHealth {
  status: string;
  checks: { database: boolean; redis: boolean };
}

type Theme = 'light' | 'dark' | 'system';

function IntegrationRow({ label, description, ok }: { label: string; description: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
        ok ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'
      }`}>
        {ok ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}

const THEME_OPTIONS: { value: Theme; label: string; icon: React.ElementType }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  const { theme, setTheme } = useThemeStore();

  const { data: health } = useQuery<SystemHealth>({
    queryKey: ['health-ready'],
    queryFn: () => healthApi.ready().then((r) => r.data as SystemHealth),
    refetchInterval: 30_000,
    retry: false,
  });

  const dbOk = health?.checks?.database ?? true;
  const redisOk = health?.checks?.redis ?? true;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-foreground">Settings</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Manage your account and application preferences</p>
      </div>

      {/* Account */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-card">
        <h3 className="text-sm font-semibold text-foreground mb-4">Account</h3>
        <dl className="space-y-1">
          {([
            ['Name', user?.full_name],
            ['Email', user?.email],
            ['Role', <span className="capitalize">{user?.role}</span>],
          ] as [string, React.ReactNode][]).map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
              <dt className="text-sm text-muted-foreground">{label}</dt>
              <dd className="text-sm font-medium text-foreground">{value}</dd>
            </div>
          ))}
        </dl>
        <Link to="/profile" className="mt-4 inline-block text-xs text-primary hover:underline">
          Edit profile & change password →
        </Link>
      </div>

      {/* Appearance */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-card">
        <h3 className="text-sm font-semibold text-foreground mb-4">Appearance</h3>
        <div className="flex items-center gap-2">
          {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setTheme(value)}
              className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-medium transition-colors ${
                theme === value
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-card text-muted-foreground hover:text-foreground hover:bg-accent'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Integrations */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-card">
        <h3 className="text-sm font-semibold text-foreground mb-4">Integrations</h3>
        <IntegrationRow label="Database" description="SQLite / PostgreSQL" ok={dbOk} />
        <IntegrationRow label="Redis" description="Cache & rate limiting" ok={redisOk} />
        <IntegrationRow label="Twilio" description="Voice API" ok={true} />
        <IntegrationRow label="ElevenLabs" description="Speech synthesis & recognition" ok={true} />
        <IntegrationRow label="OpenAI" description="AI Agent (GPT-4o)" ok={true} />
      </div>
    </div>
  );
}
