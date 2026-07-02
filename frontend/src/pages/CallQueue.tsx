import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, Plus, X } from 'lucide-react';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import { useCallJobs, useTriggerCall, useCreateAndCall, type NewCallPayload } from '../hooks/useQueries';

const DENIAL_CODES = ['CO-97', 'CO-4', 'CO-16', 'CO-50', 'CO-22'];

const EMPTY_FORM: NewCallPayload = {
  patient_name: '',
  payer_name: '',
  payer_phone: '',
  claim_number: '',
  denial_code: 'CO-97',
  denial_reason: '',
  amount_billed: 0,
  provider_name: '',
  provider_npi: '',
};

export default function CallQueue() {
  const { data: jobs, isLoading } = useCallJobs();
  const navigate = useNavigate();
  const trigger = useTriggerCall();
  const createAndCall = useCreateAndCall();

  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<NewCallPayload>(EMPTY_FORM);
  const [error, setError] = useState('');

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === 'amount_billed' ? parseFloat(value) || 0 : value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      await createAndCall.mutateAsync(form);
      setShowModal(false);
      setForm(EMPTY_FORM);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message || 'Failed to place call.');
    }
  }

  const columns = [
    { key: 'id', header: 'ID', render: (row: Record<string, unknown>) => (row.id as string).slice(0, 8) },
    { key: 'phone_number', header: 'Phone' },
    { key: 'status', header: 'Status', render: (row: Record<string, unknown>) => <StatusBadge status={row.status as string} /> },
    { key: 'priority', header: 'Priority' },
    { key: 'attempt_count', header: 'Attempts' },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: Record<string, unknown>) => (
        <button
          onClick={(e) => { e.stopPropagation(); trigger.mutate(row.id as string); }}
          disabled={trigger.isPending || row.status === 'in_progress'}
          className="inline-flex items-center gap-1 rounded-md bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          <Phone className="h-3 w-3" />
          {trigger.isPending ? 'Calling...' : 'Call'}
        </button>
      ),
    },
  ];

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Call Queue</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{jobs?.length ?? 0} jobs</span>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            New Call
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={jobs || []}
        onRowClick={(row) => navigate(`/calls/${row.id}`)}
        emptyMessage="No call jobs in queue"
      />

      {/* New Call Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-900">New Outbound Call</h3>
              <button onClick={() => { setShowModal(false); setError(''); }} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Patient Name</label>
                  <input name="patient_name" value={form.patient_name} onChange={handleChange} required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Payer Name</label>
                  <input name="payer_name" value={form.payer_name} onChange={handleChange} required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Payer Phone</label>
                  <input name="payer_phone" value={form.payer_phone} onChange={handleChange} required placeholder="+1234567890"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Claim Number</label>
                  <input name="claim_number" value={form.claim_number} onChange={handleChange} required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Denial Code</label>
                  <select name="denial_code" value={form.denial_code} onChange={handleChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    {DENIAL_CODES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Amount Billed ($)</label>
                  <input name="amount_billed" type="number" min="0" step="0.01" value={form.amount_billed} onChange={handleChange} required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Provider Name</label>
                  <input name="provider_name" value={form.provider_name} onChange={handleChange} required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Provider NPI</label>
                  <input name="provider_npi" value={form.provider_npi} onChange={handleChange} required
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Denial Reason</label>
                <input name="denial_reason" value={form.denial_reason} onChange={handleChange} required
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              {error && <p className="text-xs text-red-600">{error}</p>}
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => { setShowModal(false); setError(''); }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Cancel
                </button>
                <button type="submit" disabled={createAndCall.isPending}
                  className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
                  <Phone className="h-4 w-4" />
                  {createAndCall.isPending ? 'Placing call...' : 'Place Call'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

