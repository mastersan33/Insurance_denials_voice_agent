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
  list: (params?: { status?: string }) => api.get('/api/v1/tickets', { params }),
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
