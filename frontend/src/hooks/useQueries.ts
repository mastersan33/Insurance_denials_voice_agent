import { useQuery } from '@tanstack/react-query';
import { dashboardApi, callJobsApi, callsApi, transcriptsApi } from '../services/endpoints';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats().then((r) => r.data),
    refetchInterval: 30_000,
  });
}

export function useCallJobs(status?: string) {
  return useQuery({
    queryKey: ['call-jobs', status],
    queryFn: () => callJobsApi.list({ status }).then((r) => r.data),
  });
}

export function useActiveCalls() {
  return useQuery({
    queryKey: ['active-calls'],
    queryFn: () => callsApi.getActive().then((r) => r.data),
    refetchInterval: 5_000,
  });
}

export function useTranscripts(sessionId: string) {
  return useQuery({
    queryKey: ['transcripts', sessionId],
    queryFn: () => transcriptsApi.getBySession(sessionId).then((r) => r.data),
    enabled: !!sessionId,
  });
}
