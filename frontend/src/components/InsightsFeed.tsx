import React from 'react';
import {
  TrendingUp,
  AlertOctagon,
  GitBranch,
  Layers,
  Sparkles,
  CheckCircle,
  HelpCircle,
} from 'lucide-react';
import { InsightItem } from '../types';

interface InsightsFeedProps {
  insights: InsightItem[];
}

const CATEGORY_CONFIG: Record<string, { label: string; icon: any; color: string; badge: string }> = {
  trend: {
    label: 'Trend',
    icon: TrendingUp,
    color: 'text-cyan-400',
    badge: 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60',
  },
  outlier: {
    label: 'Outlier',
    icon: AlertOctagon,
    color: 'text-amber-400',
    badge: 'bg-amber-950/60 text-amber-300 border-amber-800/60',
  },
  correlation: {
    label: 'Correlation',
    icon: GitBranch,
    color: 'text-indigo-400',
    badge: 'bg-indigo-950/60 text-indigo-300 border-indigo-800/60',
  },
  segment: {
    label: 'Segment',
    icon: Layers,
    color: 'text-purple-400',
    badge: 'bg-purple-950/60 text-purple-300 border-purple-800/60',
  },
  recommendation: {
    label: 'Takeaway',
    icon: Sparkles,
    color: 'text-emerald-400',
    badge: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60',
  },
};

export const InsightsFeed: React.FC<InsightsFeedProps> = ({ insights }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <span>Synthesized Strategic Insights</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
            {insights.length}
          </span>
        </h3>
        <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
          <CheckCircle className="w-3.5 h-3.5" />
          Validated by Verification Agent
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((item) => {
          const config = CATEGORY_CONFIG[item.category.toLowerCase()] || {
            label: item.category,
            icon: HelpCircle,
            color: 'text-slate-400',
            badge: 'bg-slate-800 text-slate-300 border-slate-700',
          };
          const Icon = config.icon;

          return (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-800/90 bg-slate-900/50 backdrop-blur-sm p-5 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
            >
              {/* Header */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span
                    className={`inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full border ${config.badge}`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {config.label}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Confidence: {Math.round((item.confidence_score || 0.95) * 100)}%
                  </span>
                </div>

                <h4 className="font-semibold text-slate-100 text-sm">{item.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{item.finding}</p>
              </div>

              {/* Data Evidence Callout */}
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800/60 font-mono text-[11px] text-slate-400 space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 block font-sans font-semibold">
                  Quantitative Evidence
                </span>
                <p className="text-indigo-300 font-medium">{item.data_evidence}</p>
              </div>

              {/* Business Impact */}
              {item.business_impact && (
                <div className="text-xs text-slate-400 pt-1 border-t border-slate-800/60 flex items-start gap-1.5">
                  <span className="font-semibold text-slate-300 flex-shrink-0">Strategic Impact:</span>
                  <span>{item.business_impact}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
