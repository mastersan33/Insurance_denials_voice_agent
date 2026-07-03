import { useState } from 'react';
import { Download, FileText, Phone, MessageSquare } from 'lucide-react';
import { reportsApi } from '../services/endpoints';

interface ReportConfig {
  key: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  fn: (fmt: 'csv' | 'json') => Promise<{ data: Blob }>;
  filename: (fmt: string) => string;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const reports: ReportConfig[] = [
    {
      key: 'billing-cases',
      title: 'Billing Cases',
      description: 'All billing cases with patient, payer, claim, and denial details.',
      icon: <FileText className="h-5 w-5 text-primary" />,
      fn: (fmt) => reportsApi.billingCases(fmt) as Promise<{ data: Blob }>,
      filename: (fmt) => `billing_cases.${fmt}`,
    },
    {
      key: 'calls',
      title: 'Call Jobs',
      description: 'All call jobs with status, outcome, and attempt details.',
      icon: <Phone className="h-5 w-5 text-success" />,
      fn: (fmt) => reportsApi.calls(fmt) as Promise<{ data: Blob }>,
      filename: (fmt) => `calls.${fmt}`,
    },
    {
      key: 'transcripts',
      title: 'Transcripts',
      description: 'All conversation transcripts across all call sessions.',
      icon: <MessageSquare className="h-5 w-5 text-info" />,
      fn: (fmt) => reportsApi.transcripts(undefined, fmt) as Promise<{ data: Blob }>,
      filename: (fmt) => `transcripts.${fmt}`,
    },
  ];

  async function handleDownload(report: ReportConfig, fmt: 'csv' | 'json') {
    const key = `${report.key}-${fmt}`;
    setLoading((p) => ({ ...p, [key]: true }));
    try {
      const res = await report.fn(fmt);
      downloadBlob(res.data, report.filename(fmt));
    } catch {
      alert('Failed to download report. Please try again.');
    } finally {
      setLoading((p) => ({ ...p, [key]: false }));
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-foreground">Reports</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Export data as CSV or JSON</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {reports.map((report) => (
          <div key={report.key} className="rounded-xl border border-border bg-card p-5 shadow-card flex flex-col gap-4">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-muted p-2">{report.icon}</div>
              <div>
                <h2 className="text-sm font-semibold text-foreground">{report.title}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">{report.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-auto">
              {(['csv', 'json'] as const).map((fmt) => {
                const key = `${report.key}-${fmt}`;
                return (
                  <button
                    key={fmt}
                    disabled={loading[key]}
                    onClick={() => handleDownload(report, fmt)}
                    className="flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent disabled:opacity-50 transition-colors uppercase"
                  >
                    <Download className="h-3 w-3" />
                    {loading[key] ? '…' : fmt}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-card p-5 shadow-card">
        <h2 className="text-sm font-semibold text-foreground mb-3">Export Notes</h2>
        <ul className="space-y-1.5 text-xs text-muted-foreground">
          <li>• CSV files open directly in Excel, Google Sheets, or Numbers.</li>
          <li>• JSON files are UTF-8 encoded arrays suitable for data pipelines.</li>
          <li>• All exports include the full dataset with no row limit.</li>
          <li>• Export actions are recorded in the audit log.</li>
        </ul>
      </div>
    </div>
  );
}
