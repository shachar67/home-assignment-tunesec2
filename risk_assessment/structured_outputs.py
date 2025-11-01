"""
Structured output models for LLM responses using Pydantic.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .models import Criticality


class VulnerabilityItem(BaseModel):
    """Individual vulnerability with confidence scoring."""
    cve_id: str = Field(description="CVE identifier (e.g., CVE-2024-1234)")
    severity: str = Field(description="Severity level: critical, high, medium, low")
    cvss_score: Optional[float] = Field(None, description="CVSS score if available (0.0-10.0)")
    description: str = Field(description="Brief description of the vulnerability")
    source_number: int = Field(description="Which search result this came from (1-based index)")
    confidence: str = Field(
        description="Confidence that this CVE applies to the target software: high, medium, low",
        pattern="^(high|medium|low)$"
    )
    reasoning: str = Field(
        description="One sentence explaining why this CVE matches the software"
    )


class VulnerabilityAnalysisOutput(BaseModel):
    """Structured output for vulnerability analysis with confidence scoring."""
    
    vulnerabilities: List[VulnerabilityItem] = Field(
        description="List of identified vulnerabilities with confidence scores",
        default_factory=list
    )
    security_update_cadence: str = Field(
        description="How frequently security updates are released: frequent, moderate, infrequent, or unknown",
        pattern="^(frequent|moderate|infrequent|unknown)$"
    )
    overall_confidence: str = Field(
        description="Overall confidence in the vulnerability analysis: high, medium, low",
        pattern="^(high|medium|low)$",
        default="medium"
    )


class CriticalityAnalysisOutput(BaseModel):
    """Structured output for criticality analysis with chain-of-thought."""
    
    # Flattened chain-of-thought fields (nested models cause issues with some LLMs)
    company_business: str = Field(
        description="Brief description of company's primary business"
    )
    software_purpose: str = Field(
        description="Brief description of what the software does"
    )
    relevance: str = Field(
        description="How the software relates to the company's business"
    )
    impact_if_unavailable: str = Field(
        description="What would happen if software was unavailable"
    )
    
    criticality_level: Criticality = Field(
        description="Business criticality level: low, medium, or high"
    )
    reasoning: str = Field(
        description="2-3 sentences explaining why this criticality level was assigned"
    )
    confidence: str = Field(
        description="Confidence in this assessment: high, medium, low",
        pattern="^(high|medium|low)$",
        default="medium"
    )

