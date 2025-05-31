#!/usr/bin/env python3
"""
Example usage of the GitHub Repository Change Analyzer
"""

import os
from .github_analyzer import GitHubChangeTracker


def example_basic_analysis():
    """Example of basic repository analysis"""
    # Example repositories (replace with your own)
    repositories = [
        "octocat/Hello-World",
        # Add more repositories here
    ]
    
    # Initialize the tracker
    # Make sure to set GITHUB_TOKEN environment variable
    tracker = GitHubChangeTracker(output_dir="example_output")
    
    # Analyze repositories
    print("Running basic analysis...")
    results = tracker.analyze_repositories(
        repos=repositories,
        base_ref="HEAD~3",  # Compare last 3 commits
        head_ref="HEAD",
        save_files=True
    )
    
    # Print results
    for result in results:
        print(f"\nRepository: {result.repo}")
        print(f"Files changed: {result.total_files_changed}")
        print(f"Functions/classes changed: {result.total_functions_changed}")
        
        # Show details of changes
        for filename, changes in result.function_changes.items():
            print(f"\n  File: {filename}")
            for func_name, (old_def, new_def) in changes.items():
                if old_def is None:
                    print(f"    + {func_name} (added)")
                elif new_def is None:
                    print(f"    - {func_name} (removed)")
                else:
                    print(f"    ~ {func_name} (modified)")


def example_history_analysis():
    """Example of analyzing repository history"""
    repo = "octocat/Hello-World"
    
    tracker = GitHubChangeTracker(output_dir="history_output")
    
    print(f"Analyzing history for {repo}...")
    results = tracker.analyze_repository_history(repo, days_back=14)
    
    print(f"Found {len(results)} commit ranges with changes")
    for result in results:
        print(f"  Changes: {result.total_functions_changed} functions/classes")


def example_custom_analysis():
    """Example of custom analysis with specific commits"""
    repo = "octocat/Hello-World"
    
    tracker = GitHubChangeTracker(output_dir="custom_output")
    
    # Analyze specific commit range
    result = tracker.github_analyzer.analyze_repository(
        repo=repo,
        base_ref="7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",  # Specific commit SHA
        head_ref="HEAD"
    )
    
    print(f"Custom analysis for {repo}:")
    print(f"Files changed: {result.total_files_changed}")
    print(f"Functions/classes changed: {result.total_functions_changed}")


def example_with_filtering():
    """Example showing how to filter results"""
    repositories = ["octocat/Hello-World"]
    
    tracker = GitHubChangeTracker(output_dir="filtered_output")
    results = tracker.analyze_repositories(repositories)
    
    # Filter to only show added functions
    for result in results:
        print(f"\nNew functions/classes in {result.repo}:")
        for filename, changes in result.function_changes.items():
            added_items = [(name, new_def) for name, (old_def, new_def) in changes.items() 
                          if old_def is None and new_def is not None]
            
            if added_items:
                print(f"  {filename}:")
                for name, func_def in added_items:
                    print(f"    + {func_def.node_type}: {name}")
                    if func_def.decorators:
                        print(f"      Decorators: {func_def.decorators}")


if __name__ == "__main__":
    # Make sure you have GITHUB_TOKEN set in your environment
    if not os.environ.get('GITHUB_TOKEN'):
        print("Please set GITHUB_TOKEN environment variable")
        print("You can get a token from: https://github.com/settings/tokens")
        exit(1)
    
    print("GitHub Repository Change Analyzer Examples")
    print("=" * 50)
    
    try:
        # Run examples (uncomment the ones you want to try)
        example_basic_analysis()
        # example_history_analysis()
        # example_custom_analysis()
        # example_with_filtering()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have a valid GITHUB_TOKEN and internet connection") 