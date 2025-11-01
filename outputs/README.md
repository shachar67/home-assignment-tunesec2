# Sample Outputs

This directory contains sample outputs from the risk assessment workflow.

## Running Examples

To generate real assessment outputs, you need to:

1. Set up your API keys in `.env`:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

2. Run individual assessments:
   ```bash
   python run.py --software "Tiles" --company "Shopify"
   ```

3. Or run all examples:
   ```bash
   python run.py batch examples.json
   ```

## Example Files

The example files demonstrate the output structure:

- `example_approve.json` - Example of an approved software (no vulnerabilities)
- `example_decline.json` - Example of a declined software (critical vulnerabilities)

## Output Structure

Each JSON file contains:

- **timestamp**: When the assessment was run
- **company_name**: Company being assessed
- **software_name**: Software being evaluated
- **decision**: "approve" or "decline"
- **vulnerability_summary**: Summary of security findings
- **criticality_level**: "low", "medium", or "high"
- **criticality_reasoning**: Why the software is critical/not critical
- **final_summary**: Markdown-formatted comprehensive report
- **traces**: Execution metadata including:
  - Tool calls (Tavily searches, Gemini analysis)
  - Elapsed times
  - Result counts

## Provided Examples

The `examples.json` file contains 5 test cases:

1. **Okta Workforce Identity** @ Citi Bank - Identity management for banking
2. **Langflow** @ NVIDIA - AI development tool for tech company
3. **Tiles** @ Shopify - Productivity tool for e-commerce
4. **Base44** @ Payoneer - Payment infrastructure tool
5. **Goshgoha** @ Wiz - Security tool for cybersecurity company

Run these to see how the system handles different combinations of software types and company needs.

