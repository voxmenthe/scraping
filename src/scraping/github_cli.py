#!/usr/bin/env python3
"""
Command-line interface for GitHub Repository Change Analyzer
"""

import argparse
import os
import sys
from typing import List, Optional
from datetime import datetime, timedelta

from .github_analyzer import GitHubChangeTracker, get_repos_from_gh_cli


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repositories for Python file changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze specific repositories (last commit vs current)
  python -m scraping.github_cli owner/repo1 owner/repo2

  # Analyze with custom commit range
  python -m scraping.github_cli owner/repo --base HEAD~5 --head HEAD

  # Analyze repositories from GitHub CLI
  python -m scraping.github_cli --auto-discover

  # Analyze recent history
  python -m scraping.github_cli owner/repo --history --days 7

  # Custom output directory
  python -m scraping.github_cli owner/repo --output-dir my_analysis
        """
    )
    
    parser.add_argument(
        'repositories',
        nargs='*',
        help='Repository names in format owner/repo'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        help='GitHub API token (or set GITHUB_TOKEN environment variable)'
    )
    
    parser.add_argument(
        '--base',
        type=str,
        default='HEAD~1',
        help='Base reference for comparison (default: HEAD~1)'
    )
    
    parser.add_argument(
        '--head',
        type=str,
        default='HEAD',
        help='Head reference for comparison (default: HEAD)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='github_analysis_output',
        help='Output directory for results (default: github_analysis_output)'
    )
    
    parser.add_argument(
        '--auto-discover',
        action='store_true',
        help='Automatically discover repositories using GitHub CLI'
    )
    
    parser.add_argument(
        '--history',
        action='store_true',
        help='Analyze repository history instead of single comparison'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days back to analyze when using --history (default: 7)'
    )
    
    parser.add_argument(
        '--no-save-files',
        action='store_true',
        help='Do not save individual file versions to disk'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def validate_repositories(repos: List[str]) -> List[str]:
    """Validate repository format"""
    valid_repos = []
    for repo in repos:
        if '/' not in repo:
            print(f"Warning: Invalid repository format '{repo}'. Expected 'owner/repo'")
            continue
        valid_repos.append(repo)
    return valid_repos


def main():
    """Main CLI function"""
    args = parse_arguments()
    
    # Determine repositories to analyze
    repositories = []
    
    if args.auto_discover:
        print("Auto-discovering repositories using GitHub CLI...")
        repositories = get_repos_from_gh_cli()
        if not repositories:
            print("No repositories found via GitHub CLI. Please specify repositories manually.")
            sys.exit(1)
    elif args.repositories:
        repositories = validate_repositories(args.repositories)
        if not repositories:
            print("No valid repositories provided.")
            sys.exit(1)
    else:
        print("Please specify repositories or use --auto-discover")
        sys.exit(1)
    
    # Initialize the tracker
    try:
        tracker = GitHubChangeTracker(
            token=args.token,
            output_dir=args.output_dir
        )
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set GITHUB_TOKEN environment variable or use --token parameter")
        sys.exit(1)
    
    print(f"Starting GitHub Repository Analysis...")
    print(f"Output directory: {args.output_dir}")
    print(f"Repositories to analyze: {repositories}")
    
    if args.verbose:
        print(f"Base reference: {args.base}")
        print(f"Head reference: {args.head}")
        print(f"Save files: {not args.no_save_files}")
    
    try:
        if args.history:
            # Analyze repository history
            print(f"Analyzing repository history for the last {args.days} days...")
            all_results = []
            
            for repo in repositories:
                print(f"\nAnalyzing history for {repo}...")
                results = tracker.analyze_repository_history(repo, args.days)
                all_results.extend(results)
            
            if all_results:
                report_path = tracker.report_generator.generate_comprehensive_report(
                    all_results, f"history_analysis_{args.days}days.txt"
                )
                print(f"\nHistory analysis complete! Report saved to: {report_path}")
            else:
                print("No changes found in the specified time period.")
        
        else:
            # Analyze specific commit comparison
            results = tracker.analyze_repositories(
                repos=repositories,
                base_ref=args.base,
                head_ref=args.head,
                save_files=not args.no_save_files
            )
            
            if results:
                # Print summary
                total_files = sum(r.total_files_changed for r in results)
                total_functions = sum(r.total_functions_changed for r in results)
                
                print(f"\nAnalysis Summary:")
                print(f"Repositories analyzed: {len(results)}")
                print(f"Total Python files changed: {total_files}")
                print(f"Total functions/classes changed: {total_functions}")
                
                if args.verbose:
                    for result in results:
                        print(f"\n{result.repo}:")
                        print(f"  Files changed: {result.total_files_changed}")
                        print(f"  Functions/classes changed: {result.total_functions_changed}")
            else:
                print("No changes found.")
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main() 