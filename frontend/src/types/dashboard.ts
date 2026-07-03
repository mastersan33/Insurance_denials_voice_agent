export interface CallVolumePoint {
  date: string;
  total: number;
  completed: number;
  failed: number;
}

export interface OutcomeBreakdown {
  outcome: string;
  count: number;
  percentage: number;
}

export interface RecentCallActivity {
  id: string;
  claim_number: string;
  payer_name: string;
  patient_name: string;
  status: string;
  outcome: string | null;
  duration_seconds: number | null;
  created_at: string;
}

export interface QueueStatus {
  pending: number;
  in_progress: number;
  scheduled: number;
  failed_retryable: number;
}

export interface SystemHealthStatus {
  database: boolean;
  redis: boolean;
  twilio_configured: boolean;
  elevenlabs_configured: boolean;
  openai_configured: boolean;
}

export interface DashboardStats {
  total_calls: number;
  active_calls: number;
  completed_calls: number;
  failed_calls: number;
  resolution_rate: number;
  average_call_duration: number;
  total_billing_cases: number;
  open_tickets: number;
  calls_today: number;
  completed_today: number;
  failed_today: number;
  amount_recovered_today: number;
  queue: QueueStatus;
  call_volume_7d: CallVolumePoint[];
  outcome_breakdown: OutcomeBreakdown[];
  recent_activity: RecentCallActivity[];
  health: SystemHealthStatus;
}
