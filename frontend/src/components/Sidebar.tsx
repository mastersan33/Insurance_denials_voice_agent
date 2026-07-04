import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, PhoneCall, Radio, FileText, Settings,
  Ticket, Users, BarChart2, PhoneForwarded, Brain, ChevronLeft, ChevronRight,
  Download, Activity, ShieldCheck,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useState } from 'react';
import { useAuthStore } from '../store/authStore';

interface NavItem {
  path: string;
  label: string;
  icon: React.ElementType;
  badge?: number;
  minRole?: 'viewer' | 'operator' | 'supervisor' | 'admin';
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: 'Overview',
    items: [
      { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    title: 'Operations',
    items: [
      { path: '/billing-cases', label: 'Billing Cases', icon: FileText },
      { path: '/call-queue', label: 'Call Queue', icon: PhoneCall },
      { path: '/live-calls', label: 'Live Calls', icon: Radio },
      { path: '/human-handoff', label: 'Human Handoff', icon: PhoneForwarded },
    ],
  },
  {
    title: 'Insights',
    items: [
      { path: '/analytics', label: 'Analytics', icon: BarChart2 },
      { path: '/reports', label: 'Reports', icon: Download },
      { path: '/tickets', label: 'Tickets', icon: Ticket },
    ],
  },
  {
    title: 'System',
    items: [
      { path: '/users', label: 'Users', icon: Users, minRole: 'supervisor' as const },
      { path: '/system-health', label: 'System Health', icon: Activity },
      { path: '/audit-log', label: 'Audit Log', icon: ShieldCheck, minRole: 'supervisor' as const },
      { path: '/settings', label: 'Settings', icon: Settings },
      { path: '/profile', label: 'Profile', icon: Brain },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();
  const { user } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const initials = user?.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) ?? '?';

  return (
    <aside
      className={clsx(
        'flex flex-col border-r border-border bg-card transition-all duration-200 flex-shrink-0',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <PhoneCall className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold text-foreground leading-none">
              Voice Agent
            </span>
          </div>
        )}
        {collapsed && (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary mx-auto">
            <PhoneCall className="h-4 w-4 text-primary-foreground" />
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {navGroups.map((group) => (
          <div key={group.title}>
            {!collapsed && (
              <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
                {group.title}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                if (item.minRole && !user) return null;
                if (item.minRole) {
                  const ROLE_LEVEL: Record<string, number> = { viewer: 0, operator: 1, supervisor: 2, admin: 3 };
                  if ((ROLE_LEVEL[user!.role] ?? -1) < (ROLE_LEVEL[item.minRole] ?? 0)) return null;
                }
                const Icon = item.icon;
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    title={collapsed ? item.label : undefined}
                    className={clsx(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      collapsed && 'justify-center px-2',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                    {!collapsed && item.badge != null && item.badge > 0 && (
                      <span className="ml-auto flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-2">
        {collapsed ? (
          <button
            onClick={() => setCollapsed(false)}
            className="flex w-full items-center justify-center rounded-lg p-2 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            title="Expand"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <Link
            to="/profile"
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 hover:bg-accent transition-colors"
          >
            <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-semibold text-primary">{initials}</span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{user?.full_name}</p>
              <p className="text-[10px] text-muted-foreground capitalize">{user?.role}</p>
            </div>
          </Link>
        )}
      </div>
    </aside>
  );
}

