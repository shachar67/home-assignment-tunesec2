"""
Unit tests for CVE database client.
"""

import pytest
from risk_assessment.cve_client import CVEDatabaseClient


class TestCVEDatabaseClient:
    """Test CVE database client."""
    
    def test_client_initialization(self):
        """Test client can be initialized."""
        client = CVEDatabaseClient()
        assert client.nvd_base_url == "https://services.nvd.nist.gov/rest/json/cves/2.0"
        assert client.api_key is None
    
    def test_client_with_api_key(self):
        """Test client initialization with API key."""
        client = CVEDatabaseClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert "apiKey" in client.session.headers
    
    def test_v2_score_to_severity(self):
        """Test CVSS v2 score conversion."""
        client = CVEDatabaseClient()
        
        assert client._v2_score_to_severity(9.0) == "high"
        assert client._v2_score_to_severity(7.5) == "high"
        assert client._v2_score_to_severity(6.0) == "medium"
        assert client._v2_score_to_severity(4.0) == "medium"
        assert client._v2_score_to_severity(3.0) == "low"
        assert client._v2_score_to_severity(0.5) == "low"
        assert client._v2_score_to_severity(0.0) == "unknown"
    
    def test_extract_severity_v31(self):
        """Test severity extraction from CVSS v3.1."""
        client = CVEDatabaseClient()
        
        metrics = {
            "cvssMetricV31": [{
                "cvssData": {
                    "baseSeverity": "HIGH"
                }
            }]
        }
        
        severity = client._extract_severity(metrics)
        assert severity == "high"
    
    def test_extract_severity_v30_fallback(self):
        """Test severity extraction falls back to CVSS v3.0."""
        client = CVEDatabaseClient()
        
        metrics = {
            "cvssMetricV30": [{
                "cvssData": {
                    "baseSeverity": "CRITICAL"
                }
            }]
        }
        
        severity = client._extract_severity(metrics)
        assert severity == "critical"
    
    def test_extract_severity_v2_fallback(self):
        """Test severity extraction falls back to CVSS v2."""
        client = CVEDatabaseClient()
        
        metrics = {
            "cvssMetricV2": [{
                "cvssData": {
                    "baseScore": 8.5
                }
            }]
        }
        
        severity = client._extract_severity(metrics)
        assert severity == "high"
    
    def test_extract_severity_unknown(self):
        """Test unknown severity when no metrics available."""
        client = CVEDatabaseClient()
        
        severity = client._extract_severity({})
        assert severity == "unknown"
    
    def test_parse_cve_data(self):
        """Test parsing CVE data from NVD response."""
        client = CVEDatabaseClient()
        
        nvd_response = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-12345",
                        "descriptions": [
                            {"lang": "en", "value": "Test vulnerability"}
                        ],
                        "published": "2024-01-15T10:00:00.000",
                        "metrics": {
                            "cvssMetricV31": [{
                                "cvssData": {"baseSeverity": "HIGH"}
                            }]
                        }
                    }
                }
            ]
        }
        
        cves = client._parse_cve_data(nvd_response)
        
        assert len(cves) == 1
        assert cves[0]["cve_id"] == "CVE-2024-12345"
        assert cves[0]["description"] == "Test vulnerability"
        assert cves[0]["severity"] == "high"
        assert cves[0]["published_date"] == "2024-01-15T10:00:00.000"
        assert "nvd.nist.gov" in cves[0]["source_url"]

