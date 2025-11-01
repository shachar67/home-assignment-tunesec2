"""
Data models for the risk assessment workflow.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """CVE severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Criticality(str, Enum):
    """Business criticality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(str, Enum):
    """Risk assessment decision."""
    APPROVE = "approve"
    DECLINE = "decline"


class Vulnerability(BaseModel):
    """Represents a single vulnerability/CVE."""
    cve_id: Optional[str] = None
    severity: Severity
    cvss_score: Optional[float] = None  # CVSS numeric score (0.0-10.0)
    description: str
    published_date: Optional[str] = None
    source_url: Optional[str] = None  # Where this information was found


class VulnerabilityAssessment(BaseModel):
    """Results of vulnerability assessment."""
    software_name: str
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    total_count: int = 0
    severity_counts: dict = Field(default_factory=dict)
    has_critical: bool = False
    has_high: bool = False
    security_update_cadence: str = "unknown"
    summary: str = ""
    source_data: List[dict] = Field(default_factory=list)  # Raw search results for verification
    software_exists: bool = True  # Whether software was verified to exist
    existence_confidence: str = "unknown"  # Confidence level: high, low, none, unknown


class CriticalityAssessment(BaseModel):
    """Results of business criticality assessment."""
    company_name: str
    software_name: str
    criticality: Criticality
    reasoning: str
    # Chain-of-thought reasoning fields
    company_business: Optional[str] = None
    software_purpose: Optional[str] = None
    relevance: Optional[str] = None
    impact_if_unavailable: Optional[str] = None


class RiskAssessmentState(BaseModel):
    """State of the risk assessment workflow."""
    # Input
    company_name: str
    software_name: str
    
    # Assessment results
    vulnerability_assessment: Optional[VulnerabilityAssessment] = None
    criticality_assessment: Optional[CriticalityAssessment] = None
    
    # Decision
    decision: Optional[Decision] = None
    decision_reasoning: str = ""
    final_summary: str = ""
    
    # Metadata
    traces: List[dict] = Field(default_factory=list)


class RiskAssessmentOutput(BaseModel):
    """Final output of the risk assessment."""
    company_name: str
    software_name: str
    decision: Decision
    vulnerability_summary: str
    criticality_level: Criticality
    criticality_reasoning: str
    final_summary: str
    traces: List[dict] = Field(default_factory=list)
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)  # Detailed vuln list with sources
    source_urls: List[dict] = Field(default_factory=list)  # URLs where data came from
    software_exists: bool = True  # Whether software was verified to exist
    existence_confidence: str = "unknown"  # Confidence level: high, low, none, unknown
    # Chain-of-thought reasoning fields from criticality assessment
    company_business: Optional[str] = None
    software_purpose: Optional[str] = None
    relevance: Optional[str] = None
    impact_if_unavailable: Optional[str] = None

