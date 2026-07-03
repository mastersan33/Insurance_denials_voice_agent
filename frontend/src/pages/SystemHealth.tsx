import { useQuery } from '@tanstack/react-query';
import { Database, Cpu, MemoryStick, HardDrive, Wifi, Activity, RefreshCw } from 'lucide-react';
import { healthApi } from '../services/endpoints';

interface SystemMetrics {
  cpu_percent?: number;
  memory_total_mb?: number;
  memory_used_mb?: number;
  memory_percent?: number;
  disk_total_gb?: number;
  disk_used_gb?: number;
  disk_percent?: number;
  database?: boolean;
  redis?: boolean;
  redis_used_memory_mb?: number;
  active_ws_connections?: number;
  psutil?: string;
}

function ProgressBar({ value, color = 'bg-primary' }: { value: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, value));
  const barColor = pct > 85 ? 'bg-destructive' : pct > 65 ? 'bg-warning' : color;
  return (
    <div className="h-2 rounded-full bg-muted overflow-hidden">
      <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function StatusDot({ ok }: { ok: boolean | undefined }) {
  if (ok === undefined) return <span className="h-2 w-2 rounded-full bg-muted-foreground inline-block" />;
  return <span className={`h-2 w-2 rounded-full inline-block ${ok ? 'bg-success' : 'bg-destructive'}`} />;
}

function MetricCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-card">
      <div className="flex items-center gap-2 mb-4">
        <div className="rounded-lg bg-muted p-1.5">{icon}</div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
      </div>
      {children}
    </div>
  );
}

export default function SystemHealth() {
  const { data: metrics, isLoading, refetch, isFetching } = useQuery<SystemMetrics>({
    queryKey: ['system-health'],
    queryFn: () => healthApi.system().then((r) => r.data as SystemMetrics),
    refetchInterval: 15_000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-bold text-foreground">System Health</h1>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  const m = metrics ?? {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">System Health</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Live metrics — refreshes every 15s</p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* CPU */}
        <MetricCard icon={<Cpu className="h-4 w-4 text-primary" />} title="CPU">
          {m.cpu_percent !== undefined ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Usage</span>
                <span className="font-semibold text-foreground tabular-nums">{m.cpu_percent.toFixed(1)}%</span>
              </div>
              <ProgressBar value={m.cpu_percent} />
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">psutil not installed</p>
          )}
        </MetricCard>

        {/* Memory */}
        <MetricCard icon={<MemoryStick className="h-4 w-4 text-info" />} title="Memory">
          {m.memory_percent !== undefined ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Used</span>
                <span className="font-semibold text-foreground tabular-nums">
                  {m.memory_used_mb?.toFixed(0)} / {m.memory_total_mb?.toFixed(0)} MB
                </span>
              </div>
              <ProgressBar value={m.memory_percent} color="bg-info" />
              <p className="text-xs text-muted-foreground text-right">{m.memory_percent.toFixed(1)}%</p>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">psutil not installed</p>
          )}
        </MetricCard>

        {/* Disk */}
        <MetricCard icon={<HardDrive className="h-4 w-4 text-warning" />} title="Disk">
          {m.disk_percent !== undefined ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Used</span>
                <span className="font-semibold text-foreground tabular-nums">
                  {m.disk_used_gb?.toFixed(1)} / {m.disk_total_gb?.toFixed(1)} GB
                </span>
              </div>
              <ProgressBar value={m.disk_percent} color="bg-warning" />
              <p className="text-xs text-muted-foreground text-right">{m.disk_percent.toFixed(1)}%</p>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">psutil not installed</p>
          )}
        </MetricCard>

        {/* Database */}
        <MetricCard icon={<Database className="h-4 w-4 text-success" />} title="Database">
          <div className="flex items-center gap-2">
            <StatusDot ok={m.database} />
            <span className="text-sm font-medium text-foreground">{m.database ? 'Connected' : 'Disconnected'}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">PostgreSQL / SQLite async engine</p>
        </MetricCard>

        {/* Redis */}
        <MetricCard icon={<Activity className="h-4 w-4 text-destructive" />} title="Redis">
          <div className="flex items-center gap-2">
            <StatusDot ok={m.redis} />
            <span className="text-sm font-medium text-foreground">{m.redis ? 'Connected' : 'Disconnected'}</span>
          </div>
          {m.redis_used_memory_mb !== undefined && (
            <p className="text-xs text-muted-foreground mt-2">Memory: {m.redis_used_memory_mb.toFixed(1)} MB</p>
          )}
        </MetricCard>

        {/* WebSocket */}
        <MetricCard icon={<Wifi className="h-4 w-4 text-primary" />} title="WebSocket">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-foreground tabular-nums">{m.active_ws_connections ?? 0}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Active connections</p>
        </MetricCard>
      </div>
    </div>
  );
}
