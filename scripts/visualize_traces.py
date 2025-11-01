#!/usr/bin/env python3
"""
Visualize execution traces from assessment runs.

Generates markdown reports with:
- Execution timeline (Mermaid gantt charts)
- Step-by-step trace details
- Cost and timing analysis
- Results summary
"""

import json
import os
from pathlib import Path


def load_assessment_results(output_dir="outputs"):
    """Load all assessment results from output directory."""
    results = []
    output_path = Path(output_dir)
    
    for json_file in output_path.glob("*.json"):
        # Skip example files
        if "example_" in json_file.name:
            continue
        
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["filename"] = json_file.name
                results.append(data)
        except Exception as e:
            print(f"⚠️  Could not load {json_file}: {e}")
    
    return results


def visualize_trace(assessment):
    """Create a visual representation of execution trace."""
    company = assessment.get("company_name", "Unknown")
    software = assessment.get("software_name", "Unknown")
    decision = assessment.get("decision", "unknown").upper()
    timestamp = assessment.get("timestamp", "")
    traces = assessment.get("traces", [])
    
    # Decision emoji
    decision_emoji = "✅" if decision == "APPROVE" else "❌"
    
    print("\n" + "="*80)
    print(f"{decision_emoji} {software} @ {company} - {decision}")
    print("="*80)
    print(f"📅 Timestamp: {timestamp}")
    print(f"📊 Total Steps: {len(traces)}")
    
    # Calculate total time
    total_time = sum(trace.get("elapsed_time", 0) for trace in traces)
    print(f"⏱️  Total Time: {total_time:.2f}s")
    
    print("\n" + "─"*80)
    print("Execution Trace:")
    print("─"*80)
    
    # Show each trace step
    for i, trace in enumerate(traces, 1):
        step_name = trace.get("step", "unknown")
        tool = trace.get("tool", "unknown")
        elapsed = trace.get("elapsed_time", 0)
        
        # Step-specific details
        details = []
        if "query" in trace:
            details.append(f"Query: {trace['query']}")
        if "results_count" in trace:
            details.append(f"Results: {trace['results_count']}")
        if "vulnerabilities_found" in trace:
            details.append(f"Vulns: {trace['vulnerabilities_found']}")
        if "criticality" in trace:
            details.append(f"Level: {trace['criticality']}")
        if "source" in trace:
            details.append(f"Source: {trace['source']}")
        if "data_source" in trace:
            details.append(f"Data: {trace['data_source']}")
        
        # Progress bar
        bar_length = int((elapsed / total_time) * 30) if total_time > 0 else 0
        bar = "█" * bar_length + "░" * (30 - bar_length)
        
        print(f"\n{i}. {step_name}")
        print(f"   🔧 Tool: {tool}")
        print(f"   ⏱️  Time: {elapsed:.2f}s [{bar}] {(elapsed/total_time*100):.1f}%")
        if details:
            print(f"   📋 {' | '.join(details)}")
    
    # Show results
    print("\n" + "─"*80)
    print("Results:")
    print("─"*80)
    print(f"Decision: {decision}")
    print(f"Criticality: {assessment.get('criticality_level', 'unknown').upper()}")
    print(f"Vulnerabilities: {assessment.get('vulnerability_summary', 'N/A')[:100]}...")
    
    print("\n")


def create_summary_table(assessments):
    """Create a summary table of all assessments."""
    print("\n" + "="*80)
    print("ASSESSMENT SUMMARY TABLE")
    print("="*80)
    print()
    
    # Header
    print(f"{'Software':<25} {'Company':<20} {'Decision':<10} {'Time (s)':<10} {'Steps':<8}")
    print("─"*80)
    
    # Rows
    for assessment in assessments:
        software = assessment.get("software_name", "?")[:24]
        company = assessment.get("company_name", "?")[:19]
        decision = assessment.get("decision", "?").upper()[:9]
        traces = assessment.get("traces", [])
        total_time = sum(t.get("elapsed_time", 0) for t in traces)
        num_steps = len(traces)
        
        decision_mark = "✅" if decision == "APPROVE" else "❌"
        
        print(f"{software:<25} {company:<20} {decision_mark} {decision:<8} {total_time:<10.2f} {num_steps:<8}")
    
    print()


def create_performance_report(assessments):
    """Create a performance analysis report."""
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS")
    print("="*80)
    print()
    
    # Collect stats
    all_traces = []
    for assessment in assessments:
        all_traces.extend(assessment.get("traces", []))
    
    if not all_traces:
        print("No traces found.")
        return
    
    # Stats by tool
    tool_times = {}
    tool_counts = {}
    
    for trace in all_traces:
        tool = trace.get("tool", "unknown")
        elapsed = trace.get("elapsed_time", 0)
        
        if tool not in tool_times:
            tool_times[tool] = []
            tool_counts[tool] = 0
        
        tool_times[tool].append(elapsed)
        tool_counts[tool] += 1
    
    # Display stats
    print("Tool Usage Statistics:")
    print("─"*80)
    print(f"{'Tool':<20} {'Calls':<10} {'Avg Time (s)':<15} {'Total Time (s)':<15}")
    print("─"*80)
    
    for tool in sorted(tool_times.keys()):
        times = tool_times[tool]
        count = tool_counts[tool]
        avg_time = sum(times) / len(times)
        total_time = sum(times)
        
        print(f"{tool:<20} {count:<10} {avg_time:<15.2f} {total_time:<15.2f}")
    
    print()
    
    # Decision stats
    approvals = sum(1 for a in assessments if a.get("decision") == "approve")
    declines = sum(1 for a in assessments if a.get("decision") == "decline")
    
    print("Decision Statistics:")
    print("─"*80)
    print(f"Total Assessments: {len(assessments)}")
    print(f"✅ Approved: {approvals} ({approvals/len(assessments)*100:.1f}%)")
    print(f"❌ Declined: {declines} ({declines/len(assessments)*100:.1f}%)")
    print()


def export_trace_to_markdown(assessment, output_file):
    """Export trace visualization to markdown file."""
    company = assessment.get("company_name", "Unknown")
    software = assessment.get("software_name", "Unknown")
    decision = assessment.get("decision", "unknown").upper()
    timestamp = assessment.get("timestamp", "")
    traces = assessment.get("traces", [])
    
    md_content = f"""# Trace Visualization: {software} @ {company}

**Decision**: {decision}  
**Timestamp**: {timestamp}  
**Total Steps**: {len(traces)}  

## Execution Timeline

```mermaid
gantt
    title Execution Timeline
    dateFormat  X
    axisFormat %S.%Ls
"""
    
    current_time = 0
    for i, trace in enumerate(traces, 1):
        step_name = trace.get("step", f"step_{i}").replace("_", " ").title()
        elapsed = trace.get("elapsed_time", 0)
        start = int(current_time * 1000)
        end = int((current_time + elapsed) * 1000)
        md_content += f"    {step_name} : {start}, {end}\n"
        current_time += elapsed
    
    md_content += "```\n\n"
    
    # Add detailed trace table
    md_content += "## Detailed Trace\n\n"
    md_content += "| Step | Tool | Time (s) | Details |\n"
    md_content += "|------|------|----------|----------|\n"
    
    for i, trace in enumerate(traces, 1):
        step_name = trace.get("step", "unknown")
        tool = trace.get("tool", "unknown")
        elapsed = trace.get("elapsed_time", 0)
        
        details = []
        if "results_count" in trace:
            details.append(f"{trace['results_count']} results")
        if "vulnerabilities_found" in trace:
            details.append(f"{trace['vulnerabilities_found']} vulns")
        if "criticality" in trace:
            details.append(f"{trace['criticality']} criticality")
        
        details_str = ", ".join(details) if details else "-"
        
        md_content += f"| {i}. {step_name} | {tool} | {elapsed:.2f}s | {details_str} |\n"
    
    md_content += "\n"
    
    # Add results
    md_content += "## Results\n\n"
    md_content += f"- **Decision**: {decision}\n"
    md_content += f"- **Criticality**: {assessment.get('criticality_level', 'unknown').upper()}\n"
    md_content += f"- **Vulnerability Summary**: {assessment.get('vulnerability_summary', 'N/A')}\n"
    
    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return output_file


def main():
    """Main function."""
    print("="*80)
    print("TRACE VISUALIZATION (Bonus #2)")
    print("="*80)
    
    # Load assessments
    print("\nLoading assessment results from outputs/...")
    assessments = load_assessment_results()
    
    if not assessments:
        print("❌ No assessment results found in outputs/")
        print("   Run some assessments first:")
        print("   python run.py --software 'Software' --company 'Company'")
        return
    
    print(f"✅ Found {len(assessments)} assessment(s)\n")
    
    # Show summary table
    create_summary_table(assessments)
    
    # Show performance analysis
    create_performance_report(assessments)
    
    # Show detailed traces
    print("="*80)
    print("DETAILED EXECUTION TRACES")
    print("="*80)
    
    for assessment in assessments:
        visualize_trace(assessment)
    
    # Export to markdown
    print("="*80)
    print("EXPORTING TRACE VISUALIZATIONS")
    print("="*80)
    print()
    
    os.makedirs("viz/traces", exist_ok=True)
    
    for assessment in assessments:
        software = assessment.get("software_name", "Unknown").replace(" ", "_")
        company = assessment.get("company_name", "Unknown").replace(" ", "_")
        filename = f"viz/traces/{software}_{company}_trace.md"
        
        export_trace_to_markdown(assessment, filename)
        print(f"✅ Exported: {filename}")
    
    print()
    print("="*80)
    print("TRACE VISUALIZATION COMPLETE!")
    print("="*80)
    print()
    print("📊 Summary available in terminal")
    print("📁 Detailed traces exported to viz/traces/")
    print("🔍 View markdown files for timeline diagrams")
    print()


if __name__ == "__main__":
    main()

