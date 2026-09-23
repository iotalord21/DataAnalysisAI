import React, { useState } from 'react';
import { Terminal, Code, Clock, CheckCircle2, XCircle, Copy, Check } from 'lucide-react';
import { AnalysisResult, PlanStep } from '../types';

interface CodeViewerProps {
  results: AnalysisResult[];
  plan: PlanStep[];
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ results, plan }) => {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [copied, setCopied] = useState(false);

  if (results.length === 0) return null;

  const currentResult = results[selectedIdx] || results[0];
  const matchingPlan = plan.find((p) => p.id === currentResult.step_id);

  const handleCopy = () => {
    navigator.clipboard.writeText(currentResult.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-indigo-400" />
          <h3 className="font-bold text-sm text-slate-100">Reproducible Code Execution Audit</h3>
          <span className="text-xs text-slate-500 font-mono">({results.length} scripts run)</span>
        </div>

        {/* Step Selector Tabs */}
        <div className="flex flex-wrap gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
          {results.map((res, i) => (
            <button
              key={i}
              onClick={() => setSelectedIdx(i)}
              className={`px-3 py-1 rounded-lg text-xs font-mono transition flex items-center gap-1.5 ${
                selectedIdx === i
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {res.success ? (
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              ) : (
                <XCircle className="w-3 h-3 text-red-400" />
              )}
              <span>Step {i + 1}</span>
            </button>
          ))}
        </div>
      </div>

      {matchingPlan && (
        <div className="text-xs text-slate-400 bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
          <span className="font-semibold text-slate-200">{matchingPlan.title}:</span>{' '}
          {matchingPlan.description}
        </div>
      )}

      {/* Code Editor Frame */}
      <div className="rounded-xl border border-slate-800 bg-slate-950 overflow-hidden font-mono text-xs">
        <div className="flex items-center justify-between px-4 py-2 bg-slate-900/90 border-b border-slate-800 text-slate-400">
          <div className="flex items-center gap-2">
            <Code className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-[11px] text-slate-300 font-semibold">sandbox_worker.py</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-[11px] text-slate-400">
              <Clock className="w-3 h-3" />
              {currentResult.execution_time_ms}ms
            </span>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-0.5 rounded hover:bg-slate-800 text-[11px] text-slate-300 transition"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        </div>

        <pre className="p-4 text-slate-200 overflow-x-auto leading-relaxed max-h-72">
          <code>{currentResult.code}</code>
        </pre>

        {/* Stdout Output Console */}
        {currentResult.stdout && (
          <div className="border-t border-slate-800 bg-slate-950/90 p-3">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block mb-1">
              Standard Output (stdout)
            </span>
            <pre className="text-slate-300 font-mono text-[11px] overflow-x-auto max-h-36 whitespace-pre-wrap">
              {currentResult.stdout}
            </pre>
          </div>
        )}

        {currentResult.error && (
          <div className="border-t border-red-900/40 bg-red-950/20 p-3 text-red-300 text-xs">
            <span className="font-bold">Error:</span> {currentResult.error}
          </div>
        )}
      </div>
    </div>
  );
};
