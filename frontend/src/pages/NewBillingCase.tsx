import { useNavigate } from 'react-router-dom';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft } from 'lucide-react';
import { useCreateBillingCase } from '../hooks/useQueries';

const schema = z.object({
  patient_name: z.string().min(1, 'Patient name is required'),
  payer_name: z.string().min(1, 'Payer name is required'),
  payer_phone: z.string().optional(),
  claim_number: z.string().min(1, 'Claim number is required'),
  patient_dob: z.string().optional(),
  subscriber_id: z.string().optional(),
  service_date: z.string().optional(),
  cpt_codes: z.string().optional(),
  icd10_codes: z.string().optional(),
  amount_billed_str: z.string().optional(),
  denial_code: z.string().optional(),
  denial_reason: z.string().optional(),
  provider_name: z.string().optional(),
  provider_npi: z.string().optional(),
  priority: z.enum(['low', 'normal', 'high', 'urgent']),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

function Field({
  label,
  error,
  required,
  children,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-foreground mb-1">
        {label}{required && <span className="text-destructive ml-0.5">*</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-[11px] text-destructive">{error}</p>}
    </div>
  );
}

const inputCls = 'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30';

export default function NewBillingCase() {
  const navigate = useNavigate();
  const createMutation = useCreateBillingCase();

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { priority: 'normal' as const },
  });

  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    const amount = data.amount_billed_str ? parseFloat(data.amount_billed_str) : undefined;
    const result = await createMutation.mutateAsync({
      ...data,
      amount_billed: Number.isFinite(amount) ? amount : undefined,
    });
    navigate(`/billing-cases/${result.id}`);
  };

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-foreground">New Billing Case</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Enter the denial details to create a new case</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Patient info */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-card space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Patient Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Patient Name" required error={errors.patient_name?.message}>
              <input {...register('patient_name')} className={inputCls} placeholder="John Doe" />
            </Field>
            <Field label="Date of Birth" error={errors.patient_dob?.message}>
              <input {...register('patient_dob')} type="date" className={inputCls} />
            </Field>
            <Field label="Subscriber ID" error={errors.subscriber_id?.message}>
              <input {...register('subscriber_id')} className={inputCls} placeholder="SUB-12345" />
            </Field>
          </div>
        </section>

        {/* Payer info */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-card space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Payer Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Payer Name" required error={errors.payer_name?.message}>
              <input {...register('payer_name')} className={inputCls} placeholder="Blue Cross" />
            </Field>
            <Field label="Payer Phone" error={errors.payer_phone?.message}>
              <input {...register('payer_phone')} className={inputCls} placeholder="+1 800 555 0100" />
            </Field>
          </div>
        </section>

        {/* Claim info */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-card space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Claim Details</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Claim Number" required error={errors.claim_number?.message}>
              <input {...register('claim_number')} className={inputCls} placeholder="CLM-2024-001" />
            </Field>
            <Field label="Service Date" error={errors.service_date?.message}>
              <input {...register('service_date')} type="date" className={inputCls} />
            </Field>
            <Field label="CPT Codes" error={errors.cpt_codes?.message}>
              <input {...register('cpt_codes')} className={inputCls} placeholder="99213, 85025" />
            </Field>
            <Field label="ICD-10 Codes" error={errors.icd10_codes?.message}>
              <input {...register('icd10_codes')} className={inputCls} placeholder="Z00.00, J06.9" />
            </Field>
            <Field label="Amount Billed ($)" error={errors.amount_billed_str?.message}>
              <input {...register('amount_billed_str')} type="number" step="0.01" className={inputCls} placeholder="250.00" />
            </Field>
          </div>
        </section>

        {/* Denial info */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-card space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Denial Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Denial Code" error={errors.denial_code?.message}>
              <input {...register('denial_code')} className={inputCls} placeholder="CO-4" />
            </Field>
            <Field label="Priority" error={errors.priority?.message}>
              <select {...register('priority')} className={inputCls}>
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </Field>
            <div className="sm:col-span-2">
              <Field label="Denial Reason" error={errors.denial_reason?.message}>
                <textarea
                  {...register('denial_reason')}
                  rows={2}
                  className={inputCls}
                  placeholder="Service not covered under current plan…"
                />
              </Field>
            </div>
          </div>
        </section>

        {/* Provider info */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-card space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Provider Information</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Provider Name" error={errors.provider_name?.message}>
              <input {...register('provider_name')} className={inputCls} placeholder="Dr. Jane Smith" />
            </Field>
            <Field label="Provider NPI" error={errors.provider_npi?.message}>
              <input {...register('provider_npi')} className={inputCls} placeholder="1234567890" />
            </Field>
          </div>
        </section>

        {/* Notes */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-card space-y-4">
          <Field label="Notes" error={errors.notes?.message}>
            <textarea
              {...register('notes')}
              rows={3}
              className={inputCls}
              placeholder="Additional context or follow-up instructions…"
            />
          </Field>
        </section>

        {/* Actions */}
        <div className="flex items-center gap-3 justify-end">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || createMutation.isPending}
            className="rounded-lg bg-primary px-6 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {isSubmitting || createMutation.isPending ? 'Creating…' : 'Create Case'}
          </button>
        </div>

        {createMutation.isError && (
          <p className="text-sm text-destructive text-center">
            Failed to create case. Please try again.
          </p>
        )}
      </form>
    </div>
  );
}
