#!/usr/bin/env python3
"""
Generate workflow graph visualization.
Creates a visual representation of the LangGraph workflow.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Set dummy keys if not present (just for visualization)
if not os.getenv("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = "dummy_key_for_viz"
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "dummy_key_for_viz"

def create_mermaid_diagram():
    """Create a Mermaid diagram of the workflow."""
    mermaid = """# Workflow Graph Visualization

```mermaid
graph TD
    Start([Start]) --> Input[Input: Company + Software]
    Input --> AssessVuln[Assess Vulnerabilities]
    
    AssessVuln --> Verify[Verify Software Exists]
    Verify --> NVD{Try NVD API}
    NVD -->|Success| CVSS[Extract CVSS Scores]
    NVD -->|Fail/Empty| TavilySearch[Tavily Web Search]
    TavilySearch --> GeminiVuln[Gemini Analysis<br/>with Confidence Scoring]
    
    CVSS --> Critique[Self-Critique Loop]
    GeminiVuln --> Critique
    Critique -->|Validate CVEs| FilterConf[Filter Low Confidence]
    FilterConf --> AssessCrit[Assess Business Criticality]
    
    AssessCrit --> TavilyCompany[Search Company Info]
    TavilyCompany --> TavilySoftware[Search Software Info]
    TavilySoftware --> GeminiCrit[Gemini Chain-of-Thought<br/>Criticality Analysis]
    
    GeminiCrit --> MakeDecision[Make Decision]
    MakeDecision --> Policy{Decision Policy}
    
    Policy -->|No Vulns| Approve1[✓ APPROVE]
    Policy -->|Med-High + Low Risk| Approve2[✓ APPROVE]
    Policy -->|Otherwise| Decline[✗ DECLINE]
    
    Approve1 --> Output[Generate Report + Save JSON]
    Approve2 --> Output
    Decline --> Output
    Output --> End([End])
    
    style AssessVuln fill:#e1f5ff
    style AssessCrit fill:#fff3e0
    style MakeDecision fill:#f3e5f5
    style Approve1 fill:#c8e6c9
    style Approve2 fill:#c8e6c9
    style Decline fill:#ffcdd2
    style NVD fill:#e3f2fd
    style Policy fill:#f3e5f5
    style Critique fill:#ffe0b2
    style CVSS fill:#e1f5ff
```

## Workflow Steps

1. **assess_vulnerabilities** - Check CVEs using NVD API (primary) or Tavily (fallback)
   - Extracts CVSS numeric scores for severity classification
   - Assigns confidence scores to each CVE match (high/medium/low)
   - Validates matches with self-critique loop to prevent false positives
   - Filters out low-confidence matches automatically

2. **assess_criticality** - Determine business importance using web search + LLM
   - Uses chain-of-thought reasoning for explainable assessments
   - Analyzes company business, software purpose, and operational impact
   
3. **make_decision** - Apply deterministic policy rules
   - Rule 1: No vulnerabilities → APPROVE
   - Rule 2: Med-High criticality + Low risk only → APPROVE  
   - Rule 3: Otherwise → DECLINE

## Tools Used

- **NVD API** - Authoritative CVE database with CVSS scores
- **Tavily** - AI-optimized web search
- **Gemini** - Google's LLM for analysis (temperature=0 for determinism)
- **LangGraph** - Workflow orchestration
"""
    
    os.makedirs("viz", exist_ok=True)
    with open("viz/workflow_diagram.md", "w", encoding="utf-8") as f:
        f.write(mermaid)
    
    print("✅ Mermaid diagram saved to viz/workflow_diagram.md")
    print("   View it at: https://mermaid.live/ or in any Markdown viewer")

def create_ascii_diagram():
    """Create a simple ASCII diagram."""
    ascii_art = """
┌─────────────────────────────────────────────────────────────────┐
│                  RISK ASSESSMENT WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

INPUT: Company Name + Software Name
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Assess Vulnerabilities                        │
│  ├─ Verify software exists                             │
│  ├─ Try NVD API → Extract CVSS numeric scores          │
│  └─ Fallback to Tavily web search                      │
│     ├─ Gemini analyzes with confidence scoring         │
│     ├─ Self-critique validation loop                   │
│     └─ Filter low-confidence CVEs                      │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Assess Business Criticality                   │
│  ├─ Search company information (Tavily)                │
│  ├─ Search software information (Tavily)               │
│  └─ Gemini chain-of-thought reasoning:                 │
│     ├─ Analyze company's core business                 │
│     ├─ Analyze software purpose                        │
│     ├─ Assess relevance to operations                  │
│     └─ Determine impact if unavailable                 │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Make Decision (Deterministic)                 │
│                                                         │
│  Rule 1: No vulnerabilities → APPROVE                  │
│  Rule 2: Med-High + Low risk only → APPROVE            │
│  Rule 3: Otherwise → DECLINE                           │
└─────────────────────────────────────────────────────────┘
   │
   ▼
OUTPUT: Decision + Summary + Traces + CVSS Scores (JSON)
"""
    
    os.makedirs("viz", exist_ok=True)
    with open("viz/workflow_ascii.txt", "w", encoding="utf-8") as f:
        f.write(ascii_art)
    
    print("✅ ASCII diagram saved to viz/workflow_ascii.txt")

def main():
    print("="*60)
    print("Generating Workflow Visualizations (Bonus #1)")
    print("="*60)
    print()
    
    # Create text-based visualizations
    create_mermaid_diagram()
    create_ascii_diagram()
    
    print()
    print("="*60)
    print("Visualizations Complete!")
    print("="*60)
    print()
    print("Files created:")
    print("  📊 viz/workflow_diagram.md (Mermaid - view at mermaid.live)")
    print("  📊 viz/workflow_ascii.txt (ASCII art)")
    print("  📊 viz/workflow.md (already exists - detailed description)")
    print()
    print("Note: PNG generation requires additional dependencies.")
    print("The Mermaid diagram can be converted to PNG at:")
    print("  https://mermaid.live/")
    print()

if __name__ == "__main__":
    main()

