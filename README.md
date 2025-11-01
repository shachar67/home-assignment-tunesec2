# Risk Assessment Workflow

An agentic workflow system that assesses the risk of adopting software for a specific company using deterministic decision rules and AI-powered analysis.

## Overview

This system combines:
1. **CVE & Vulnerability Search** - Direct NVD API integration with Tavily fallback
2. **Business Criticality Assessment** - LLM-powered analysis with structured outputs
3. **Deterministic Decision Policy** - Clear, testable approval rules

## Decision Policy

The system follows three deterministic rules:
1. **No vulnerabilities found** → APPROVE
2. **Medium-high business importance AND only low-risk vulnerabilities** → APPROVE
3. **Otherwise** → DECLINE

## Prerequisites

- Python 3.10 or higher
- Tavily API key (free tier: https://tavily.com)
- Google Gemini API key (free tier: https://aistudio.google.com/app/apikey)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd risk-assessment-workflow

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp env.example .env
# Edit .env and add your API keys:
# GOOGLE_API_KEY=your_gemini_api_key
# TAVILY_API_KEY=your_tavily_api_key
```

## Usage

### Single Assessment

```bash
python run.py --software "Tiles" --company "Shopify"
```

Options:
- `--software, -s`: Software name (required)
- `--company, -c`: Company name (required)
- `--output, -o`: Output directory (default: outputs)
- `--no-save`: Don't save output to file
- `--visualize, -v`: Generate workflow graph

### Batch Assessment

```bash
python run.py batch examples.json
```

Example input file format:
```json
[
  {"company": "Citi Bank", "software": "Okta Workforce Identity"},
  {"company": "NVIDIA", "software": "Langflow"}
]
```

### Examples

```bash
# Run all provided examples
python run.py batch examples.json

# Individual examples
python run.py --software "Okta Workforce Identity" --company "Citi Bank"
python run.py --software "Langflow" --company "NVIDIA"
python run.py --software "Tiles" --company "Shopify"
python run.py --software "Base44" --company "Payoneer"
python run.py --software "Goshgoha" --company "Wiz"
```

## Output

Each assessment generates a JSON file in `outputs/` containing:
- Decision (APPROVE/DECLINE)
- Vulnerability summary with CVE IDs and severity
- Business criticality assessment (LOW/MEDIUM/HIGH)
- Source URLs for verification
- Execution traces with timestamps and costs
- Final markdown report

Example:
```json
{
  "decision": "approve",
  "vulnerability_summary": "Found 2 low-severity vulnerabilities...",
  "criticality_level": "high",
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-1234",
      "severity": "low",
      "description": "...",
      "source_url": "https://nvd.nist.gov/..."
    }
  ],
  "traces": [...]
}
```

## Architecture

### Workflow Graph

```
┌─────────────────────────┐
│  assess_vulnerabilities │
│  (NVD API + Gemini)     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  assess_criticality     │
│  (Tavily + Gemini)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  make_decision          │
│  (Deterministic Policy) │
└─────────────────────────┘
```

### Project Structure

```
risk_assessment/
├── models.py                    # Pydantic data models
├── vulnerability_assessment.py  # CVE search & analysis
├── criticality_assessment.py    # Business criticality evaluation
├── decision_policy.py           # Deterministic decision rules
├── workflow.py                  # LangGraph workflow orchestration
├── cve_client.py               # NVD API client
├── utils.py                    # Logging & cost tracking
└── main.py                     # CLI interface

tests/                          # Unit tests (pytest)
outputs/                        # Assessment results
viz/                           # Workflow diagrams and traces
```

## Key Features

- **Software Validation**: Verifies software exists before assessment
- **CVE Analysis**: Uses CVSS numeric scores for accurate severity classification
- **Confidence Scoring**: Validates CVEs belong to target software with confidence levels
- **CVE Deduplication**: Removes duplicate CVEs from multiple sources
- **Chain-of-Thought**: Explicit reasoning steps for criticality assessment
- **Source Tracking**: Every vulnerability includes verification URL
- **Deterministic LLM**: Temperature=0 for consistent results
- **Structured Outputs**: Type-safe Pydantic models with validation
- **Cost Tracking**: Token usage and estimated API costs
- **Comprehensive Testing**: >80% code coverage
- **Batch Processing**: Run multiple assessments efficiently

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=risk_assessment --cov-report=html

# Run specific test files
pytest tests/test_decision_policy.py
```

## Configuration

The system uses environment variables for configuration. Set these in a `.env` file:

```bash
# Required API Keys
TAVILY_API_KEY=your_tavily_key
GOOGLE_API_KEY=your_gemini_key

# Optional (for higher NVD rate limits)
NVD_API_KEY=your_nvd_key
```

Default settings (hardcoded for simplicity):
- **LLM Model**: gemini-2.0-flash-exp
- **Temperature**: 0 for vulnerability assessment, 0.3 for criticality
- **CVE Lookback**: 730 days (2 years)
- **NVD API**: Enabled by default with Tavily fallback

For advanced customization, modify the assessor initialization in `workflow.py`.

## Design Choices

1. **LangGraph**: Provides clear workflow structure and easy debugging
2. **NVD API Primary**: Authoritative CVE source with Tavily fallback
3. **Pydantic Models**: Type safety and automatic validation
4. **Temperature=0**: Deterministic, reproducible LLM outputs
5. **CVSS Numeric Scores**: Uses standardized CVSS ratings (9.0+ = Critical, 7.0+ = High, 4.0+ = Medium)
6. **Confidence Filtering**: Only accepts CVE matches with high or medium confidence
7. **Dual Validation**: Second LLM pass validates CVE attributions to prevent false positives
8. **Structured Reasoning**: Chain-of-thought approach for explainable criticality assessments

## Limitations

1. **API Rate Limits**: NVD (5 req/30sec), Tavily (1000/month free tier)
2. **Web Search Dependency**: Results quality depends on search engine
3. **Software Name Ambiguity**: Similar names may cause confusion despite confidence scoring
4. **English Only**: Best results with English software/company names
5. **Recent CVEs**: Very new vulnerabilities may not appear immediately

## Extending the System

### Add New Assessment Step

```python
def _new_assessment_step(self, state: WorkflowState) -> WorkflowState:
    # Custom logic
    return state

workflow.add_node("new_step", self._new_assessment_step)
workflow.add_edge("assess_criticality", "new_step")
```

### Custom Decision Policy

Modify `decision_policy.py`:

```python
def make_decision(vuln, crit):
    # Custom rules
    if custom_condition:
        return Decision.APPROVE, "reason"
    return Decision.DECLINE, "reason"
```
### Extensibility Features

The codebase includes additional modules designed for future enhancements:

#### RAG-based CVE Knowledge Base (`rag_cve.py`)
- **Purpose**: Semantic search over historical CVE data using vector embeddings
- **Status**: Implemented but not enabled (requires ChromaDB setup)
- **Use case**: When assessing software with large CVE histories
- **Enable**: Import and initialize `CVEKnowledgeBase` in `workflow.py`

#### Multi-Agent Consensus (`multi_agent.py`)
- **Purpose**: Cross-validate criticality assessments using multiple LLMs
- **Status**: Implemented but not enabled (requires additional API keys)
- **Use case**: High-stakes decisions requiring multiple perspectives
- **Enable**: Import and initialize `MultiAgentConsensus` in `workflow.py`

These features demonstrate extensibility but remain disabled to:
1. Keep the core solution simple and maintainable
2. Avoid additional API costs
3. Meet free-tier requirements of the assignment

## Development Approach

This solution was developed using AI-assisted tools (Cursor) as encouraged by the assignment guidelines. The workflow was:

1. **Architecture Design** - Manual planning of workflow, data models, and interfaces
2. **Implementation** - AI-assisted coding with human review and refactoring
3. **Testing** - Manual test case design with AI-assisted test implementation
4. **Refinement** - Human-driven debugging and optimization

Key decisions made during development:
- Chose LangGraph for clear workflow visualization and debugging
- Implemented NVD API with Tavily fallback for reliability
- Used structured LLM outputs (Pydantic) to prevent hallucinations
- Added software verification to prevent false positives from name similarity

## Helper Scripts

Additional scripts in `scripts/` directory:
- `generate_viz.py` - Generate workflow diagram
- `visualize_traces.py` - Generate execution trace reports (used for Bonus #2)