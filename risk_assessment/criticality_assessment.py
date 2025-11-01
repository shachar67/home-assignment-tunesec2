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
        
        prompt = f"""You are a business analyst assessing software criticality using CHAIN-OF-THOUGHT reasoning.

COMPANY: {company_name}
SOFTWARE: {software_name}

COMPANY CONTEXT:
{company_context}

SOFTWARE CONTEXT:
{software_context}

ANALYSIS PROCESS (think through each step):

STEP 1: COMPANY ANALYSIS
- What is {company_name}'s primary business?
- What are their core revenue streams?
- What industry/sector do they operate in?

STEP 2: SOFTWARE ANALYSIS  
- What does {software_name} do?
- What is its primary purpose/function?
- Who typically uses this software?

STEP 3: RELEVANCE ASSESSMENT
- How would {software_name} be used at {company_name}?
- Is it core to their business operations or supplementary?
- Would losing this software significantly impact revenue/operations?

STEP 4: CRITICALITY DETERMINATION
Apply these guidelines:
- HIGH: Critical to core business operations, revenue-generating, or security-critical
  Examples: IDE @ Software Company, Identity Management @ Bank, Payment Processor @ E-commerce
- MEDIUM: Important for productivity but not core to business model
  Examples: Analytics Tool @ Any Company, Project Management @ Tech Company
- LOW: Nice-to-have, minimal business impact if unavailable
  Examples: Wallpaper App @ Bank, Entertainment Tool @ Enterprise

EXAMPLES:
✓ Okta Workforce Identity @ Bank → HIGH (security-critical, regulatory requirement)
✓ IDE @ Software Company → HIGH (core productivity tool for primary business)
✓ Analytics Tool @ E-commerce → MEDIUM (helpful insights but not essential)
✓ Wallpaper App @ Bank → LOW (no business relevance)

Provide your complete chain-of-thought analysis and final assessment."""

        try:
            # Use structured output with Pydantic model
            structured_llm = self.llm.with_structured_output(CriticalityAnalysisOutput)
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
                reasoning=result.reasoning[:REASONING_MAX_LENGTH]  # Limit length
            )
            
            return assessment, elapsed, cost_info
            
        except Exception as e:
            logger.error("Error assessing criticality: %s", e)
            # Fallback to default
            return CriticalityAssessment(
                company_name=company_name,
                software_name=software_name,
                criticality=Criticality.MEDIUM,
                reasoning=f"Error assessing criticality: {str(e)}"
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

