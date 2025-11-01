"""
Unit tests for data models.
"""

import pytest
from pydantic import ValidationError
from risk_assessment.models import (
    Severity,
    Criticality,
    Decision,
    Vulnerability,
    VulnerabilityAssessment,
    CriticalityAssessment
)


class TestEnums:
    """Test enum definitions."""
    
    def test_severity_values(self):
        """Test Severity enum has correct values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.UNKNOWN.value == "unknown"
    
    def test_criticality_values(self):
        """Test Criticality enum has correct values."""
        assert Criticality.LOW.value == "low"
        assert Criticality.MEDIUM.value == "medium"
        assert Criticality.HIGH.value == "high"
    
    def test_decision_values(self):
        """Test Decision enum has correct values."""
        assert Decision.APPROVE.value == "approve"
        assert Decision.DECLINE.value == "decline"


class TestVulnerability:
    """Test Vulnerability model."""
    
    def test_create_vulnerability_minimal(self):
        """Test creating vulnerability with minimal fields."""
        vuln = Vulnerability(
            severity=Severity.HIGH,
            description="Test vulnerability"
        )
        assert vuln.severity == Severity.HIGH
        assert vuln.description == "Test vulnerability"
        assert vuln.cve_id is None
        assert vuln.published_date is None
    
    def test_create_vulnerability_full(self):
        """Test creating vulnerability with all fields."""
        vuln = Vulnerability(
            cve_id="CVE-2024-12345",
            severity=Severity.CRITICAL,
            description="Critical RCE vulnerability",
            published_date="2024-01-15"
        )
        assert vuln.cve_id == "CVE-2024-12345"
        assert vuln.severity == Severity.CRITICAL
        assert vuln.description == "Critical RCE vulnerability"
        assert vuln.published_date == "2024-01-15"
    
    def test_vulnerability_serialization(self):
        """Test vulnerability can be serialized to dict."""
        vuln = Vulnerability(
            severity=Severity.MEDIUM,
            description="Test"
        )
        data = vuln.model_dump()
        assert data["severity"] == "medium"
        assert data["description"] == "Test"


class TestVulnerabilityAssessment:
    """Test VulnerabilityAssessment model."""
    
    def test_create_assessment(self):
        """Test creating vulnerability assessment."""
        assessment = VulnerabilityAssessment(
            software_name="Test Software",
            vulnerabilities=[
                Vulnerability(severity=Severity.HIGH, description="Issue 1"),
                Vulnerability(severity=Severity.LOW, description="Issue 2")
            ],
            total_count=2,
            severity_counts={"critical": 0, "high": 1, "medium": 0, "low": 1, "unknown": 0},
            has_critical=False,
            has_high=True,
            summary="Found 2 vulnerabilities"
        )
        
        assert assessment.software_name == "Test Software"
        assert len(assessment.vulnerabilities) == 2
        assert assessment.total_count == 2
        assert assessment.has_high is True
        assert assessment.has_critical is False
    
    def test_assessment_default_values(self):
        """Test default values for optional fields."""
        assessment = VulnerabilityAssessment(
            software_name="Software"
        )
        assert assessment.vulnerabilities == []
        assert assessment.total_count == 0
        assert assessment.severity_counts == {}
        assert assessment.has_critical is False
        assert assessment.has_high is False


class TestCriticalityAssessment:
    """Test CriticalityAssessment model."""
    
    def test_create_criticality_assessment(self):
        """Test creating criticality assessment."""
        assessment = CriticalityAssessment(
            company_name="Test Company",
            software_name="Test Software",
            criticality=Criticality.HIGH,
            reasoning="This software is critical for operations"
        )
        
        assert assessment.company_name == "Test Company"
        assert assessment.software_name == "Test Software"
        assert assessment.criticality == Criticality.HIGH
        assert "critical for operations" in assessment.reasoning
    
    def test_criticality_levels(self):
        """Test all criticality levels work."""
        for level in [Criticality.LOW, Criticality.MEDIUM, Criticality.HIGH]:
            assessment = CriticalityAssessment(
                company_name="Co",
                software_name="Sw",
                criticality=level,
                reasoning="Test"
            )
            assert assessment.criticality == level

