"""
Unit tests for decision policy logic.
"""

import pytest
from risk_assessment.models import (
    Vulnerability,
    VulnerabilityAssessment,
    CriticalityAssessment,
    Severity,
    Criticality,
    Decision
)
from risk_assessment.decision_policy import make_decision, generate_final_summary


class TestDecisionPolicy:
    """Test suite for decision policy rules."""
    
    def test_no_vulnerabilities_approves(self):
        """Rule 1: No vulnerabilities → APPROVE"""
        vuln = VulnerabilityAssessment(
            software_name="Safe App",
            total_count=0,
            vulnerabilities=[],
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0},
            has_critical=False,
            has_high=False
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Safe App",
            criticality=Criticality.HIGH,
            reasoning="Important tool"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.APPROVE
        assert "No vulnerabilities" in reasoning
        assert "APPROVED" in reasoning
    
    def test_high_criticality_low_vulns_approves(self):
        """Rule 2: High criticality + only low-risk vulnerabilities → APPROVE"""
        vuln = VulnerabilityAssessment(
            software_name="Tool",
            total_count=2,
            vulnerabilities=[
                Vulnerability(severity=Severity.LOW, description="Minor issue"),
                Vulnerability(severity=Severity.LOW, description="Another minor")
            ],
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 2, "unknown": 0},
            has_critical=False,
            has_high=False
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Tool",
            criticality=Criticality.HIGH,
            reasoning="Critical business tool"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.APPROVE
        assert "low-risk" in reasoning.lower()
        assert "APPROVED" in reasoning
    
    def test_medium_criticality_low_vulns_approves(self):
        """Rule 2: Medium criticality + only low-risk vulnerabilities → APPROVE"""
        vuln = VulnerabilityAssessment(
            software_name="Tool",
            total_count=1,
            vulnerabilities=[
                Vulnerability(severity=Severity.LOW, description="Minor issue")
            ],
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 1, "unknown": 0},
            has_critical=False,
            has_high=False
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Tool",
            criticality=Criticality.MEDIUM,
            reasoning="Useful tool"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.APPROVE
    
    def test_critical_vulnerability_declines(self):
        """Rule 3: Critical vulnerability → DECLINE"""
        vuln = VulnerabilityAssessment(
            software_name="Risky App",
            total_count=1,
            vulnerabilities=[
                Vulnerability(severity=Severity.CRITICAL, description="RCE vulnerability")
            ],
            severity_counts={"critical": 1, "high": 0, "medium": 0, "low": 0, "unknown": 0},
            has_critical=True,
            has_high=False
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Risky App",
            criticality=Criticality.HIGH,
            reasoning="Important"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.DECLINE
        assert "DECLINED" in reasoning
        assert "critical" in reasoning.lower()
    
    def test_high_vulnerability_declines(self):
        """Rule 3: High severity vulnerability → DECLINE"""
        vuln = VulnerabilityAssessment(
            software_name="Risky App",
            total_count=2,
            vulnerabilities=[
                Vulnerability(severity=Severity.HIGH, description="SQL injection"),
                Vulnerability(severity=Severity.MEDIUM, description="XSS")
            ],
            severity_counts={"critical": 0, "high": 2, "medium": 0, "low": 0, "unknown": 0},
            has_critical=False,
            has_high=True
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Risky App",
            criticality=Criticality.LOW,
            reasoning="Not important"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.DECLINE
        assert "DECLINED" in reasoning
    
    def test_medium_vulnerability_declines(self):
        """Rule 3: Medium severity vulnerability → DECLINE"""
        vuln = VulnerabilityAssessment(
            software_name="App",
            total_count=1,
            vulnerabilities=[
                Vulnerability(severity=Severity.MEDIUM, description="Issue")
            ],
            severity_counts={"critical": 0, "high": 0, "medium": 1, "low": 0, "unknown": 0},
            has_critical=False,
            has_high=False
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="App",
            criticality=Criticality.HIGH,
            reasoning="Important"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.DECLINE
        assert "DECLINED" in reasoning
    
    def test_low_criticality_low_vulns_declines(self):
        """Rule 3: Low criticality + low vulnerabilities → DECLINE (not med-high)"""
        vuln = VulnerabilityAssessment(
            software_name="Tool",
            total_count=1,
            vulnerabilities=[
                Vulnerability(severity=Severity.LOW, description="Minor")
            ],
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 1, "unknown": 0},
            has_critical=False,
            has_high=False
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Tool",
            criticality=Criticality.LOW,  # Not medium-high!
            reasoning="Not important"
        )
        
        decision, reasoning = make_decision(vuln, crit)
        
        assert decision == Decision.DECLINE


class TestFinalSummary:
    """Test summary generation."""
    
    def test_summary_includes_all_components(self):
        """Test that summary includes all required information."""
        vuln = VulnerabilityAssessment(
            software_name="Test App",
            total_count=2,
            vulnerabilities=[
                Vulnerability(severity=Severity.LOW, description="Issue 1"),
                Vulnerability(severity=Severity.LOW, description="Issue 2")
            ],
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 2, "unknown": 0},
            has_critical=False,
            has_high=False,
            summary="Test summary"
        )
        crit = CriticalityAssessment(
            company_name="Test Co",
            software_name="Test App",
            criticality=Criticality.MEDIUM,
            reasoning="Useful tool"
        )
        decision = Decision.APPROVE
        reasoning = "Test reasoning"
        
        summary = generate_final_summary(decision, reasoning, vuln, crit)
        
        # Check all components are present
        assert "Test Co" in summary
        assert "Test App" in summary
        assert "APPROVE" in summary
        assert "Test summary" in summary
        assert "MEDIUM" in summary
        assert "Useful tool" in summary
        assert "Test reasoning" in summary
    
    def test_summary_format_is_markdown(self):
        """Test that summary is valid markdown."""
        vuln = VulnerabilityAssessment(
            software_name="App",
            total_count=0,
            summary="No issues"
        )
        crit = CriticalityAssessment(
            company_name="Co",
            software_name="App",
            criticality=Criticality.LOW,
            reasoning="Test"
        )
        
        summary = generate_final_summary(Decision.APPROVE, "OK", vuln, crit)
        
        # Check markdown elements
        assert "# Risk Assessment Report" in summary
        assert "**Company:**" in summary
        assert "**Software:**" in summary
        assert "**Decision:**" in summary
        assert "## Security Assessment" in summary
        assert "## Business Criticality Assessment" in summary
        assert "## Final Decision" in summary

