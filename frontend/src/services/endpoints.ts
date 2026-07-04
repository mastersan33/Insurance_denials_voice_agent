import { api } from './api';

export const dashboardApi = {
  getStats: () => api.get('/api/v1/dashboard/stats'),
};

export const callJobsApi = {
  list: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get('/api/v1/call-jobs', { params }),
  get: (id: string) => api.get(`/api/v1/call-jobs/${id}`),
  create: (data: { billing_case_id: string; phone_number: string; priority?: number }) =>
    api.post('/api/v1/call-jobs', data),
  update: (id: string, data: { status?: string; priority?: number }) =>
    api.patch(`/api/v1/call-jobs/${id}`, data),
  getPending: (limit?: number) => api.get('/api/v1/call-jobs/pending', { params: { limit } }),
  trigger: (id: string) => api.post(`/api/v1/call-jobs/${id}/trigger`),
  cancel: (id: string) => api.post(`/api/v1/call-jobs/${id}/cancel`),
  // Queue management
  pauseQueue: () => api.post('/api/v1/call-jobs/queue/pause'),
  resumeQueue: () => api.post('/api/v1/call-jobs/queue/resume'),
  cancelAll: () => api.post('/api/v1/call-jobs/queue/cancel-all'),
  retryFailed: () => api.post('/api/v1/call-jobs/queue/retry-failed'),
};

export const callsApi = {
  getActive: () => api.get('/api/v1/calls/active'),
  get: (id: string) => api.get(`/api/v1/calls/${id}`),
};

export const transcriptsApi = {
  getBySession: (sessionId: string) => api.get(`/api/v1/transcripts/${sessionId}`),
  listAll: (params?: { skip?: number; limit?: number }) => api.get('/api/v1/transcripts/list', { params }),
};

export const ticketsApi = {
  list: (params?: { status?: string; skip?: number; limit?: number }) => api.get('/api/v1/tickets', { params }),
  create: (data: { title: string; description?: string; priority?: string }) =>
    api.post('/api/v1/tickets', data),
  update: (id: string, data: { status?: string; resolution?: string }) =>
    api.patch(`/api/v1/tickets/${id}`, data),
};

export const billingCasesApi = {
  list: (params?: { q?: string; status?: string; priority?: string; skip?: number; limit?: number }) =>
    api.get('/api/v1/billing-cases', { params }),
  get: (id: string) => api.get(`/api/v1/billing-cases/${id}`),
  create: (data: Record<string, unknown>) => api.post('/api/v1/billing-cases', data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/api/v1/billing-cases/${id}`, data),
  remove: (id: string) => api.delete(`/api/v1/billing-cases/${id}`),
  bulkImport: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/api/v1/billing-cases/bulk-import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const analyticsApi = {
  summary: () => api.get('/api/v1/analytics/summary'),
  callVolume: (days?: number) => api.get('/api/v1/analytics/call-volume', { params: { days } }),
  outcomes: () => api.get('/api/v1/analytics/outcomes'),
  avgDuration: (days?: number) => api.get('/api/v1/analytics/avg-duration', { params: { days } }),
  resolutionTrend: (days?: number) => api.get('/api/v1/analytics/resolution-trend', { params: { days } }),
  payers: () => api.get('/api/v1/analytics/payers'),
  denialCodes: () => api.get('/api/v1/analytics/denial-codes'),
};

export const reportsApi = {
  billingCases: (fmt: 'csv' | 'json' = 'csv') =>
    api.get('/api/v1/reports/billing-cases', { params: { fmt }, responseType: 'blob' }),
  calls: (fmt: 'csv' | 'json' = 'csv') =>
    api.get('/api/v1/reports/calls', { params: { fmt }, responseType: 'blob' }),
  transcripts: (sessionId?: string, fmt: 'csv' | 'json' = 'csv') =>
    api.get('/api/v1/reports/transcripts', { params: { fmt, session_id: sessionId }, responseType: 'blob' }),
};

export const auditApi = {
  list: (params?: { actor_id?: string; action?: string; resource_type?: string; skip?: number; limit?: number }) =>
    api.get('/api/v1/audit', { params }),
};

export const healthApi = {
  ready: () => api.get('/health/ready'),
  system: () => api.get('/health/system'),
};

export const humanHandoffApi = {
  list: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get('/api/v1/human-handoff', { params }),
  update: (id: string, data: { status?: string; resolution_notes?: string; assigned_to?: string }) =>
    api.patch(`/api/v1/human-handoff/${id}`, data),
};

export const usersApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/api/v1/users', { params }),
  update: (id: string, data: { role: string; is_active?: boolean }) =>
    api.patch(`/api/v1/users/${id}`, data),
  deactivate: (id: string) =>
    api.delete(`/api/v1/users/${id}`),
};

