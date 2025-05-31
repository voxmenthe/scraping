#!/usr/bin/env python3
"""
Test script for the DiffAnnotator functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraping.github_analyzer import DiffAnnotator

def test_diff_annotator():
    """Test the DiffAnnotator with sample code"""
    
    old_content = """def hello_world():
    print("Hello, World!")
    return True

def calculate_sum(a, b):
    result = a + b
    return result

def old_function():
    print("This will be removed")
    return None

# This line will be unchanged
CONSTANT = 42
"""

    new_content = """def hello_world():
    print("Hello, Universe!")  # Changed greeting
    return True

def calculate_sum(a, b, c=0):  # Added parameter
    result = a + b + c
    return result

def new_function():
    print("This is a new function")
    return "new"

# This line will be unchanged
CONSTANT = 42

# This is a completely new line
NEW_CONSTANT = 100
"""

    print("Testing DiffAnnotator...")
    print("=" * 50)
    
    # Test comment style
    print("\n1. Testing COMMENT style:")
    annotator = DiffAnnotator(old_content, new_content, "comment")
    
    print("\nOLD FILE (annotated):")
    print("-" * 30)
    print(annotator.create_annotated_old_file())
    
    print("\nNEW FILE (annotated):")
    print("-" * 30)
    print(annotator.create_annotated_new_file())
    
    print("\nCHANGE SUMMARY:")
    print("-" * 30)
    summary = annotator.get_change_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Test inline style
    print("\n\n2. Testing INLINE style:")
    print("=" * 50)
    annotator_inline = DiffAnnotator(old_content, new_content, "inline")
    
    print("\nOLD FILE (annotated):")
    print("-" * 30)
    print(annotator_inline.create_annotated_old_file())
    
    # Test HTML style (just show a snippet)
    print("\n\n3. Testing HTML style (first 20 lines):")
    print("=" * 50)
    annotator_html = DiffAnnotator(old_content, new_content, "html")
    html_old = annotator_html.create_annotated_old_file()
    html_lines = html_old.split('\n')[:20]
    print('\n'.join(html_lines))
    print("... (truncated)")

if __name__ == "__main__":
    test_diff_annotator() 