import { create } from 'zustand';

interface DashboardStats {
  total_calls: number;
  active_calls: number;
  completed_calls: number;
  failed_calls: number;
  total_billing_cases: number;
  open_tickets: number;
  resolution_rate: number;
  average_call_duration: number;
}

interface DashboardState {
  stats: DashboardStats | null;
  setStats: (stats: DashboardStats) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  setStats: (stats) => set({ stats }),
}));
