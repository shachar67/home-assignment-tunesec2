"""
CLI interface for the risk assessment workflow.
"""

import os
import json
from pathlib import Path
from datetime import datetime
import typer
from dotenv import load_dotenv

from .workflow import RiskAssessmentWorkflow
from .models import RiskAssessmentOutput
from .utils import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()

app = typer.Typer(
    name="risk-assess",
    help="Agentic Risk Assessment Workflow - Assess software adoption risk",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True
)


@app.callback()
def main(
    ctx: typer.Context,
    software: str = typer.Option(None, "--software", "-s", help="Name of the software to assess"),
    company: str = typer.Option(None, "--company", "-c", help="Name of the company"),
    output_dir: str = typer.Option("outputs", "--output", "-o", help="Directory to save output files"),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save output to file"),
    visualize: bool = typer.Option(False, "--visualize", "-v", help="Generate workflow graph visualization"),
):
    """
    Agentic Risk Assessment Workflow - Assess software adoption risk.
    
    Examples:
        python run.py --software "Tiles" --company "Shopify"
        python run.py assess --software "Tiles" --company "Shopify"
        python run.py batch examples.json
    """
    # If a subcommand is invoked, don't run the default behavior
    if ctx.invoked_subcommand is not None:
        return
    
    # If no software/company provided, show help
    if not software or not company:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    
    # Run assessment with provided options
    run_assessment(software, company, output_dir, no_save, visualize)


def run_assessment(
    software: str,
    company: str, 
    output_dir: str = "outputs",
    no_save: bool = False,
    visualize: bool = False
):
    """Core assessment logic."""
    # Check for API keys
    tavily_key = os.getenv("TAVILY_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if not tavily_key or not google_key:
        typer.echo("❌ Error: API keys not found!", err=True)
        typer.echo("\nPlease set the following environment variables:")
        if not tavily_key:
            typer.echo("  - TAVILY_API_KEY (get it from https://tavily.com/)")
        if not google_key:
            typer.echo("  - GOOGLE_API_KEY (get it from https://aistudio.google.com/app/apikey)")
        typer.echo("\nYou can set them in a .env file or as environment variables.")
        raise typer.Exit(code=1)
    
    try:
        # Initialize workflow
        workflow = RiskAssessmentWorkflow(
            tavily_api_key=tavily_key,
            google_api_key=google_key
        )
        
        # Visualize graph if requested
        if visualize:
            workflow.visualize()
        
        # Run assessment
        output = workflow.run(company_name=company, software_name=software)
        
        # Print summary
        print("\n" + "="*80)
        print(output.final_summary)
        print("="*80)
        
        # Save output
        if not no_save:
            save_output(output, output_dir)
        
        # Exit with appropriate code
        exit_code = 0 if output.decision.value == "approve" else 1
        raise typer.Exit(code=exit_code)
        
    except Exception as e:
        typer.echo(f"\n❌ Error: {str(e)}", err=True)
        raise typer.Exit(code=2)


def save_output(output: RiskAssessmentOutput, output_dir: str = "outputs"):
    """Save the assessment output to a JSON file."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company = output.company_name.replace(" ", "_").replace("/", "_")
    safe_software = output.software_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_software}_{safe_company}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Prepare output data
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "company_name": output.company_name,
        "software_name": output.software_name,
        "decision": output.decision.value,
        "vulnerability_summary": output.vulnerability_summary,
        "criticality_level": output.criticality_level.value,
        "criticality_reasoning": output.criticality_reasoning,
        "chain_of_thought": {
            "company_business": output.company_business,
            "software_purpose": output.software_purpose,
            "relevance": output.relevance,
            "impact_if_unavailable": output.impact_if_unavailable
        },
        "final_summary": output.final_summary,
        "vulnerabilities": [
            {
                "cve_id": v.cve_id,
                "severity": v.severity.value,
                "cvss_score": v.cvss_score,
                "description": v.description,
                "source_url": v.source_url
            }
            for v in output.vulnerabilities
        ],
        "source_urls": output.source_urls,
        "software_verification": {
            "exists": output.software_exists,
            "confidence": output.existence_confidence
        },
        "traces": output.traces
    }
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    typer.echo(f"\n💾 Output saved to: {filepath}")
    return filepath


@app.command(name="assess")
def assess_command(
    software: str = typer.Option(..., "--software", "-s", help="Name of the software to assess"),
    company: str = typer.Option(..., "--company", "-c", help="Name of the company"),
    output_dir: str = typer.Option("outputs", "--output", "-o", help="Directory to save output files"),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save output to file"),
    visualize: bool = typer.Option(False, "--visualize", "-v", help="Generate workflow graph visualization"),
):
    """
    Assess the risk of adopting software for a company.
    
    Example:
        python run.py assess --software "Tiles" --company "Shopify"
    """
    run_assessment(software, company, output_dir, no_save, visualize)


@app.command()
def batch(
    input_file: str = typer.Argument(..., help="Path to JSON file with assessment requests"),
    output_dir: str = typer.Option("outputs", "--output", "-o", help="Directory to save output files"),
):
    """
    Run batch assessments from a JSON input file.
    
    Input file format:
    [
        {"company": "Company Name", "software": "Software Name"},
        ...
    ]
    """
    # Check for API keys
    tavily_key = os.getenv("TAVILY_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if not tavily_key or not google_key:
        typer.echo("❌ Error: API keys not found!", err=True)
        raise typer.Exit(code=1)
    
    try:
        # Load input file
        with open(input_file, "r", encoding="utf-8") as f:
            requests = json.load(f)
        
        # Initialize workflow
        workflow = RiskAssessmentWorkflow(
            tavily_api_key=tavily_key,
            google_api_key=google_key
        )
        
        # Process each request
        results = []
        for i, req in enumerate(requests, 1):
            typer.echo(f"\n{'='*80}")
            typer.echo(f"Processing {i}/{len(requests)}")
            typer.echo(f"{'='*80}")
            
            output = workflow.run(
                company_name=req["company"],
                software_name=req["software"]
            )
            
            filepath = save_output(output, output_dir)
            results.append({
                "company": req["company"],
                "software": req["software"],
                "decision": output.decision.value,
                "output_file": filepath
            })
        
        # Print summary
        typer.echo(f"\n{'='*80}")
        typer.echo(f"✅ Batch processing complete: {len(results)} assessments")
        typer.echo(f"{'='*80}\n")
        
        for result in results:
            status = "✓" if result["decision"] == "approve" else "✗"
            typer.echo(f"{status} {result['software']} @ {result['company']}: {result['decision'].upper()}")
        
    except Exception as e:
        typer.echo(f"\n❌ Error: {str(e)}", err=True)
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()

