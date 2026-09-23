import React, { useEffect, useRef, useState } from 'react';
import Plotly from 'plotly.js-dist-min';
import { Maximize2, Minimize2, Info, Download } from 'lucide-react';
import { VisualizationSpec } from '../types';

interface PlotlyChartProps {
  spec: VisualizationSpec;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({ spec }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !spec.figure) return;

    const baseLayout = spec.figure.layout || {};

    // Dark slate theme styling that matches the app aesthetic
    const themedLayout = {
      ...baseLayout,
      autosize: true,
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: {
        family: 'Plus Jakarta Sans, sans-serif',
        color: '#cbd5e1',
        size: 11,
      },
      title: {
        text: spec.title,
        font: {
          family: 'Plus Jakarta Sans, sans-serif',
          color: '#f8fafc',
          size: 14,
          weight: 700,
        },
      },
      margin: { t: 50, r: 20, l: 50, b: 50, ...baseLayout.margin },
      xaxis: {
        gridcolor: '#1e293b',
        zerolinecolor: '#334155',
        tickfont: { color: '#94a3b8' },
        ...baseLayout.xaxis,
      },
      yaxis: {
        gridcolor: '#1e293b',
        zerolinecolor: '#334155',
        tickfont: { color: '#94a3b8' },
        ...baseLayout.yaxis,
      },
      legend: {
        font: { color: '#cbd5e1' },
        ...baseLayout.legend,
      },
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
      toImageButtonOptions: {
        format: 'png',
        filename: spec.title.toLowerCase().replace(/\s+/g, '_'),
        height: 600,
        width: 1000,
        scale: 2,
      },
    };

    Plotly.newPlot(containerRef.current, spec.figure.data || [], themedLayout, config);

    const handleResize = () => {
      if (containerRef.current) {
        Plotly.Plots.resize(containerRef.current);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current) {
        Plotly.purge(containerRef.current);
      }
    };
  }, [spec, isFullscreen]);

  return (
    <div
      className={`rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md p-4 transition-all flex flex-col ${
        isFullscreen
          ? 'fixed inset-4 z-50 bg-slate-950 p-6 flex flex-col justify-between shadow-2xl'
          : 'relative hover:border-slate-700/80 shadow-lg'
      }`}
    >
      {/* Header Controls */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800/60">
            {spec.chart_type}
          </span>
          <h3 className="font-semibold text-sm text-slate-100 truncate max-w-[240px] sm:max-w-md">
            {spec.title}
          </h3>
        </div>

        <div className="flex items-center gap-1.5 text-slate-400">
          <button
            onClick={() => setShowInfo(!showInfo)}
            title="Chart description"
            className="p-1 rounded hover:bg-slate-800 hover:text-slate-200 transition"
          >
            <Info className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            className="p-1 rounded hover:bg-slate-800 hover:text-slate-200 transition"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {showInfo && (
        <div className="mb-3 p-3 rounded-lg bg-slate-800/50 text-xs text-slate-300 border border-slate-700/60">
          {spec.description}
        </div>
      )}

      {/* Chart Canvas */}
      <div
        ref={containerRef}
        className={`w-full ${isFullscreen ? 'flex-1 min-h-[500px]' : 'h-[360px]'}`}
      />
    </div>
  );
};
