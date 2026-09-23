from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: str
    title: str
    analysis_type: str = Field(
        ...,
        description="One of: statistics, correlation, trends, outliers, segmentation, custom"
    )
    description: str
    hypothesis: Optional[str] = None
    status: str = "pending"


class AnalysisResult(BaseModel):
    step_id: str
    code: str
    success: bool
    stdout: str = ""
    error: Optional[str] = None
    result_data: Optional[Any] = None
    execution_time_ms: float = 0.0


class VisualizationSpec(BaseModel):
    id: str
    title: str
    chart_type: str
    description: str
    figure: Dict[str, Any]


class InsightItem(BaseModel):
    id: str
    title: str
    category: str = Field(
        ...,
        description="One of: trend, outlier, correlation, segment, recommendation, anomaly"
    )
    finding: str
    data_evidence: str
    business_impact: str
    confidence_score: float = 0.95


class VerificationResult(BaseModel):
    is_valid: bool
    score: float = 100.0
    checks_passed: List[str] = []
    discrepancies: List[str] = []
    replan_guidance: Optional[str] = None


class AgentEvent(BaseModel):
    stage: str
    agent: str
    message: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None


class FinalReport(BaseModel):
    title: str
    executive_summary: str
    kpis: List[Dict[str, Any]] = []
    detailed_findings: str
    recommendations: List[str] = []
    methodology_notes: str
    markdown_report: str


class AgentState(TypedDict):
    dataset_id: str
    file_path: str
    user_query: str
    profile: Dict[str, Any]
    profile_summary: str
    plan: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    visualizations: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    verification: Optional[Dict[str, Any]]
    retry_count: int
    max_retries: int
    events: List[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    error: Optional[str]
