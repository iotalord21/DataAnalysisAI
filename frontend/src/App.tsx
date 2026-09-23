import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { DatasetUpload } from './components/DatasetUpload';
import { AgentTimeline } from './components/AgentTimeline';
import { Dashboard } from './components/Dashboard';
import { AnalysisState, DatasetSummary } from './types';
import { api } from './services/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [state, setState] = useState<AnalysisState>({
    status: 'idle',
    plan: [],
    events: [],
    analysisResults: [],
    visualizations: [],
    insights: [],
  });

  const handleDatasetReady = async (dataset: DatasetSummary, query: string) => {
    setState((prev) => ({
      ...prev,
      status: 'analyzing',
      dataset,
      plan: [],
      events: [],
      analysisResults: [],
      visualizations: [],
      insights: [],
      verification: undefined,
      finalReport: undefined,
      error: undefined,
    }));

    // Start SSE stream
    try {
      const cancelStream = api.streamAnalysis(
        dataset.dataset_id,
        query,
        (update) => {
          setState((prev) => ({
            ...prev,
            events: update.events || prev.events,
            plan: update.plan || prev.plan,
            visualizations: update.visualizations || prev.visualizations,
            insights: update.insights || prev.insights,
            verification: update.verification || prev.verification,
            finalReport: update.final_report || prev.finalReport,
          }));
        },
        (complete) => {
          setState((prev) => ({
            ...prev,
            status: 'completed',
            events: complete.events || prev.events,
            plan: complete.plan || prev.plan,
            analysisResults: complete.analysis_results || prev.analysisResults,
            visualizations: complete.visualizations || prev.visualizations,
            insights: complete.insights || prev.insights,
            verification: complete.verification || prev.verification,
            finalReport: complete.final_report || prev.finalReport,
          }));
        },
        async (streamError) => {
          console.warn('SSE streaming encountered an issue. Falling back to direct execution...', streamError);
          try {
            const result = await api.runAnalysis(dataset.dataset_id, query);
            setState((prev) => ({
              ...prev,
              status: 'completed',
              events: result.events || prev.events,
              plan: result.plan || prev.plan,
              analysisResults: result.analysis_results || prev.analysisResults,
              visualizations: result.visualizations || prev.visualizations,
              insights: result.insights || prev.insights,
              verification: result.verification || prev.verification,
              finalReport: result.final_report || prev.finalReport,
            }));
          } catch (err: any) {
            setState((prev) => ({
              ...prev,
              status: 'error',
              error: err.response?.data?.detail || err.message || 'Analysis failed to complete.',
            }));
          }
        }
      );
    } catch (e: any) {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: e.message || 'Failed to initiate agent workflow.',
      }));
    }
  };

  const handleReset = () => {
    setState({
      status: 'idle',
      plan: [],
      events: [],
      analysisResults: [],
      visualizations: [],
      insights: [],
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        onReset={handleReset}
        hasActiveSession={state.status !== 'idle'}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
        {state.status === 'idle' && (
          <DatasetUpload
            onDatasetReady={handleDatasetReady}
            isLoading={false}
          />
        )}

        {(state.status === 'analyzing' || state.status === 'completed') && (
          <div className="space-y-8">
            <AgentTimeline
              events={state.events}
              plan={state.plan}
              verification={state.verification}
              isAnalyzing={state.status === 'analyzing'}
            />

            {(state.status === 'completed' || state.visualizations.length > 0) && (
              <Dashboard state={state} />
            )}
          </div>
        )}

        {state.status === 'error' && (
          <div className="max-w-xl mx-auto p-6 rounded-2xl bg-red-950/40 border border-red-800/60 text-center space-y-4">
            <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
            <div>
              <h3 className="text-base font-bold text-red-200">Analysis Encountered an Error</h3>
              <p className="text-xs text-red-300 mt-1">{state.error}</p>
            </div>
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded-xl bg-red-900/80 hover:bg-red-800 text-white text-xs font-semibold transition inline-flex items-center gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try Again with New Dataset</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
