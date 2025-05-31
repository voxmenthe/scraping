#!/usr/bin/env python3
"""
Comprehensive demo of the partial diff functionality
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraping.github_analyzer import DiffAnnotator, ReportGenerator, FileChange

def create_demo_files():
    """Create demo old and new Python files"""
    
    old_content = '''#!/usr/bin/env python3
"""
Example Python module - OLD VERSION
"""

import os
import sys

class Calculator:
    """A simple calculator class"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract b from a"""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def old_method(self):
        """This method will be removed"""
        print("This method is deprecated")
        return None

def helper_function():
    """A helper function"""
    return "helper"

# Global constant
VERSION = "1.0.0"
DEBUG = False
'''

    new_content = '''#!/usr/bin/env python3
"""
Example Python module - NEW VERSION
Enhanced with new features!
"""

import os
import sys
import math  # New import

class Calculator:
    """A simple calculator class with enhanced features"""
    
    def __init__(self, precision=2):
        self.history = []
        self.precision = precision  # New attribute
    
    def add(self, a, b):
        """Add two numbers"""
        result = round(a + b, self.precision)  # Enhanced with precision
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract b from a"""
        result = round(a - b, self.precision)  # Enhanced with precision
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers - NEW METHOD"""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history - NEW METHOD"""
        return self.history.copy()

def helper_function():
    """A helper function"""
    return "helper"

def new_helper_function():
    """A brand new helper function"""
    return "new_helper"

# Global constants
VERSION = "2.0.0"  # Updated version
DEBUG = False
PI_APPROXIMATION = 3.14159  # New constant
'''

    return old_content, new_content

def demo_all_annotation_styles():
    """Demonstrate all annotation styles"""
    print("🎯 COMPREHENSIVE PARTIAL DIFF DEMO")
    print("=" * 60)
    
    old_content, new_content = create_demo_files()
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Output directory: {temp_path}")
        
        # Create a mock FileChange object
        file_change = FileChange(
            filename="calculator.py",
            repo="demo/example",
            old_content=old_content,
            new_content=new_content,
            status="modified",
            old_sha="abc123",
            new_sha="def456"
        )
        
        # Test all annotation styles
        styles = ["comment", "inline", "html"]
        
        for style in styles:
            print(f"\n🎨 Testing {style.upper()} annotation style:")
            print("-" * 40)
            
            # Create report generator with this style
            report_gen = ReportGenerator(temp_path, annotation_style=style)
            
            # Save files with annotations
            result = report_gen.save_file_versions(
                file_change, 
                f"demo_{style}", 
                save_annotated=True
            )
            
            # Show what files were created
            for file_type, path in result.items():
                if path:
                    file_path = Path(path)
                    print(f"  ✅ {file_type}: {file_path.name}")
                    
                    # Show file size
                    size = file_path.stat().st_size
                    print(f"     Size: {size} bytes")
                    
                    # For HTML files, show first few lines
                    if style == "html" and "annotated" in file_type:
                        print(f"     Preview (first 10 lines):")
                        with open(file_path, 'r') as f:
                            lines = f.readlines()[:10]
                            for i, line in enumerate(lines, 1):
                                print(f"     {i:2}: {line.rstrip()}")
                        print("     ...")
        
        # Show directory structure
        print(f"\n📂 Generated file structure:")
        print("-" * 40)
        for root, dirs, files in os.walk(temp_path):
            level = root.replace(str(temp_path), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = Path(root) / file
                size = file_path.stat().st_size
                print(f"{subindent}{file} ({size} bytes)")
        
        # Demonstrate DiffAnnotator directly
        print(f"\n🔍 Direct DiffAnnotator Analysis:")
        print("-" * 40)
        
        annotator = DiffAnnotator(old_content, new_content, "comment")
        summary = annotator.get_change_summary()
        
        print("Change Summary:")
        for key, value in summary.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Show a sample of annotated content
        print(f"\n📝 Sample annotated OLD content (first 15 lines):")
        print("-" * 40)
        annotated_old = annotator.create_annotated_old_file()
        old_lines = annotated_old.split('\n')[:15]
        for i, line in enumerate(old_lines, 1):
            print(f"{i:2}: {line}")
        print("...")
        
        print(f"\n📝 Sample annotated NEW content (first 15 lines):")
        print("-" * 40)
        annotated_new = annotator.create_annotated_new_file()
        new_lines = annotated_new.split('\n')[:15]
        for i, line in enumerate(new_lines, 1):
            print(f"{i:2}: {line}")
        print("...")
        
        # Copy one HTML file to current directory for easy viewing
        html_files = list(temp_path.rglob("*.html"))
        if html_files:
            sample_html = html_files[0]
            dest_path = Path("sample_annotated_diff.html")
            shutil.copy2(sample_html, dest_path)
            print(f"\n🌐 Sample HTML file copied to: {dest_path}")
            print(f"   Open this file in a web browser to see the styled diff!")
        
        print(f"\n✨ Demo completed! All annotation styles working correctly.")
        print(f"🎉 The partial diff feature is ready for use!")

if __name__ == "__main__":
    demo_all_annotation_styles() 