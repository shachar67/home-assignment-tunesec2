"""
Direct CVE database client for querying NVD API.
"""

import time
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CVEDatabaseClient:
    """Direct integration with National Vulnerability Database (NVD) API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CVE database client.
        
        Args:
            api_key: Optional NVD API key for higher rate limits
        """
        self.nvd_base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"apiKey": api_key})
    
    def search_cves(
        self, 
        software_name: str, 
        days_back: int = 730,  # 2 years default
        max_results: int = 100
    ) -> Dict:
        """
        Search NVD database for CVEs related to software.
        
        Args:
            software_name: Name of the software to search
            days_back: Number of days to look back
            max_results: Maximum number of results
            
        Returns:
            Dict containing CVE data and metadata
        """
        start_time = time.time()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Build params with proper ISO 8601 date format for NVD API v2.0
        params = {
            "keywordSearch": software_name,
            "resultsPerPage": min(max_results, 2000)  # API limit
        }
        
        # Add date filters in ISO 8601 format (required by NVD API v2.0)
        # Format: YYYY-MM-DDTHH:MM:SS.000 (with .000 for milliseconds)
        params["pubStartDate"] = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        params["pubEndDate"] = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        try:
            response = self.session.get(
                self.nvd_base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            elapsed = time.time() - start_time
            
            return {
                "cves": self._parse_cve_data(data),
                "total_results": data.get("totalResults", 0),
                "query": software_name,
                "elapsed_time": elapsed,
                "source": "nvd_api"
            }
            
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error("Error fetching CVEs from NVD: %s", e)
            return {
                "cves": [],
                "total_results": 0,
                "query": software_name,
                "elapsed_time": elapsed,
                "source": "nvd_api",
                "error": str(e)
            }
    
    def _parse_cve_data(self, nvd_response: Dict) -> List[Dict]:
        """
        Parse NVD API response into structured CVE data.
        
        Args:
            nvd_response: Raw response from NVD API
            
        Returns:
            List of parsed CVE dictionaries
        """
        cves = []
        
        vulnerabilities = nvd_response.get("vulnerabilities", [])
        
        for item in vulnerabilities:
            cve = item.get("cve", {})
            cve_id = cve.get("id", "Unknown")
            
            # Extract description
            descriptions = cve.get("descriptions", [])
            description = next(
                (d.get("value", "") for d in descriptions if d.get("lang") == "en"),
                "No description available"
            )
            
            # Extract severity metrics
            metrics = cve.get("metrics", {})
            severity, cvss_score = self._extract_severity(metrics)
            
            # Extract published date
            published = cve.get("published", "")
            
            cves.append({
                "cve_id": cve_id,
                "description": description,
                "severity": severity,
                "cvss_score": cvss_score,
                "published_date": published,
                "source_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            })
        
        return cves
    
    def _extract_severity(self, metrics: Dict) -> tuple:
        """
        Extract severity rating and CVSS score from CVE metrics.
        
        Priority: CVSS v3.1 > CVSS v3.0 > CVSS v2.0
        
        Returns:
            Tuple of (severity_string, cvss_score)
        """
        # Try CVSS v3.1
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            cvss_data = cvss_v31[0].get("cvssData", {})
            return (
                cvss_data.get("baseSeverity", "unknown").lower(),
                cvss_data.get("baseScore", None)
            )
        
        # Try CVSS v3.0
        cvss_v30 = metrics.get("cvssMetricV30", [])
        if cvss_v30:
            cvss_data = cvss_v30[0].get("cvssData", {})
            return (
                cvss_data.get("baseSeverity", "unknown").lower(),
                cvss_data.get("baseScore", None)
            )
        
        # Try CVSS v2.0
        cvss_v2 = metrics.get("cvssMetricV2", [])
        if cvss_v2:
            base_score = cvss_v2[0].get("cvssData", {}).get("baseScore", 0.0)
            return (self._v2_score_to_severity(base_score), base_score)
        
        return ("unknown", None)
    
    def _v2_score_to_severity(self, score: float) -> str:
        """Convert CVSS v2 score to severity label."""
        if score >= 7.0:
            return "high"
        elif score >= 4.0:
            return "medium"
        elif score > 0:
            return "low"
        return "unknown"

