export interface BillingCase {
  id: string;
  patient_name: string;
  patient_dob: string | null;
  subscriber_id: string | null;
  payer_name: string;
  payer_phone: string | null;
  claim_number: string;
  service_date: string | null;
  cpt_codes: string | null;
  icd10_codes: string | null;
  amount_billed: number | null;
  denial_code: string | null;
  denial_reason: string | null;
  provider_name: string | null;
  provider_npi: string | null;
  status: string;
  priority: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface BillingCaseCreate {
  patient_name: string;
  payer_name: string;
  payer_phone?: string;
  claim_number: string;
  patient_dob?: string;
  subscriber_id?: string;
  service_date?: string;
  cpt_codes?: string;
  icd10_codes?: string;
  amount_billed?: number;
  denial_code?: string;
  denial_reason?: string;
  provider_name?: string;
  provider_npi?: string;
  priority?: string;
  notes?: string;
}

export interface BillingCaseUpdate {
  patient_name?: string;
  payer_name?: string;
  payer_phone?: string;
  claim_number?: string;
  denial_code?: string;
  denial_reason?: string;
  status?: string;
  priority?: string;
  notes?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
