import React, { useState } from 'react';
import {
  FileSearch,
  ListTodo,
  Terminal,
  PieChart,
  Lightbulb,
  ShieldCheck,
  FileText,
  CheckCircle2,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react';
import { AgentEvent, PlanStep, VerificationResult } from '../types';

interface AgentTimelineProps {
  events: AgentEvent[];
  plan: PlanStep[];
  verification?: VerificationResult;
  isAnalyzing: boolean;
}

const STAGES = [
  { id: 'Data Profiling', label: 'Data Profiling', icon: FileSearch, agent: 'Data Agent' },
  { id: 'Create Analysis Plan', label: 'Analysis Plan', icon: ListTodo, agent: 'Planner Agent' },
  { id: 'Execute Required Analyses', label: 'Execute Analyses', icon: Terminal, agent: 'Analysis Agent' },
  { id: 'Generate Visualizations', label: 'Visualizations', icon: PieChart, agent: 'Viz Agent' },
  { id: 'Generate Insights', label: 'Synthesize Insights', icon: Lightbulb, agent: 'Insight Agent' },
  { id: 'Verify Findings', label: 'Verification Audit', icon: ShieldCheck, agent: 'Verification Agent' },
  { id: 'Final Report', label: 'Final Report', icon: FileText, agent: 'Report Agent' },
];

export const AgentTimeline: React.FC<AgentTimelineProps> = ({
  events,
  plan,
  verification,
  isAnalyzing,
}) => {
  const [showConsole, setShowConsole] = useState(true);

  // Identify latest completed and active stages
  const executedStages = new Set(events.map((e) => e.stage));
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;
  const currentActiveStage = isAnalyzing && latestEvent ? latestEvent.stage : null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur-md space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span>Agentic Orchestration Cycle</span>
            {isAnalyzing && (
              <span className="flex items-center gap-1.5 text-xs text-indigo-400 font-normal normal-case">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Autonomous loop executing...
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-500">Plan → Act → Observe → Verify → Re-plan → Report</p>
        </div>

        <button
          onClick={() => setShowConsole(!showConsole)}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <span>{showConsole ? 'Hide Console Logs' : 'View Console Logs'}</span>
          {showConsole ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Visual Stage Stepper */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isDone = executedStages.has(stage.id) && currentActiveStage !== stage.id;
          const isActive = currentActiveStage === stage.id;

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-xl border transition-all flex flex-col justify-between gap-2 ${
                isActive
                  ? 'border-indigo-500 bg-indigo-950/40 ring-1 ring-indigo-500/50'
                  : isDone
                  ? 'border-slate-800 bg-slate-950/60 text-slate-200'
                  : 'border-slate-800/40 bg-slate-950/20 text-slate-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                    isActive
                      ? 'bg-indigo-600 text-white'
                      : isDone
                      ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                      : 'bg-slate-900 text-slate-600'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                ) : (
                  <span className="text-[10px] font-mono text-slate-600">0{idx + 1}</span>
                )}
              </div>

              <div>
                <p className={`text-xs font-semibold ${isActive ? 'text-indigo-200' : isDone ? 'text-slate-200' : 'text-slate-500'}`}>
                  {stage.label}
                </p>
                <p className="text-[10px] text-slate-500 truncate">{stage.agent}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Agent Console Log Drawer */}
      {showConsole && (
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs space-y-2 max-h-60 overflow-y-auto">
          <div className="flex items-center justify-between pb-2 border-b border-slate-900 text-[11px] text-slate-500">
            <span>TERMINAL LOG STREAM</span>
            <span>{events.length} agent events logged</span>
          </div>

          {events.length === 0 ? (
            <p className="text-slate-600 italic">Awaiting pipeline initialization...</p>
          ) : (
            <div className="space-y-1.5">
              {events.map((ev, i) => (
                <div key={i} className="flex items-start gap-2 text-slate-300">
                  <span className="text-slate-600 flex-shrink-0">
                    {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-900 text-indigo-400 border border-slate-800 flex-shrink-0 text-[10px]">
                    {ev.agent}
                  </span>
                  <span className="text-slate-300 break-words">{ev.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
