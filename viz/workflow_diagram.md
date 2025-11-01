# Workflow Graph Visualization

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
