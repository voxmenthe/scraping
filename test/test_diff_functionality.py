#!/usr/bin/env python3
"""
Test script to verify diff functionality for GitHub analyzer
"""

from src.scraping.github_analyzer import FunctionInfo, ReportGenerator, FileChange
from pathlib import Path
import tempfile
import os

def test_diff_generation():
    """Test the diff generation functionality"""
    
    # Create sample old and new function definitions
    old_function = FunctionInfo(
        name="calculate_sum",
        start_line=0,
        end_line=4,
        source_code="""def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers\"\"\"
    result = a + b
    return result""",
        node_type="function",
        decorators=[],
        docstring="Calculate sum of two numbers"
    )
    
    new_function = FunctionInfo(
        name="calculate_sum",
        start_line=0,
        end_line=5,
        source_code="""def calculate_sum(a, b, c=0):
    \"\"\"Calculate sum of two or three numbers\"\"\"
    result = a + b + c
    print(f"Sum calculated: {result}")
    return result""",
        node_type="function",
        decorators=[],
        docstring="Calculate sum of two or three numbers"
    )
    
    # Create sample commit information
    sample_commits = [
        {
            'sha': 'abc123def456789',
            'commit': {
                'message': 'Add optional third parameter to calculate_sum\n\nThis allows for more flexible sum calculations.',
                'author': {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'date': '2024-01-15T10:30:00Z'
                },
                'committer': {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'date': '2024-01-15T10:30:00Z'
                }
            }
        },
        {
            'sha': 'def456abc789123',
            'commit': {
                'message': 'Add debug print statement',
                'author': {
                    'name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'date': '2024-01-15T11:00:00Z'
                },
                'committer': {
                    'name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'date': '2024-01-15T11:00:00Z'
                }
            }
        }
    ]
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        report_generator = ReportGenerator(Path(temp_dir))
        
        # Test unified diff generation
        diff_content = report_generator.generate_unified_diff(
            old_function, new_function, "calculate_sum", "test_file.py"
        )
        
        print("Generated Unified Diff:")
        print("=" * 50)
        print(diff_content)
        print("=" * 50)
        
        # Test side-by-side comparison
        comparison = report_generator.generate_side_by_side_comparison(
            old_function, new_function, "calculate_sum"
        )
        
        print("\nGenerated Side-by-Side Comparison:")
        print("=" * 50)
        print(comparison)
        print("=" * 50)
        
        # Test diff file generation with commit information
        file_change = FileChange(
            filename="test_file.py",
            repo="owner/test-repo",
            old_content=old_function.source_code,
            new_content=new_function.source_code,
            status="modified",
            old_sha="abc123",
            new_sha="def456"
        )
        
        function_changes = {
            "calculate_sum": (old_function, new_function)
        }
        
        diff_files = report_generator.save_diff_files(
            file_change, function_changes, "test_output", sample_commits
        )
        
        print(f"\nGenerated diff files: {diff_files}")
        
        # Read and display the generated diff file content
        if diff_files:
            with open(diff_files[0], 'r') as f:
                diff_file_content = f.read()
            
            print("\nGenerated Diff File Content:")
            print("=" * 50)
            print(diff_file_content)
            print("=" * 50)

if __name__ == "__main__":
    test_diff_generation() 