"""
Decision policy for risk assessment.
Implements deterministic rules for approve/decline decisions.
"""

from .models import (
    Decision, 
    VulnerabilityAssessment, 
    CriticalityAssessment,
    Criticality
)


def make_decision(
    vulnerability_assessment: VulnerabilityAssessment,
    criticality_assessment: CriticalityAssessment
) -> tuple[Decision, str]:
    """
    Make approve/decline decision based on deterministic policy.
    
    Policy:
    1. If no vulnerabilities are found → Approve
    2. If app is medium-high importance and only low-risk vulnerabilities → Approve
    3. Otherwise → Decline
    
    Returns:
        Tuple of (Decision, reasoning)
    """
    vuln = vulnerability_assessment
    crit = criticality_assessment
    
    # Rule 1: No vulnerabilities → Approve
    if vuln.total_count == 0:
        reasoning = (
            f"✓ APPROVED: No vulnerabilities found for {vuln.software_name}. "
            f"The software appears to have a clean security record."
        )
        return Decision.APPROVE, reasoning
    
    # Check if only low-risk vulnerabilities exist
    has_only_low_risk = (
        not vuln.has_critical and 
        not vuln.has_high and
        vuln.severity_counts.get("medium", 0) == 0 and
        vuln.severity_counts.get("low", 0) > 0
    )
    
    # Rule 2: Medium-high importance AND only low-risk vulnerabilities → Approve
    if crit.criticality in [Criticality.MEDIUM, Criticality.HIGH] and has_only_low_risk:
        reasoning = (
            f"✓ APPROVED: {vuln.software_name} has {crit.criticality.value} business criticality "
            f"for {crit.company_name} and only {vuln.severity_counts.get('low', 0)} low-risk "
            f"vulnerabilit{'y' if vuln.severity_counts.get('low', 0) == 1 else 'ies'}. "
            f"The security risk is acceptable given the business value."
        )
        return Decision.APPROVE, reasoning
    
    # Rule 3: Otherwise → Decline
    risk_details = []
    if vuln.has_critical:
        risk_details.append(f"{vuln.severity_counts.get('critical', 0)} critical")
    if vuln.has_high:
        risk_details.append(f"{vuln.severity_counts.get('high', 0)} high")
    if vuln.severity_counts.get("medium", 0) > 0:
        risk_details.append(f"{vuln.severity_counts.get('medium', 0)} medium")
    if vuln.severity_counts.get("unknown", 0) > 0:
        risk_details.append(f"{vuln.severity_counts.get('unknown', 0)} unknown severity")
    
    # If we have vulnerabilities but no specific severity (edge case), mention count
    if not risk_details and vuln.total_count > 0:
        risk_summary = f"{vuln.total_count} vulnerabilit{'y' if vuln.total_count == 1 else 'ies'} with unclassified severity"
    else:
        risk_summary = " and ".join(risk_details) if risk_details else "security concerns"
    
    reasoning = (
        f"✗ DECLINED: {vuln.software_name} has {risk_summary}. "
        f"With {crit.criticality.value} business criticality for {crit.company_name}, "
        f"the security risk outweighs the business benefit."
    )
    
    return Decision.DECLINE, reasoning


def generate_final_summary(
    decision: Decision,
    decision_reasoning: str,
    vulnerability_assessment: VulnerabilityAssessment,
    criticality_assessment: CriticalityAssessment
) -> str:
    """Generate a comprehensive final summary."""
    
    summary_parts = [
        "# Risk Assessment Report",
        "",
        f"**Company:** {criticality_assessment.company_name}",
        f"**Software:** {vulnerability_assessment.software_name}",
        f"**Decision:** {decision.value.upper()}",
        "",
        "## Security Assessment",
        f"{vulnerability_assessment.summary}",
        "",
        f"**Vulnerabilities Found:** {vulnerability_assessment.total_count}",
    ]
    
    if vulnerability_assessment.total_count > 0:
        summary_parts.append("**Severity Distribution:**")
        for severity in ["critical", "high", "medium", "low"]:
            count = vulnerability_assessment.severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"  - {severity.capitalize()}: {count}")
    
    summary_parts.extend([
        "",
        "## Business Criticality Assessment",
        f"**Criticality Level:** {criticality_assessment.criticality.value.upper()}",
        "",
        f"**Reasoning:** {criticality_assessment.reasoning}",
        "",
        "## Final Decision",
        f"{decision_reasoning}",
        "",
    ])
    
    return "\n".join(summary_parts)

