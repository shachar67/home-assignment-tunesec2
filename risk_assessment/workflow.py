"""
LangGraph workflow for risk assessment.
"""

import os
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END

from .models import RiskAssessmentOutput
from .vulnerability_assessment import VulnerabilityAssessor
from .criticality_assessment import CriticalityAssessor
from .decision_policy import make_decision, generate_final_summary

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State for the LangGraph workflow."""
    company_name: str
    software_name: str
    vulnerability_assessment: dict
    criticality_assessment: dict
    decision: str
    decision_reasoning: str
    final_summary: str
    traces: list


class RiskAssessmentWorkflow:
    """LangGraph-based workflow for risk assessment."""
    
    def __init__(
        self, 
        tavily_api_key: str = None, 
        google_api_key: str = None,
        nvd_api_key: str = None,
        use_nvd: bool = True
    ):
        """Initialize the workflow."""
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.nvd_api_key = nvd_api_key or os.getenv("NVD_API_KEY")
        
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        
        self.vuln_assessor = VulnerabilityAssessor(
            tavily_api_key=self.tavily_api_key,
            google_api_key=self.google_api_key,
            nvd_api_key=self.nvd_api_key,
            use_nvd=use_nvd
        )
        self.crit_assessor = CriticalityAssessor(
            tavily_api_key=self.tavily_api_key,
            google_api_key=self.google_api_key
        )
        
        self.graph = self._build_graph()
    
    def _assess_vulnerabilities(self, state: WorkflowState) -> WorkflowState:
        """Node: Assess vulnerabilities."""
        logger.info("Assessing vulnerabilities for %s", state['software_name'])
        
        assessment, traces = self.vuln_assessor.assess(state["software_name"])
        
        state["vulnerability_assessment"] = assessment.model_dump()
        state["traces"].extend(traces)
        
        return state
    
    def _assess_criticality(self, state: WorkflowState) -> WorkflowState:
        """Node: Assess business criticality."""
        logger.info("Assessing business criticality for %s", state['company_name'])
        
        assessment, traces = self.crit_assessor.assess(
            state["company_name"],
            state["software_name"]
        )
        
        state["criticality_assessment"] = assessment.model_dump()
        state["traces"].extend(traces)
        
        return state
    
    def _make_decision(self, state: WorkflowState) -> WorkflowState:
        """Node: Make approve/decline decision."""
        logger.info("Making decision based on policy")
        
        from .models import VulnerabilityAssessment, CriticalityAssessment
        
        vuln_assessment = VulnerabilityAssessment(**state["vulnerability_assessment"])
        crit_assessment = CriticalityAssessment(**state["criticality_assessment"])
        
        decision, reasoning = make_decision(vuln_assessment, crit_assessment)
        
        state["decision"] = decision.value
        state["decision_reasoning"] = reasoning
        
        # Generate final summary
        final_summary = generate_final_summary(
            decision,
            reasoning,
            vuln_assessment,
            crit_assessment
        )
        state["final_summary"] = final_summary
        
        return state
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("assess_vulnerabilities", self._assess_vulnerabilities)
        workflow.add_node("assess_criticality", self._assess_criticality)
        workflow.add_node("make_decision", self._make_decision)
        
        # Define edges
        workflow.set_entry_point("assess_vulnerabilities")
        workflow.add_edge("assess_vulnerabilities", "assess_criticality")
        workflow.add_edge("assess_criticality", "make_decision")
        workflow.add_edge("make_decision", END)
        
        return workflow.compile()
    
    def run(self, company_name: str, software_name: str) -> RiskAssessmentOutput:
        """
        Run the risk assessment workflow.
        
        Args:
            company_name: Name of the company
            software_name: Name of the software
            
        Returns:
            RiskAssessmentOutput with the final decision and summary
        """
        logger.info("="*80)
        logger.info("Starting Risk Assessment")
        logger.info("Company: %s", company_name)
        logger.info("Software: %s", software_name)
        logger.info("="*80)
        
        # Initialize state
        initial_state = {
            "company_name": company_name,
            "software_name": software_name,
            "vulnerability_assessment": {},
            "criticality_assessment": {},
            "decision": "",
            "decision_reasoning": "",
            "final_summary": "",
            "traces": []
        }
        
        # Run the workflow
        final_state = self.graph.invoke(initial_state)
        
        # Convert to output model
        from .models import Decision, VulnerabilityAssessment, CriticalityAssessment
        
        vuln_assessment = VulnerabilityAssessment(**final_state["vulnerability_assessment"])
        crit_assessment = CriticalityAssessment(**final_state["criticality_assessment"])
        
        output = RiskAssessmentOutput(
            company_name=company_name,
            software_name=software_name,
            decision=Decision(final_state["decision"]),
            vulnerability_summary=vuln_assessment.summary,
            criticality_level=crit_assessment.criticality,
            criticality_reasoning=crit_assessment.reasoning,
            final_summary=final_state["final_summary"],
            traces=final_state["traces"],
            vulnerabilities=vuln_assessment.vulnerabilities,
            source_urls=vuln_assessment.source_data,
            software_exists=vuln_assessment.software_exists,
            existence_confidence=vuln_assessment.existence_confidence,
            # Pass through chain-of-thought fields
            company_business=crit_assessment.company_business,
            software_purpose=crit_assessment.software_purpose,
            relevance=crit_assessment.relevance,
            impact_if_unavailable=crit_assessment.impact_if_unavailable
        )
        
        logger.info("="*80)
        logger.info("Risk Assessment Complete")
        logger.info("Decision: %s", output.decision.value.upper())
        logger.info("="*80)
        
        return output
    
    def visualize(self, output_path: str = "viz/graph.png"):
        """
        Visualize the workflow graph.
        
        Args:
            output_path: Path to save the visualization
        """
        try:
            from IPython.display import Image
            img = Image(self.graph.get_graph().draw_mermaid_png())
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to file
            with open(output_path, "wb") as f:
                f.write(img.data)
            
            logger.info("Graph visualization saved to %s", output_path)
            return img
        except Exception as e:
            logger.warning("Could not generate graph visualization: %s", e)
            logger.info("Graph visualization is optional and doesn't affect functionality")
            return None

