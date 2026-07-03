import { clsx } from 'clsx';

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-success/10 text-success border-success/20',
  in_progress: 'bg-success/10 text-success border-success/20',
  initiated: 'bg-info/10 text-info border-info/20',
  ringing: 'bg-info/10 text-info border-info/20',
  completed: 'bg-muted text-muted-foreground border-border',
  failed: 'bg-destructive/10 text-destructive border-destructive/20',
  pending: 'bg-warning/10 text-warning border-warning/20',
  scheduled: 'bg-primary/10 text-primary border-primary/20',
  cancelled: 'bg-muted text-muted-foreground border-border',
  canceled: 'bg-muted text-muted-foreground border-border',
  open: 'bg-warning/10 text-warning border-warning/20',
  closed: 'bg-muted text-muted-foreground border-border',
  resolved: 'bg-success/10 text-success border-success/20',
  transferred_to_human: 'bg-info/10 text-info border-info/20',
  escalated: 'bg-destructive/10 text-destructive border-destructive/20',
  high: 'bg-destructive/10 text-destructive border-destructive/20',
  medium: 'bg-warning/10 text-warning border-warning/20',
  low: 'bg-muted text-muted-foreground border-border',
};

const STATUS_DOT: Record<string, string> = {
  active: 'bg-success',
  in_progress: 'bg-success',
  initiated: 'bg-info',
  ringing: 'bg-info',
  completed: 'bg-muted-foreground',
  failed: 'bg-destructive',
  pending: 'bg-warning',
  scheduled: 'bg-primary',
};

interface StatusBadgeProps {
  status: string;
  dot?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export default function StatusBadge({ status, dot = false, size = 'sm', className }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? 'bg-muted text-muted-foreground border-border';
  const dotColor = STATUS_DOT[status] ?? 'bg-muted-foreground';
  const label = status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
        style,
        className
      )}
    >
      {dot && <span className={clsx('h-1.5 w-1.5 rounded-full flex-shrink-0', dotColor)} />}
      {label}
    </span>
  );
}

