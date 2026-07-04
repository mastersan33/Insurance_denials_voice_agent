import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { TrendingUp, Phone, Clock, Target } from 'lucide-react';
import { analyticsApi } from '../services/endpoints';
import StatsCard from '../components/StatsCard';
import { ChartSkeleton, StatCardSkeleton } from '../components/Skeleton';

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];
const DAY_OPTIONS = [7, 14, 30, 60, 90];

export default function Analytics() {
  const [days, setDays] = useState(30);

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: () => analyticsApi.summary().then((r) => r.data as Record<string, number>),
    staleTime: 60_000,
  });

  const { data: volume = [], isLoading: volumeLoading } = useQuery({
    queryKey: ['analytics-volume', days],
    queryFn: () => analyticsApi.callVolume(days).then((r) => r.data as { date: string; total: number; completed: number; failed: number }[]),
    staleTime: 60_000,
  });

  const { data: outcomes = [] } = useQuery({
    queryKey: ['analytics-outcomes'],
    queryFn: () => analyticsApi.outcomes().then((r) => r.data as { outcome: string; count: number; percentage: number }[]),
    staleTime: 60_000,
  });

  const { data: duration = [] } = useQuery({
    queryKey: ['analytics-duration', days],
    queryFn: () => analyticsApi.avgDuration(days).then((r) => r.data as { date: string; avg_duration: number }[]),
    staleTime: 60_000,
  });

  const { data: resolution = [] } = useQuery({
    queryKey: ['analytics-resolution', days],
    queryFn: () => analyticsApi.resolutionTrend(days).then((r) => r.data as { date: string; rate: number }[]),
    staleTime: 60_000,
  });

  const { data: payers = [] } = useQuery({
    queryKey: ['analytics-payers'],
    queryFn: () => analyticsApi.payers().then((r) => r.data as { payer: string; count: number; percentage: number }[]),
    staleTime: 60_000,
  });

  const { data: denials = [] } = useQuery({
    queryKey: ['analytics-denials'],
    queryFn: () => analyticsApi.denialCodes().then((r) => r.data as { code: string; count: number; percentage: number }[]),
    staleTime: 60_000,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Analytics</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Performance metrics and trends</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Period:</span>
          {DAY_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                days === d
                  ? 'bg-primary text-primary-foreground'
                  : 'border border-border bg-card text-muted-foreground hover:text-foreground'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {summaryLoading
          ? Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
          : [
              { title: 'Total Calls', value: summary?.total_calls ?? 0, icon: <Phone className="h-4 w-4" />, iconColor: 'bg-primary/10 text-primary' },
              { title: 'Resolution Rate', value: `${summary?.resolution_rate ?? 0}%`, icon: <Target className="h-4 w-4" />, iconColor: 'bg-success/10 text-success' },
              { title: 'Avg Duration', value: `${summary?.avg_duration_seconds ?? 0}s`, icon: <Clock className="h-4 w-4" />, iconColor: 'bg-info/10 text-info' },
              { title: 'Billing Cases', value: summary?.total_billing_cases ?? 0, icon: <TrendingUp className="h-4 w-4" />, iconColor: 'bg-warning/10 text-warning' },
            ].map((card) => <StatsCard key={card.title} {...card} />)}
      </div>

      {/* Call Volume + Resolution Trend */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-sm font-semibold text-foreground mb-4">Call Volume ({days} days)</p>
          {volumeLoading ? <ChartSkeleton height={200} /> : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={volume} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gCompleted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.05} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="total" stroke="#6366f1" fill="url(#gTotal)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="completed" stroke="#22c55e" fill="url(#gCompleted)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="failed" stroke="#ef4444" fill="none" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-sm font-semibold text-foreground mb-4">Resolution Rate Trend</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={resolution} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gRate" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.05} />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 100]} />
              <Tooltip contentStyle={{ fontSize: 12 }} formatter={(v) => [`${v}%`, 'Rate']} />
              <Area type="monotone" dataKey="rate" stroke="#22c55e" fill="url(#gRate)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Avg Duration + Outcome Breakdown */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-sm font-semibold text-foreground mb-4">Avg Call Duration (seconds)</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={duration} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.05} />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ fontSize: 12 }} formatter={(v) => [`${v}s`, 'Avg']} />
              <Area type="monotone" dataKey="avg_duration" stroke="#f59e0b" fill="none" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-sm font-semibold text-foreground mb-4">Outcome Breakdown</p>
          {outcomes.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">No outcome data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={outcomes} dataKey="count" nameKey="outcome" cx="50%" cy="50%" outerRadius={70} label={(p) => { const d = p as { outcome?: string; percentage?: number }; return `${d.outcome ?? ''} ${d.percentage ?? 0}%`; }} labelLine={false}>
                  {outcomes.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Payer + Denial Code breakdown */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-sm font-semibold text-foreground mb-4">Top Payers</p>
          {payers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={payers} layout="vertical" margin={{ left: 60, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.05} />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="payer" tick={{ fontSize: 10 }} width={60} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-card">
          <p className="text-sm font-semibold text-foreground mb-4">Denial Codes</p>
          {denials.length === 0 ? (
            <p className="text-sm text-muted-foreground">No data</p>
          ) : (
            <div className="space-y-2">
              {denials.map((d) => (
                <div key={d.code} className="flex items-center gap-3">
                  <span className="w-16 shrink-0 rounded bg-muted px-2 py-0.5 text-center text-xs font-mono font-semibold text-foreground">{d.code}</span>
                  <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${d.percentage}%` }} />
                  </div>
                  <span className="w-12 text-right text-xs text-muted-foreground">{d.count} ({d.percentage}%)</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
