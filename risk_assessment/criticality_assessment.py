"""
Business criticality assessment module.
"""

import time
import logging
from typing import List
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI

from .models import CriticalityAssessment, Criticality
from .structured_outputs import CriticalityAnalysisOutput
from .utils import calculate_cost

logger = logging.getLogger(__name__)

REASONING_MAX_LENGTH = 500
class CriticalityAssessor:
    """Assesses business criticality of software for a company."""
    
    def __init__(self, tavily_api_key: str, google_api_key: str):
        """Initialize the criticality assessor."""
        self.tavily_client = TavilyClient(api_key=tavily_api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=google_api_key,
            temperature=0.3
        )
    
    def search_company_info(self, company_name: str) -> dict:
        """Search for company information."""
        start_time = time.time()
        
        query = f"{company_name} company business industry products services"
        
        try:
            results = self.tavily_client.search(
                query=query,
                max_results=3,
                search_depth="basic"
            )
            
            elapsed = time.time() - start_time
            
            return {
                "results": results.get("results", []),
                "query": query,
                "elapsed_time": elapsed
            }
        except Exception as e:
            logger.error("Error searching company info: %s", e)
            return {
                "results": [],
                "query": query,
                "elapsed_time": time.time() - start_time,
                "error": str(e)
            }
    
    def search_software_info(self, software_name: str) -> dict:
        """Search for software information."""
        start_time = time.time()
        
        query = f"{software_name} software tool purpose use case features"
        
        try:
            results = self.tavily_client.search(
                query=query,
                max_results=3,
                search_depth="basic"
            )
            
            elapsed = time.time() - start_time
            
            return {
                "results": results.get("results", []),
                "query": query,
                "elapsed_time": elapsed
            }
        except Exception as e:
            logger.error("Error searching software info: %s", e)
            return {
                "results": [],
                "query": query,
                "elapsed_time": time.time() - start_time,
                "error": str(e)
            }
    
    def assess_criticality(self, company_name: str, software_name: str, 
                          company_info: List[dict], software_info: List[dict]) -> tuple:
        """Assess business criticality using LLM with structured outputs."""
        start_time = time.time()
        
        # Prepare context
        company_context = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\nContent: {r.get('content', '')}"
            for r in company_info
        ])
        
        software_context = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\nContent: {r.get('content', '')}"
            for r in software_info
        ])
        
        prompt = f"""You are a business analyst assessing software criticality.

COMPANY: {company_name}
SOFTWARE: {software_name}

COMPANY CONTEXT:
{company_context}

SOFTWARE CONTEXT:
{software_context}

Analyze the business criticality by thinking through these steps:

1. COMPANY BUSINESS: Describe {company_name}'s primary business in 1-2 sentences
2. SOFTWARE PURPOSE: Describe what {software_name} does in 1-2 sentences  
3. RELEVANCE: Explain how {software_name} relates to {company_name}'s business (1-2 sentences)
4. IMPACT IF UNAVAILABLE: Describe what would happen if {software_name} was unavailable (1-2 sentences)

Then determine CRITICALITY LEVEL using these guidelines:
- HIGH: Critical to core business operations, revenue-generating, or security-critical
  Examples: IDE @ Software Company, Identity Management @ Bank, Payment Processor @ E-commerce
- MEDIUM: Important for productivity but not core to business model
  Examples: Analytics Tool @ Any Company, Project Management @ Tech Company
- LOW: Nice-to-have, minimal business impact if unavailable
  Examples: Wallpaper App @ Bank, Entertainment Tool @ Enterprise

EXAMPLES:
- Okta Workforce Identity @ Citi Bank → HIGH (security-critical, regulatory requirement)
- IDE @ Software Company → HIGH (core productivity tool for primary business)
- Analytics Tool @ E-commerce → MEDIUM (helpful insights but not essential)

You must respond with a structured JSON object with these exact fields:
- company_business: string describing the company's primary business
- software_purpose: string describing what the software does
- relevance: string explaining how the software relates to the company's business
- impact_if_unavailable: string describing impact if software was unavailable
- criticality_level: one of "low", "medium", or "high"
- reasoning: 2-3 sentences explaining the criticality level
- confidence: one of "low", "medium", or "high"

Provide your analysis now."""

        try:
            # Use structured output with Pydantic model
            # Include schema explicitly to help the model
            structured_llm = self.llm.with_structured_output(
                CriticalityAnalysisOutput,
                include_raw=False
            )
            result = structured_llm.invoke(prompt)
            
            elapsed = time.time() - start_time
            
            # Extract token usage and calculate cost
            cost_info = {}
            if hasattr(result, 'response_metadata') and 'token_usage' in result.response_metadata:
                token_usage = result.response_metadata['token_usage']
                input_tokens = token_usage.get('prompt_tokens', 0)
                output_tokens = token_usage.get('completion_tokens', 0)
                cost_info = calculate_cost(input_tokens, output_tokens, "gemini-2.0-flash-exp")
            
            assessment = CriticalityAssessment(
                company_name=company_name,
                software_name=software_name,
                criticality=result.criticality_level,
                reasoning=result.reasoning[:REASONING_MAX_LENGTH],  # Limit length
                # Capture chain-of-thought fields
                company_business=result.company_business,
                software_purpose=result.software_purpose,
                relevance=result.relevance,
                impact_if_unavailable=result.impact_if_unavailable
            )
            
            return assessment, elapsed, cost_info
            
        except Exception as e:
            logger.error("Error assessing criticality: %s", e)
            # Fallback to default with more informative error message
            error_msg = str(e)
            if "validation error" in error_msg.lower():
                error_msg = "LLM returned malformed structured output. Using default MEDIUM criticality."
            
            return CriticalityAssessment(
                company_name=company_name,
                software_name=software_name,
                criticality=Criticality.MEDIUM,
                reasoning=error_msg[:REASONING_MAX_LENGTH]
            ), time.time() - start_time, {}
    
    def assess(self, company_name: str, software_name: str) -> tuple:
        """
        Perform complete criticality assessment.
        
        Returns:
            Tuple of (CriticalityAssessment, traces)
        """
        traces = []
        
        # Search company information
        company_search = self.search_company_info(company_name)
        traces.append({
            "step": "company_search",
            "tool": "tavily",
            "query": company_search.get("query"),
            "elapsed_time": company_search.get("elapsed_time"),
            "results_count": len(company_search.get("results", []))
        })
        
        # Search software information
        software_search = self.search_software_info(software_name)
        traces.append({
            "step": "software_search",
            "tool": "tavily",
            "query": software_search.get("query"),
            "elapsed_time": software_search.get("elapsed_time"),
            "results_count": len(software_search.get("results", []))
        })
        
        # Assess criticality
        assessment, elapsed, cost_info = self.assess_criticality(
            company_name,
            software_name,
            company_search.get("results", []),
            software_search.get("results", [])
        )
        
        trace_data = {
            "step": "criticality_analysis",
            "tool": "gemini",
            "elapsed_time": elapsed,
            "criticality": assessment.criticality.value
        }
        if cost_info:
            trace_data["cost"] = cost_info
        traces.append(trace_data)
        
        return assessment, traces

