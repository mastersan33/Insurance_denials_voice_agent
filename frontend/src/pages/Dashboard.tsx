import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer, Legend,
} from 'recharts';
import {
  PhoneCall, CheckCircle, XCircle, Clock, FileText,
  Ticket, TrendingUp, Activity, Wifi, WifiOff, RefreshCw,
} from 'lucide-react';
import StatsCard from '../components/StatsCard';
import StatusBadge from '../components/StatusBadge';
import { StatCardSkeleton, ChartSkeleton, Skeleton } from '../components/Skeleton';
import { useDashboardStats } from '../hooks/useQueries';
import { useDashboardWebSocket } from '../hooks/useWebSocket';
import type { OutcomeBreakdown, RecentCallActivity } from '../types/dashboard';
import { useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';

const CHART_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

function HealthDot({ ok }: { ok: boolean }) {
  return (
    <span className={`inline-flex h-2 w-2 rounded-full ${ok ? 'bg-success' : 'bg-destructive'}`} />
  );
}

export default function Dashboard() {
  const { data: stats, isLoading, dataUpdatedAt, refetch, isFetching } = useDashboardStats();
  const navigate = useNavigate();
  const qc = useQueryClient();

  // Real-time push from backend WebSocket — updates query cache directly
  useDashboardWebSocket();

  const lastUpdated = useMemo(() => {
    if (!dataUpdatedAt) return null;
    return formatDistanceToNow(new Date(dataUpdatedAt), { addSuffix: true });
  }, [dataUpdatedAt]);

  const chartData = stats?.call_volume_7d ?? [];
  const outcomeData = stats?.outcome_breakdown ?? [];
  const hasOutcomes = outcomeData.length > 0;

  const fadeUp = { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-7 w-36" />
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <StatCardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <ChartSkeleton height={220} />
          <ChartSkeleton height={220} />
          <ChartSkeleton height={220} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Dashboard</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {lastUpdated ? `Updated ${lastUpdated}` : 'Live data'}
            {isFetching && <span className="ml-2 text-primary">• refreshing</span>}
          </p>
        </div>
        <button
          onClick={() => { refetch(); qc.invalidateQueries({ queryKey: ['dashboard-stats'] }); }}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Live call pulse banner */}
      {stats && stats.active_calls > 0 && (
        <motion.div
          {...fadeUp}
          className="flex items-center justify-between rounded-xl border border-success/30 bg-success/5 px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success" />
            </span>
            <span className="text-sm font-semibold text-success">
              {stats.active_calls} active call{stats.active_calls > 1 ? 's' : ''} in progress
            </span>
          </div>
          <button
            onClick={() => navigate('/live-calls')}
            className="text-xs font-medium text-success hover:underline"
          >
            View live →
          </button>
        </motion.div>
      )}

      {/* Row 1 — headline metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          {
            title: 'Total Calls', value: stats?.total_calls ?? 0,
            icon: <PhoneCall className="h-4 w-4" />, iconColor: 'bg-primary/10 text-primary',
          },
          {
            title: 'Active Now', value: stats?.active_calls ?? 0,
            icon: <Activity className="h-4 w-4" />, iconColor: 'bg-success/10 text-success',
          },
          {
            title: 'Completed', value: stats?.completed_calls ?? 0,
            icon: <CheckCircle className="h-4 w-4" />, iconColor: 'bg-success/10 text-success',
          },
          {
            title: 'Failed', value: stats?.failed_calls ?? 0,
            icon: <XCircle className="h-4 w-4" />, iconColor: 'bg-destructive/10 text-destructive',
          },
        ].map((card, i) => (
          <motion.div key={card.title} {...fadeUp} transition={{ delay: i * 0.05 }}>
            <StatsCard {...card} />
          </motion.div>
        ))}
      </div>

      {/* Row 2 — secondary metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          {
            title: 'Resolution Rate', value: `${stats?.resolution_rate ?? 0}%`,
            icon: <TrendingUp className="h-4 w-4" />, iconColor: 'bg-primary/10 text-primary',
            subtitle: 'All time',
          },
          {
            title: 'Avg Duration', value: `${Math.round(stats?.average_call_duration ?? 0)}s`,
            icon: <Clock className="h-4 w-4" />, iconColor: 'bg-info/10 text-info',
            subtitle: 'Per call',
          },
          {
            title: 'Billing Cases', value: stats?.total_billing_cases ?? 0,
            icon: <FileText className="h-4 w-4" />, iconColor: 'bg-warning/10 text-warning',
          },
          {
            title: 'Open Tickets', value: stats?.open_tickets ?? 0,
            icon: <Ticket className="h-4 w-4" />, iconColor: 'bg-destructive/10 text-destructive',
          },
        ].map((card, i) => (
          <motion.div key={card.title} {...fadeUp} transition={{ delay: 0.2 + i * 0.05 }}>
            <StatsCard {...card} />
          </motion.div>
        ))}
      </div>

      {/* Row 3 — Today snapshot */}
      <motion.div {...fadeUp} transition={{ delay: 0.3 }} className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="col-span-2 lg:col-span-4 rounded-xl border border-border bg-card p-4 shadow-card">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Today</p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: 'Calls', value: stats?.calls_today ?? 0 },
              { label: 'Completed', value: stats?.completed_today ?? 0 },
              { label: 'Failed', value: stats?.failed_today ?? 0 },
              { label: 'Queue Pending', value: stats?.queue.pending ?? 0 },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-2xl font-bold text-foreground tabular-nums">{item.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Row 4 — Charts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* 7-day area chart */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.35 }}
          className="lg:col-span-2 rounded-xl border border-border bg-card p-5 shadow-card"
        >
          <p className="text-sm font-semibold text-foreground mb-4">Call Volume — Last 7 Days</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="date"
                tickFormatter={(v) => v.slice(5)}
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
              <Tooltip
                contentStyle={{
                  background: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Area type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} fill="url(#colorTotal)" name="Total" />
              <Area type="monotone" dataKey="completed" stroke="#22c55e" strokeWidth={2} fill="url(#colorCompleted)" name="Completed" />
              <Area type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={1.5} fill="none" name="Failed" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Outcome pie chart */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.4 }}
          className="rounded-xl border border-border bg-card p-5 shadow-card"
        >
          <p className="text-sm font-semibold text-foreground mb-4">Outcome Breakdown</p>
          {hasOutcomes ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={outcomeData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  dataKey="count"
                  nameKey="outcome"
                  paddingAngle={2}
                >
                  {outcomeData.map((_: OutcomeBreakdown, i: number) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v, n) => [`${v} calls`, String(n).replace(/_/g, ' ')]}
                  contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 8, fontSize: 12 }}
                />
                <Legend
                  formatter={(v) => String(v).replace(/_/g, ' ')}
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: 11 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-48 items-center justify-center">
              <p className="text-sm text-muted-foreground">No outcome data yet</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Row 5 — Queue + System Health */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Queue status */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.45 }}
          className="rounded-xl border border-border bg-card p-5 shadow-card"
        >
          <p className="text-sm font-semibold text-foreground mb-4">Queue Status</p>
          <div className="space-y-3">
            {[
              { label: 'Pending', value: stats?.queue.pending ?? 0, color: 'bg-warning' },
              { label: 'In Progress', value: stats?.queue.in_progress ?? 0, color: 'bg-success' },
              { label: 'Scheduled', value: stats?.queue.scheduled ?? 0, color: 'bg-primary' },
              { label: 'Failed (retryable)', value: stats?.queue.failed_retryable ?? 0, color: 'bg-destructive' },
            ].map((row) => (
              <div key={row.label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${row.color}`} />
                  <span className="text-sm text-muted-foreground">{row.label}</span>
                </div>
                <span className="text-sm font-semibold text-foreground tabular-nums">{row.value}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* System health */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.5 }}
          className="rounded-xl border border-border bg-card p-5 shadow-card"
        >
          <p className="text-sm font-semibold text-foreground mb-4">System Health</p>
          <div className="space-y-3">
            {[
              { label: 'Database', ok: stats?.health.database ?? false },
              { label: 'Redis', ok: stats?.health.redis ?? false },
              { label: 'Twilio', ok: stats?.health.twilio_configured ?? false },
              { label: 'ElevenLabs', ok: stats?.health.elevenlabs_configured ?? false },
              { label: 'OpenAI', ok: stats?.health.openai_configured ?? false },
            ].map((row) => (
              <div key={row.label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <HealthDot ok={row.ok} />
                  <span className="text-sm text-muted-foreground">{row.label}</span>
                </div>
                <span className="flex items-center gap-1 text-xs font-medium">
                  {row.ok
                    ? <><Wifi className="h-3 w-3 text-success" /><span className="text-success">OK</span></>
                    : <><WifiOff className="h-3 w-3 text-destructive" /><span className="text-destructive">Not configured</span></>
                  }
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recent activity feed */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.55 }}
          className="rounded-xl border border-border bg-card p-5 shadow-card"
        >
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-foreground">Recent Activity</p>
            <button
              onClick={() => navigate('/call-queue')}
              className="text-xs text-primary hover:underline"
            >
              View all
            </button>
          </div>
          {!stats?.recent_activity || stats.recent_activity.length === 0 ? (
            <div className="flex h-40 items-center justify-center">
              <p className="text-sm text-muted-foreground">No recent calls</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-52 overflow-y-auto">
              {stats.recent_activity.map((item: RecentCallActivity) => (
                <div
                  key={item.id}
                  onClick={() => navigate(`/calls/${item.id}`)}
                  className="flex items-center justify-between gap-2 rounded-lg px-3 py-2 hover:bg-accent cursor-pointer transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">{item.payer_name}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{item.claim_number}</p>
                  </div>
                  <StatusBadge status={item.status} size="sm" />
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
