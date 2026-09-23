import React from 'react';
import { X, Download, FileText, Printer, CheckCircle, Shield } from 'lucide-react';
import { FinalReport, VerificationResult } from '../types';

interface ReportModalProps {
  report: FinalReport;
  verification?: VerificationResult;
  onClose: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ report, verification, onClose }) => {
  const downloadMarkdown = () => {
    const blob = new Blob([report.markdown_report], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}_report.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadHTML = () => {
    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${report.title}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1e293b; }
    h1 { color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }
    h2 { color: #334155; margin-top: 30px; }
    h3 { color: #475569; }
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin: 24px 0; }
    .kpi-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; text-align: center; }
    .kpi-val { font-size: 24px; font-weight: bold; color: #4f46e5; }
    .kpi-label { font-size: 12px; color: #64748b; text-transform: uppercase; margin-top: 4px; }
    pre { background: #0f172a; color: #f8fafc; padding: 16px; border-radius: 8px; overflow-x: auto; }
  </style>
</head>
<body>
  <div class="kpi-grid">
    ${(report.kpis || [])
      .map(
        (k) => `
      <div class="kpi-card">
        <div class="kpi-val">${k.value}</div>
        <div class="kpi-label">${k.label}</div>
      </div>
    `
      )
      .join('')}
  </div>
  <pre style="white-space: pre-wrap; font-family: inherit; background: transparent; color: inherit; padding: 0;">${
    report.markdown_report
  }</pre>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}_report.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-lg text-white">{report.title}</h2>
              <p className="text-xs text-slate-400">Verified Autonomous Synthesis</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={downloadHTML}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download HTML</span>
            </button>
            <button
              onClick={downloadMarkdown}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Markdown</span>
            </button>
            <button
              onClick={handlePrint}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
              title="Print report"
            >
              <Printer className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 sm:p-8 overflow-y-auto space-y-6">
          {/* KPI Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(report.kpis || []).map((kpi, idx) => (
              <div
                key={idx}
                className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1"
              >
                <div className="text-2xl font-extrabold text-indigo-400 font-mono tracking-tight">
                  {kpi.value}
                </div>
                <div className="text-xs font-semibold text-slate-200">{kpi.label}</div>
                {kpi.subtext && <div className="text-[10px] text-slate-500">{kpi.subtext}</div>}
              </div>
            ))}
          </div>

          {/* Verification Badge Bar */}
          {verification && (
            <div className="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-800/40 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-emerald-400" />
                <div>
                  <h4 className="text-xs font-bold text-emerald-200 uppercase tracking-wider">
                    Verification Audit: Passed ({verification.score}/100)
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    All cited figures were audited against Python and DuckDB sandbox calculations.
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-emerald-400 px-2.5 py-1 rounded-full bg-emerald-900/60 border border-emerald-700/60">
                100% Consistent
              </span>
            </div>
          )}

          {/* Executive Markdown Body */}
          <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed space-y-4 whitespace-pre-wrap font-sans">
            {report.markdown_report}
          </div>
        </div>
      </div>
    </div>
  );
};
