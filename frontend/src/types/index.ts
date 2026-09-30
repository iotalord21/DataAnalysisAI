export interface DatasetSummary {
  dataset_id: string;
  filename: string;
  file_path?: string;
  total_rows: number;
  total_columns: number;
  numeric_columns: string[];
  categorical_columns: string[];
  sample_rows: Record<string, any>[];
}

export interface PlanStep {
  id: string;
  title: string;
  analysis_type: string;
  description: string;
  hypothesis?: string;
  status: string;
}

export interface AnalysisResult {
  step_id: string;
  code: string;
  success: boolean;
  stdout: string;
  error?: string;
  result_data?: any;
  execution_time_ms: number;
}

export interface VisualizationSpec {
  id: string;
  title: string;
  chart_type: string;
  description: string;
  figure: {
    data: any[];
    layout: any;
    config?: any;
  };
}

export interface InsightItem {
  id: string;
  title: string;
  category: 'trend' | 'outlier' | 'correlation' | 'segment' | 'recommendation' | 'anomaly';
  finding: string;
  data_evidence: string;
  business_impact: string;
  confidence_score: number;
}

export interface VerificationResult {
  is_valid: boolean;
  score: number;
  checks_passed: string[];
  discrepancies: string[];
  replan_guidance?: string;
}

export interface AgentEvent {
  stage: string;
  agent: string;
  message: string;
  timestamp: number;
  details?: any;
}

export interface FinalReport {
  title: string;
  executive_summary: string;
  kpis: Array<{
    label: string;
    value: string;
    subtext?: string;
  }>;
  markdown_report: string;
}

export interface AnalysisState {
  status: 'idle' | 'uploading' | 'analyzing' | 'completed' | 'error';
  dataset?: DatasetSummary;
  plan: PlanStep[];
  events: AgentEvent[];
  analysisResults: AnalysisResult[];
  visualizations: VisualizationSpec[];
  insights: InsightItem[];
  verification?: VerificationResult;
  finalReport?: FinalReport;
  activeStage?: string;
  error?: string;
}

export interface MLModelResult {
  target_column: string;
  is_classification: boolean;
  metrics: {
    task: string;
    accuracy?: number;
    f1_score?: number;
    precision?: number;
    recall?: number;
    roc_auc?: number | null;
    r2_score?: number;
    rmse?: number;
    mae?: number;
    train_samples: number;
    test_samples: number;
  };
  feature_importances: Array<{
    feature: string;
    importance: number;
  }>;
  importance_chart: {
    data: any[];
    layout: any;
  };
  actionable_takeaways: string[];
  available_columns: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  code_executed?: string;
  stdout?: string;
  figure?: any;
  timestamp: number;
}

