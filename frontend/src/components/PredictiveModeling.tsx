import React, { useState } from 'react';
import { Cpu, ArrowRight, CheckCircle2, TrendingUp, Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { MLModelResult, VisualizationSpec } from '../types';
import { api } from '../services/api';
import { PlotlyChart } from './PlotlyChart';

interface PredictiveModelingProps {
  datasetId: string;
  availableColumns: string[];
}

export const PredictiveModeling: React.FC<PredictiveModelingProps> = ({ datasetId, availableColumns }) => {
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MLModelResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrain = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.runPredictiveModeling(datasetId, selectedTarget || undefined);
      setResult(res);
      if (res.target_column && !selectedTarget) {
        setSelectedTarget(res.target_column);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to train predictive model.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-md space-y-6 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-800/80 flex items-center justify-center text-purple-400">
              <Cpu className="w-4 h-4" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              Predictive Machine Learning & Key Drivers
            </h3>
            <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-800">
              Random Forest
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Train an interpretable ML model to determine which features have the strongest predictive weight on your target outcome.
          </p>
        </div>

        {/* Target Selection & Trigger */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-400 font-medium">Target:</span>
            <select
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              disabled={loading}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="" className="bg-slate-900 text-slate-300">
                (Auto-Detect Target)
              </option>
              {availableColumns.map((col) => (
                <option key={col} value={col} className="bg-slate-900 text-slate-200">
                  {col}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleTrain}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition shadow-lg shadow-purple-600/20 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Training Model...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Train Predictive Model</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Model Training Results */}
      {result && (
        <div className="space-y-6 pt-2">
          {/* Performance Metric Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {result.is_classification ? (
              <>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.accuracy}%
                  </div>
                  <div className="text-xs font-semibold text-slate-300">Test Accuracy</div>
                  <div className="text-[10px] text-slate-500">Correct predictions on holdout</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.f1_score}%
                  </div>
                  <div className="text-xs font-semibold text-slate-300">F1-Score</div>
                  <div className="text-[10px] text-slate-500">Harmonic precision/recall balance</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.roc_auc !== null ? result.metrics.roc_auc : 'N/A'}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">ROC-AUC</div>
                  <div className="text-[10px] text-slate-500">Discrimination ability</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.train_samples + result.metrics.test_samples}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">Total Samples</div>
                  <div className="text-[10px] text-slate-500">
                    {result.metrics.train_samples} train / {result.metrics.test_samples} test
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.r2_score}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">R² Coefficient</div>
                  <div className="text-[10px] text-slate-500">Variance explained by model</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.rmse}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">RMSE</div>
                  <div className="text-[10px] text-slate-500">Root Mean Squared Error</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.mae}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">MAE</div>
                  <div className="text-[10px] text-slate-500">Mean Absolute Error</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center space-y-1">
                  <div className="text-2xl font-black text-purple-400 font-mono">
                    {result.metrics.train_samples + result.metrics.test_samples}
                  </div>
                  <div className="text-xs font-semibold text-slate-300">Total Samples</div>
                  <div className="text-[10px] text-slate-500">
                    {result.metrics.train_samples} train / {result.metrics.test_samples} test
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Feature Importance Chart & Strategic Takeaways */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            {/* Plotly Importance Chart */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <PlotlyChart
                spec={{
                  id: 'ml_importance_chart',
                  title: `Feature Importance for '${result.target_column}'`,
                  chart_type: 'feature_importance',
                  description: 'Gini feature importance ranking showing relative predictive contribution of top variables.',
                  figure: result.importance_chart,
                }}
              />
            </div>

            {/* Actionable Insights Callout */}
            <div className="space-y-4">
              <div className="rounded-2xl border border-purple-900/40 bg-purple-950/20 p-5 space-y-3">
                <div className="flex items-center gap-2 text-purple-300 font-bold text-sm">
                  <TrendingUp className="w-4 h-4" />
                  <span>Key Predictive Insights</span>
                </div>
                <ul className="space-y-2 text-xs text-slate-300">
                  {result.actionable_takeaways.map((takeaway, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-purple-400 font-bold">•</span>
                      <span>{takeaway}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Top 5 Feature Table */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                  Top 5 Predictive Drivers Ranking
                </h4>
                <div className="space-y-2">
                  {result.feature_importances.slice(0, 5).map((f, idx) => (
                    <div
                      key={f.feature}
                      className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-900/80 border border-slate-800/80"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-purple-950 text-purple-300 flex items-center justify-center font-mono text-[10px]">
                          {idx + 1}
                        </span>
                        <span className="font-semibold text-slate-200">{f.feature}</span>
                      </div>
                      <span className="font-mono text-purple-400 font-bold">
                        {f.importance}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
