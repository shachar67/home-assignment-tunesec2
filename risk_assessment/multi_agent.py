"""
Multi-agent consensus for more reliable assessments.
Uses multiple LLMs and combines their judgments.
"""

import asyncio
from typing import List, Optional, Dict
from langchain_google_genai import ChatGoogleGenerativeAI

from .models import CriticalityAssessment, Criticality
from .structured_outputs import CriticalityAnalysisOutput

REASONING_MAX_LENGTH = 500
class MultiAgentConsensus:
    """
    Multi-agent consensus system for criticality assessment.
    
    Uses multiple LLMs to get independent assessments and combines
    them through majority voting or confidence weighting.
    """
    
    def __init__(
        self,
        google_api_key: str,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        use_claude: bool = False,
        use_openai: bool = False
    ):
        """
        Initialize multi-agent system.
        
        Args:
            google_api_key: Google Gemini API key (required)
            claude_api_key: Anthropic Claude API key (optional)
            openai_api_key: OpenAI API key (optional)
            use_claude: Whether to include Claude in consensus
            use_openai: Whether to include OpenAI in consensus
        """
        self.models = []
        
        # Always include Gemini
        self.models.append({
            "name": "gemini",
            "model": ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=google_api_key,
                temperature=0.1
            )
        })
        
        # Optionally add Claude
        if use_claude and claude_api_key:
            try:
                from langchain_anthropic import ChatAnthropic
                self.models.append({
                    "name": "claude",
                    "model": ChatAnthropic(
                        model="claude-3-5-sonnet-20241022",
                        api_key=claude_api_key,
                        temperature=0.1
                    )
                })
            except ImportError:
                print("⚠️  langchain-anthropic not installed. Skipping Claude.")
        
        # Optionally add OpenAI
        if use_openai and openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                self.models.append({
                    "name": "openai",
                    "model": ChatOpenAI(
                        model="gpt-4o",
                        api_key=openai_api_key,
                        temperature=0.1
                    )
                })
            except ImportError:
                print("⚠️  langchain-openai not installed. Skipping OpenAI.")
        
        print(f"✅ Multi-agent consensus enabled with {len(self.models)} model(s): {[m['name'] for m in self.models]}")
    
    async def assess_criticality_async(
        self,
        company_name: str,
        software_name: str,
        prompt: str
    ) -> List[Dict]:
        """
        Get criticality assessments from all models in parallel.
        
        Args:
            company_name: Name of the company
            software_name: Name of the software
            prompt: Assessment prompt
            
        Returns:
            List of assessments from each model
        """
        async def get_assessment(model_info: Dict) -> Dict:
            """Get assessment from a single model."""
            try:
                structured_llm = model_info["model"].with_structured_output(
                    CriticalityAnalysisOutput
                )
                result = await structured_llm.ainvoke(prompt)
                
                return {
                    "model": model_info["name"],
                    "criticality": result.criticality_level,
                    "reasoning": result.reasoning,
                    "success": True
                }
            except Exception as e:
                print(f"Error from {model_info['name']}: {e}")
                return {
                    "model": model_info["name"],
                    "criticality": Criticality.MEDIUM,
                    "reasoning": f"Error: {str(e)}",
                    "success": False
                }
        
        # Run all assessments in parallel
        tasks = [get_assessment(model_info) for model_info in self.models]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def calculate_consensus(
        self,
        assessments: List[Dict],
        company_name: str,
        software_name: str
    ) -> CriticalityAssessment:
        """
        Calculate consensus from multiple assessments.
        
        Uses majority voting. In case of tie, uses most conservative (highest) criticality.
        
        Args:
            assessments: List of assessments from different models
            company_name: Name of the company
            software_name: Name of the software
            
        Returns:
            Consensus criticality assessment
        """
        # Filter successful assessments
        valid_assessments = [a for a in assessments if a["success"]]
        
        if not valid_assessments:
            # All failed, return default
            return CriticalityAssessment(
                company_name=company_name,
                software_name=software_name,
                criticality=Criticality.MEDIUM,
                reasoning="All models failed to provide assessment"
            )
        
        # Count votes for each criticality level
        votes = {
            Criticality.LOW: 0,
            Criticality.MEDIUM: 0,
            Criticality.HIGH: 0
        }
        
        for assessment in valid_assessments:
            votes[assessment["criticality"]] += 1
        
        # Find winning criticality (most votes)
        winner = max(votes.items(), key=lambda x: x[1])
        consensus_criticality = winner[0]
        
        # Combine reasoning from all models
        reasoning_parts = []
        for assessment in valid_assessments:
            reasoning_parts.append(
                f"[{assessment['model'].upper()}]: {assessment['reasoning']}"
            )
        
        combined_reasoning = " | ".join(reasoning_parts)
        
        # Add consensus info
        vote_summary = f"Consensus: {winner[1]}/{len(valid_assessments)} models agreed. "
        final_reasoning = vote_summary + combined_reasoning
        
        return CriticalityAssessment(
            company_name=company_name,
            software_name=software_name,
            criticality=consensus_criticality,
            reasoning=final_reasoning[:REASONING_MAX_LENGTH]  # Limit length
        )
    
    async def assess_with_consensus(
        self,
        company_name: str,
        software_name: str,
        prompt: str
    ) -> CriticalityAssessment:
        """
        Perform full consensus assessment.
        
        Args:
            company_name: Name of the company
            software_name: Name of the software
            prompt: Assessment prompt
            
        Returns:
            Consensus assessment
        """
        # Get assessments from all models
        assessments = await self.assess_criticality_async(
            company_name,
            software_name,
            prompt
        )
        
        # Calculate consensus
        consensus = self.calculate_consensus(
            assessments,
            company_name,
            software_name
        )
        
        return consensus

