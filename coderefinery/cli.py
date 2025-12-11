#!/usr/bin/env python3
"""
Command-line interface for CodeRefinery.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

from coderefinery.analyzer import CodeAnalyzer
from coderefinery.models import AnalysisResult


def load_files_from_paths(file_paths: List[str]) -> List[Dict[str, str]]:
    """Load files from file paths."""
    files = []
    for path_str in file_paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Warning: File {path_str} not found", file=sys.stderr)
            continue
        
        if path.suffix != '.py':
            print(f"Warning: Skipping non-Python file {path_str}", file=sys.stderr)
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            files.append({
                "path": str(path),
                "language": "python",
                "content": content
            })
        except Exception as e:
            print(f"Error reading {path_str}: {e}", file=sys.stderr)
    
    return files


def load_files_from_json(json_path: str) -> tuple:
    """Load files and options from JSON input."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        files = data.get('files', [])
        options = data.get('options', {})
        
        return files, options
    except Exception as e:
        print(f"Error reading JSON file {json_path}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CodeRefinery - AI Code Reviewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze specific Python files
    coderefinery analyze app.py utils.py
    
    # Analyze with JSON input
    coderefinery analyze --input input.json
    
    # Apply black formatting
    coderefinery analyze --apply-black app.py
    
    # Set complexity threshold
    coderefinery analyze --max-complexity 15 app.py
    
    # Export reports
    coderefinery analyze --export markdown,json app.py
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze Python files')
    analyze_parser.add_argument('files', nargs='*', help='Python files to analyze')
    analyze_parser.add_argument('--input', '-i', help='JSON input file')
    analyze_parser.add_argument('--apply-black', action='store_true', 
                               help='Apply black formatting')
    analyze_parser.add_argument('--max-complexity', type=int, default=10,
                               help='Maximum cyclomatic complexity threshold')
    analyze_parser.add_argument('--export', help='Export formats (comma-separated): markdown,json')
    analyze_parser.add_argument('--output', '-o', help='Output file for results')
    analyze_parser.add_argument('--format', choices=['human', 'json'], default='human',
                               help='Output format')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version')
    
    args = parser.parse_args()
    
    if args.command == 'version':
        from coderefinery import __version__
        print(f"CodeRefinery {__version__}")
        return
    
    elif args.command == 'analyze':
        # Determine input source
        if args.input:
            files, options = load_files_from_json(args.input)
        else:
            if not args.files:
                print("Error: No input files specified", file=sys.stderr)
                sys.exit(1)
            files = load_files_from_paths(args.files)
            options = {}
        
        # Override options with command line args
        if args.apply_black:
            options['apply_black'] = True
        if args.max_complexity:
            options['max_complexity_threshold'] = args.max_complexity
        if args.export:
            options['export_formats'] = [fmt.strip() for fmt in args.export.split(',')]
        
        if not files:
            print("Error: No valid Python files to analyze", file=sys.stderr)
            sys.exit(1)
        
        # Perform analysis
        analyzer = CodeAnalyzer(max_complexity_threshold=options.get('max_complexity_threshold', 10))
        result = analyzer.analyze_files(files, options)
        
        # Output results
        if args.format == 'json':
            output = json.dumps(analyzer._serialize_result(result), indent=2)
        else:
            output = generate_human_readable_output(result)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
    
    else:
        parser.print_help()


def generate_human_readable_output(result: AnalysisResult) -> str:
    """Generate human-readable output."""
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append("CodeRefinery Analysis Report")
    lines.append("=" * 60)
    lines.append("")
    
    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 20)
    lines.append(result.summary)
    lines.append("")
    
    # Overall metrics
    lines.append("METRICS")
    lines.append("-" * 20)
    lines.append(f"Files analyzed: {result.overall_metrics.files_analyzed}")
    lines.append(f"Total issues: {result.overall_metrics.total_issues}")
    lines.append(f"High severity: {result.overall_metrics.high_severity}")
    lines.append(f"Complexity violations: {result.overall_metrics.complexity_violations}")
    lines.append("")
    
    # File details
    for i, file_analysis in enumerate(result.files, 1):
        lines.append(f"FILE {i}: {file_analysis.path}")
        lines.append("-" * (len(file_analysis.path) + 10))
        
        # Style issues
        if file_analysis.style_issues:
            lines.append("Style Issues:")
            for issue in file_analysis.style_issues:
                lines.append(f"  Line {issue.line:3d}: [{issue.code}] {issue.message}")
                lines.append(f"           Suggestion: {issue.suggestion}")
        
        # Bugs
        if file_analysis.bugs:
            lines.append("Potential Bugs:")
            for bug in file_analysis.bugs:
                lines.append(f"  Line {bug.line:3d}: [{bug.severity.value.upper()}] {bug.message}")
        
        # Complexity
        complexity_metrics = file_analysis.complexity.get('function_metrics', [])
        if complexity_metrics:
            lines.append("Complexity Metrics:")
            for metric in complexity_metrics:
                ccn_indicator = " ⚠️" if metric['ccn'] > 10 else ""
                lines.append(f"  {metric['name']:20s} (line {metric['lineno']:3d}): CCN = {metric['ccn']}{ccn_indicator}")
            lines.append(f"  Average CCN: {file_analysis.complexity.get('avg_ccn', 0):.1f}")
        
        # Snippets
        if file_analysis.after_snippet != file_analysis.before_snippet:
            lines.append("")
            lines.append("Suggested Changes:")
            lines.append("  Before:")
            for line in file_analysis.before_snippet.split('\n')[:10]:
                lines.append(f"    {line}")
            if len(file_analysis.before_snippet.split('\n')) > 10:
                lines.append("    ...")
            
            lines.append("  After:")
            for line in file_analysis.after_snippet.split('\n')[:10]:
                lines.append(f"    {line}")
            if len(file_analysis.after_snippet.split('\n')) > 10:
                lines.append("    ...")
        
        lines.append("")
    
    # Tool status
    if result.tool_status != "all tools available":
        lines.append("TOOL STATUS")
        lines.append("-" * 20)
        lines.append(result.tool_status)
        lines.append("")
    
    # Export info
    if result.export:
        lines.append("EXPORTS")
        lines.append("-" * 20)
        for format_name in result.export.keys():
            lines.append(f"- {format_name.upper()} report generated")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    main()