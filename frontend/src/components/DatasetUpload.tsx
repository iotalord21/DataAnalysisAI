import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, ArrowRight, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { DatasetSummary } from '../types';
import { api } from '../services/api';

interface DatasetUploadProps {
  onDatasetReady: (dataset: DatasetSummary, query: string) => void;
  isLoading: boolean;
}

const PRESET_QUERIES = [
  "Analyze the primary drivers of customer churn and identify high-risk segments.",
  "Perform comprehensive statistical distribution, outlier detection, and correlation analysis.",
  "Which contract types and payment methods exhibit the highest variance in charges?",
];

export const DatasetUpload: React.FC<DatasetUploadProps> = ({ onDatasetReady, isLoading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<DatasetSummary | null>(null);
  const [query, setQuery] = useState(PRESET_QUERIES[0]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const summary = await api.uploadDataset(file);
      setSelectedDataset(summary);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and profile dataset.');
    } finally {
      setUploading(false);
    }
  };

  const loadSample = async () => {
    setError(null);
    setUploading(true);
    try {
      const summary = await api.loadSample('customer_churn');
      setSelectedDataset(summary);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load sample dataset.');
    } finally {
      setUploading(false);
    }
  };

  const handleStart = () => {
    if (selectedDataset && query.trim()) {
      onDatasetReady(selectedDataset, query.trim());
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8 px-4">
      {/* Hero Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-medium text-indigo-400">
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous Multi-Agent Analytics
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
          Data Analysis <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-400 bg-clip-text text-transparent">Agent</span>
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
          Upload any CSV or Excel file. Our team of specialized agents will automatically profile, formulate hypotheses, execute Python/SQL statistics, generate Plotly charts, and audit findings for verified accuracy.
        </p>
      </div>

      {/* Upload Zone */}
      {!selectedDataset ? (
        <div className="space-y-4">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-indigo-500 bg-indigo-950/20 scale-[1.01]'
                : 'border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileInput}
              className="hidden"
            />
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <p className="text-base font-semibold text-white">
                  Drop your CSV or Excel file here, or <span className="text-indigo-400 hover:underline">browse</span>
                </p>
                <p className="text-xs text-slate-400">Supports .csv, .xlsx, .xls</p>
              </div>
            </div>
          </div>

          {/* Quick Demo Sample Button */}
          <div className="flex items-center justify-center gap-3">
            <span className="text-xs text-slate-500">Don't have a dataset ready?</span>
            <button
              onClick={loadSample}
              disabled={uploading}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-950 text-indigo-300 border border-indigo-800/80 hover:bg-indigo-900/60 transition flex items-center gap-1.5"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              Load Sample: SaaS Customer Churn Dataset
            </button>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-300 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      ) : (
        /* Dataset Loaded & Query Form */
        <div className="space-y-6 bg-slate-900/70 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-sm">
          {/* File Card Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">{selectedDataset.filename}</h3>
                <p className="text-xs text-slate-400">
                  {selectedDataset.total_rows.toLocaleString()} rows • {selectedDataset.total_columns} columns ({selectedDataset.numeric_columns.length} numeric, {selectedDataset.categorical_columns.length} categorical)
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelectedDataset(null)}
              className="text-xs text-slate-400 hover:text-slate-200 underline"
            >
              Choose different file
            </button>
          </div>

          {/* Quick Table Preview */}
          <div className="space-y-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Data Sample Preview</span>
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    {Object.keys(selectedDataset.sample_rows[0] || {}).slice(0, 7).map((col) => (
                      <th key={col} className="px-3 py-2 font-medium">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {selectedDataset.sample_rows.slice(0, 3).map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/30">
                      {Object.keys(selectedDataset.sample_rows[0] || {}).slice(0, 7).map((col) => (
                        <td key={col} className="px-3 py-2 whitespace-nowrap">
                          {row[col] !== null ? String(row[col]) : <span className="text-slate-600">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Query Input */}
          <div className="space-y-3 pt-2">
            <label className="block text-sm font-medium text-slate-200">
              What would you like the agents to analyze?
            </label>
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Identify correlation between revenue and tenure, detect outliers, and generate key takeaways..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm text-slate-100 placeholder:text-slate-600 outline-none transition"
            />

            {/* Prompt Chips */}
            <div className="space-y-1.5">
              <span className="text-xs text-slate-500">Suggested questions:</span>
              <div className="flex flex-wrap gap-2">
                {PRESET_QUERIES.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setQuery(q)}
                    className="text-xs px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition text-left"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-4 flex justify-end">
            <button
              onClick={handleStart}
              disabled={isLoading || !query.trim()}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 font-semibold text-white shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
            >
              <span>Launch Multi-Agent Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
