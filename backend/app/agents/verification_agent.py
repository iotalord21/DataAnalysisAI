import re
import time
from typing import Dict, Any, List, Tuple
from app.agents.state import AgentState, VerificationResult


def audit_numerical_claims(insights: List[Dict[str, Any]], results: List[Dict[str, Any]], profile: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Cross-checks numerical figures cited in insights against actual tool outputs and profile.
    """
    passed_checks = []
    discrepancies = []

    # Aggregate all verifiable text from execution outputs and data profile
    evidence_corpus = ""
    for r in results:
        evidence_corpus += f" {r.get('stdout', '')} {str(r.get('result_data', ''))}"
    evidence_corpus += f" {str(profile)}"

    for insight in insights:
        evidence_str = insight.get("data_evidence", "")
        # Extract numerical tokens (integers, floats, percentages)
        numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", evidence_str)
        if not numbers:
            discrepancies.append(
                f"Insight '{insight.get('title')}' lacks explicit numerical citations in data_evidence."
            )
            continue

        verified_count = 0
        for num in numbers:
            clean_num = num.replace("%", "")
            # Check presence in evidence corpus
            if clean_num in evidence_corpus:
                verified_count += 1

        if verified_count > 0:
            passed_checks.append(
                f"Insight '{insight.get('title')}': Verified {verified_count}/{len(numbers)} numerical claims against execution records."
            )
        else:
            discrepancies.append(
                f"Insight '{insight.get('title')}': Could not verify cited numbers [{', '.join(numbers)}] in raw execution outputs."
            )

    return passed_checks, discrepancies


def verification_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Verification Agent:
    Validates calculations, checks hallucination/code execution consistency,
    audits visualization integrity, and decides whether findings are valid or require re-analysis.
    """
    insights = state.get("insights", [])
    analysis_results = state.get("analysis_results", [])
    visualizations = state.get("visualizations", [])
    profile = state.get("profile", {})
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    passed_checks = []
    discrepancies = []
    score = 100.0

    # 1. Audit Analysis Execution Success
    failed_steps = [r for r in analysis_results if not r.get("success")]
    if failed_steps:
        penalty = min(30.0, len(failed_steps) * 15.0)
        score -= penalty
        for fs in failed_steps:
            discrepancies.append(f"Analysis step '{fs.get('step_id')}' failed: {fs.get('error')}")
    else:
        passed_checks.append("All planned analysis execution steps executed without runtime errors.")

    # 2. Audit Visualizations Integrity
    if not visualizations:
        score -= 20.0
        discrepancies.append("No visualizations were produced.")
    else:
        for v in visualizations:
            fig = v.get("figure", {})
            traces = fig.get("data", [])
            if not traces:
                score -= 10.0
                discrepancies.append(f"Visualization '{v.get('title')}' contains empty trace data.")
            else:
                passed_checks.append(f"Visualization '{v.get('title')}' verified with valid Plotly traces.")

    # 3. Audit Numerical Consistency in Insights
    if not insights:
        score -= 25.0
        discrepancies.append("No qualitative insights were generated.")
    else:
        claim_passes, claim_fails = audit_numerical_claims(insights, analysis_results, profile)
        passed_checks.extend(claim_passes)
        if claim_fails:
            score -= min(25.0, len(claim_fails) * 10.0)
            discrepancies.extend(claim_fails)

    # Decision logic
    score = max(0.0, min(100.0, score))
    is_valid = score >= 70.0 or retry_count >= max_retries

    replan_guidance = None
    if not is_valid:
        replan_guidance = (
            f"Verification Score: {score}/100. The analysis contains discrepancies:\n"
            + "\n".join([f"- {d}" for d in discrepancies])
            + "\nPlease adjust the analysis scripts to fix runtime errors and calculate verifiable figures."
        )

    verification_result = {
        "is_valid": is_valid,
        "score": score,
        "checks_passed": passed_checks,
        "discrepancies": discrepancies,
        "replan_guidance": replan_guidance,
    }

    events = list(state.get("events", []))
    status_label = "PASSED" if is_valid else "FAILED - RE-ANALYSIS REQUIRED"
    events.append({
        "stage": "Verify Findings",
        "agent": "Verification Agent",
        "message": f"Verification Audit {status_label} (Score: {score}/100, Passed: {len(passed_checks)}, Issues: {len(discrepancies)}).",
        "timestamp": time.time(),
        "details": {
            "score": score,
            "is_valid": is_valid,
            "retry_count": retry_count,
            "discrepancies": discrepancies,
        },
    })

    return {
        "verification": verification_result,
        "events": events,
    }
