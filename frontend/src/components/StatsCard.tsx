import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  iconColor?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  className?: string;
  loading?: boolean;
}

export default function StatsCard({
  title,
  value,
  subtitle,
  icon,
  iconColor = 'bg-primary/10 text-primary',
  trend,
  trendValue,
  className,
}: StatsCardProps) {
  return (
    <div
      className={clsx(
        'rounded-xl border border-border bg-card p-5 shadow-card hover:shadow-card-hover transition-shadow',
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-muted-foreground mb-1.5">{title}</p>
          <p className="text-2xl font-bold text-foreground tabular-nums leading-none">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-1.5">{subtitle}</p>
          )}
          {trend && trendValue && (
            <div
              className={clsx(
                'flex items-center gap-1 mt-2 text-xs font-medium',
                trend === 'up' && 'text-success',
                trend === 'down' && 'text-destructive',
                trend === 'neutral' && 'text-muted-foreground'
              )}
            >
              {trend === 'up' && <TrendingUp className="h-3 w-3" />}
              {trend === 'down' && <TrendingDown className="h-3 w-3" />}
              {trend === 'neutral' && <Minus className="h-3 w-3" />}
              {trendValue}
            </div>
          )}
        </div>
        {icon && (
          <div className={clsx('flex h-9 w-9 items-center justify-center rounded-lg flex-shrink-0', iconColor)}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
