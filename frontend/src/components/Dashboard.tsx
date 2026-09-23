import React, { useState } from 'react';
import {
  FileText,
  BarChart3,
  Lightbulb,
  CheckCircle2,
  AlertTriangle,
  Download,
  Share2,
} from 'lucide-react';
import { AnalysisState } from '../types';
import { PlotlyChart } from './PlotlyChart';
import { InsightsFeed } from './InsightsFeed';
import { CodeViewer } from './CodeViewer';
import { ReportModal } from './ReportModal';

interface DashboardProps {
  state: AnalysisState;
}

export const Dashboard: React.FC<DashboardProps> = ({ state }) => {
  const [showReportModal, setShowReportModal] = useState(false);

  const {
    dataset,
    visualizations,
    insights,
    analysisResults,
    verification,
    finalReport,
    plan,
  } = state;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Summary Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-md flex flex-wrap items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800/80">
              Analysis Results
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Dataset: {dataset?.filename} ({dataset?.total_rows.toLocaleString()} rows)
            </span>
          </div>

          <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            {finalReport?.title || 'Exploratory & Predictive Analytical Synthesis'}
          </h2>

          <p className="text-xs sm:text-sm text-slate-300">
            {finalReport?.executive_summary ||
              'Autonomous data analysis workflow concluded with verified statistical observations and visual representations.'}
          </p>
        </div>

        {/* Action Button: View Full Executive Report */}
        {finalReport && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowReportModal(true)}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-indigo-600/30 transition"
            >
              <FileText className="w-4 h-4" />
              <span>View Executive Report</span>
            </button>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      {finalReport?.kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {finalReport.kpis.map((kpi, idx) => (
            <div
              key={idx}
              className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm space-y-1 hover:border-slate-700 transition"
            >
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                {kpi.label}
              </span>
              <div className="text-2xl font-black text-white font-mono">{kpi.value}</div>
              {kpi.subtext && <p className="text-[11px] text-slate-500">{kpi.subtext}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Visualizations Grid */}
      {visualizations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <span>Interactive Data Visualizations</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {visualizations.length}
              </span>
            </h3>
            <span className="text-xs text-slate-400 hidden sm:block">
              Fully interactive Plotly specifications (Zoom, pan, hover & export)
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {visualizations.map((spec) => (
              <PlotlyChart key={spec.id} spec={spec} />
            ))}
          </div>
        </div>
      )}

      {/* Insights Feed */}
      {insights.length > 0 && <InsightsFeed insights={insights} />}

      {/* Code Execution Viewer */}
      {analysisResults.length > 0 && (
        <CodeViewer results={analysisResults} plan={plan} />
      )}

      {/* Report Modal */}
      {showReportModal && finalReport && (
        <ReportModal
          report={finalReport}
          verification={verification}
          onClose={() => setShowReportModal(false)}
        />
      )}
    </div>
  );
};
