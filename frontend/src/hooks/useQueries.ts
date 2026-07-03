import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardApi, callJobsApi, callsApi, transcriptsApi, billingCasesApi } from '../services/endpoints';
import type { DashboardStats } from '../types/dashboard';
import type { BillingCase, BillingCaseCreate, BillingCaseUpdate, PaginatedResponse } from '../types/billingCase';

export interface NewCallPayload {
  patient_name: string;
  payer_name: string;
  payer_phone: string;
  claim_number: string;
  denial_code: string;
  denial_reason: string;
  amount_billed: number;
  provider_name: string;
  provider_npi: string;
}

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats().then((r) => r.data as DashboardStats),
    refetchInterval: 15_000,
  });
}

export function useCallJobs(status?: string) {
  return useQuery({
    queryKey: ['call-jobs', status],
    queryFn: () => callJobsApi.list({ status }).then((r) => r.data),
    refetchInterval: 10_000,
  });
}

export function useTriggerCall() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => callJobsApi.trigger(jobId).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['call-jobs'] });
      qc.invalidateQueries({ queryKey: ['active-calls'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
}

export function useCancelCallJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => callJobsApi.cancel(jobId).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['call-jobs'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
}

// Create billing case → call job → trigger call — all in one action
export function useCreateAndCall() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: NewCallPayload) => {
      const caseRes = await billingCasesApi.create({
        patient_name: payload.patient_name,
        payer_name: payload.payer_name,
        payer_phone: payload.payer_phone,
        claim_number: payload.claim_number,
        denial_code: payload.denial_code,
        denial_reason: payload.denial_reason,
        amount_billed: payload.amount_billed,
        provider_name: payload.provider_name,
        provider_npi: payload.provider_npi,
      });
      const billingCase = caseRes.data;
      const jobRes = await callJobsApi.create({
        billing_case_id: billingCase.id,
        phone_number: payload.payer_phone,
        priority: 1,
      });
      const job = jobRes.data;
      const result = await callJobsApi.trigger(job.id);
      return result.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['call-jobs'] });
      qc.invalidateQueries({ queryKey: ['active-calls'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
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
    refetchInterval: 3_000,
  });
}

// ── Billing Cases ───────────────────────────────────────────────

export function useBillingCases(params: {
  q?: string;
  status?: string;
  priority?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery<PaginatedResponse<BillingCase>>({
    queryKey: ['billing-cases', params],
    queryFn: () => billingCasesApi.list(params).then((r) => r.data as PaginatedResponse<BillingCase>),
    staleTime: 10_000,
  });
}

export function useBillingCase(id: string) {
  return useQuery<BillingCase>({
    queryKey: ['billing-case', id],
    queryFn: () => billingCasesApi.get(id).then((r) => r.data as BillingCase),
    enabled: !!id,
  });
}

export function useCreateBillingCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BillingCaseCreate) =>
      billingCasesApi.create(data as unknown as Record<string, unknown>).then((r) => r.data as BillingCase),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['billing-cases'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
}

export function useUpdateBillingCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BillingCaseUpdate }) =>
      billingCasesApi.update(id, data as Record<string, unknown>).then((r) => r.data as BillingCase),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['billing-cases'] });
      qc.invalidateQueries({ queryKey: ['billing-case', id] });
    },
  });
}

export function useDeleteBillingCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => billingCasesApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['billing-cases'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
}

export function useBulkImportBillingCases() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => billingCasesApi.bulkImport(file).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['billing-cases'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
}

export function useAllTranscripts() {
  return useQuery({
    queryKey: ['transcripts-all'],
    queryFn: () => transcriptsApi.listAll().then((r) => r.data),
    refetchInterval: 10_000,
  });
}

// ── Queue management ────────────────────────────────────────────

export function usePauseQueue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => callJobsApi.pauseQueue().then((r) => r.data as { paused: number }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['call-jobs'] }),
  });
}

export function useResumeQueue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => callJobsApi.resumeQueue().then((r) => r.data as { resumed: number }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['call-jobs'] }),
  });
}

export function useCancelAllQueue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => callJobsApi.cancelAll().then((r) => r.data as { cancelled: number }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['call-jobs'] }),
  });
}

export function useRetryFailed() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => callJobsApi.retryFailed().then((r) => r.data as { retried: number }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['call-jobs'] }),
  });
}
