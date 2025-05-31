<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Read the documentation for the github API and github cli and write a python script to gather all of the changes to *.py files in a list of github repos, and identify which functions or classes were changed, and then provide the full new function/class and old function/class side-by-side in the same file. (so not really a diff view - more like an expanded old/new comparison). If needed, you can also do AST parsing as well - make sure to read the documentation for that too if needed

Based on the GitHub API documentation and Python AST resources, I'll create a comprehensive Python script that gathers changes to Python files across repositories and identifies modified functions/classes with side-by-side comparisons.

## Python Script for GitHub Repository Analysis

```python
#!/usr/bin/env python3
"""
GitHub Repository Python File Change Analyzer

This script analyzes changes to *.py files across GitHub repositories,
identifies modified functions/classes, and provides side-by-side comparisons.
"""

import ast
import json
import requests
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set
import difflib
import os

@dataclass
class FunctionInfo:
    """Information about a function or class definition"""
    name: str
    start_line: int
    end_line: int
    source_code: str
    node_type: str  # 'function' or 'class'

@dataclass
class FileChange:
    """Information about a changed file"""
    filename: str
    repo: str
    old_content: str
    new_content: str
    status: str  # 'added', 'modified', 'removed'

class GitHubAnalyzer:
    def __init__(self, token: Optional[str] = None):
        """Initialize with GitHub token for API access"""
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}' if self.token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_repository_comparison(self, repo: str, base_ref: str, head_ref: str) -> Dict:
        """Get comparison between two refs using GitHub REST API"""
        url = f"https://api.github.com/repos/{repo}/compare/{base_ref}...{head_ref}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, repo: str, path: str, ref: str) -> str:
        """Get file content at specific commit/ref"""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        params = {'ref': ref}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 404:
            return ""  # File doesn't exist at this ref
        
        response.raise_for_status()
        content = response.json()
        
        # Decode base64 content
        import base64
        return base64.b64decode(content['content']).decode('utf-8')
    
    def get_changed_python_files(self, repo: str, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> List[FileChange]:
        """Get all changed Python files between two refs"""[^1][^2]
        comparison = self.get_repository_comparison(repo, base_ref, head_ref)
        
        changed_files = []
        for file_info in comparison.get('files', []):
            filename = file_info['filename']
            
            # Only process Python files
            if not filename.endswith('.py'):
                continue
            
            status = file_info['status']
            old_content = ""
            new_content = ""
            
            try:
                if status != 'added':
                    old_content = self.get_file_content(repo, filename, base_ref)
                if status != 'removed':
                    new_content = self.get_file_content(repo, filename, head_ref)
                
                changed_files.append(FileChange(
                    filename=filename,
                    repo=repo,
                    old_content=old_content,
                    new_content=new_content,
                    status=status
                ))
            except Exception as e:
                print(f"Warning: Could not process {filename}: {e}")
                continue
        
        return changed_files

class PythonASTAnalyzer:
    """Analyzer for Python AST to extract functions and classes"""
    
    @staticmethod
    def extract_functions_and_classes(source_code: str) -> List[FunctionInfo]:
        """Extract function and class definitions from Python source code"""[^7][^8][^11][^13]
        if not source_code.strip():
            return []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"Syntax error in Python code: {e}")
            return []
        
        definitions = []
        source_lines = source_code.splitlines()
        
        class DefinitionVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                self._extract_definition(node, 'function')
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                self._extract_definition(node, 'function')
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                self._extract_definition(node, 'class')
                self.generic_visit(node)
            
            def _extract_definition(self, node, node_type):
                start_line = node.lineno - 1  # Convert to 0-based indexing
                end_line = getattr(node, 'end_lineno', start_line + 1) - 1
                
                # Extract source code for this definition
                definition_lines = source_lines[start_line:end_line + 1]
                source_code = '\n'.join(definition_lines)
                
                definitions.append(FunctionInfo(
                    name=node.name,
                    start_line=start_line,
                    end_line=end_line,
                    source_code=source_code,
                    node_type=node_type
                ))
        
        visitor = DefinitionVisitor()
        visitor.visit(tree)
        
        return definitions
    
    @staticmethod
    def find_changed_definitions(old_definitions: List[FunctionInfo], 
                               new_definitions: List[FunctionInfo]) -> Dict[str, Tuple[Optional[FunctionInfo], Optional[FunctionInfo]]]:
        """Find changed, added, or removed function/class definitions"""
        old_by_name = {d.name: d for d in old_definitions}
        new_by_name = {d.name: d for d in new_definitions}
        
        all_names = set(old_by_name.keys()) | set(new_by_name.keys())
        changes = {}
        
        for name in all_names:
            old_def = old_by_name.get(name)
            new_def = new_by_name.get(name)
            
            # Check if there's a change
            if old_def is None:  # Added
                changes[name] = (None, new_def)
            elif new_def is None:  # Removed
                changes[name] = (old_def, None)
            elif old_def.source_code != new_def.source_code:  # Modified
                changes[name] = (old_def, new_def)
        
        return changes

class ReportGenerator:
    """Generate reports for the analysis results"""
    
    @staticmethod
    def generate_side_by_side_comparison(old_code: Optional[str], new_code: Optional[str], name: str, node_type: str) -> str:
        """Generate side-by-side comparison of old and new code"""
        result = [f"\n{'='*80}"]
        result.append(f"{node_type.upper()}: {name}")
        result.append('='*80)
        
        if old_code is None:
            result.append("STATUS: ADDED")
            result.append("\nNEW VERSION:")
            result.append("-" * 40)
            result.append(new_code or "")
        elif new_code is None:
            result.append("STATUS: REMOVED")
            result.append("\nOLD VERSION:")
            result.append("-" * 40)
            result.append(old_code or "")
        else:
            result.append("STATUS: MODIFIED")
            result.append("\nOLD VERSION:")
            result.append("-" * 40)
            result.append(old_code)
            result.append("\nNEW VERSION:")
            result.append("-" * 40)
            result.append(new_code)
        
        return '\n'.join(result)

def analyze_repositories(repos: List[str], base_ref: str = "HEAD~1", head_ref: str = "HEAD", 
                        output_file: str = "github_changes_report.txt") -> None:
    """Main function to analyze multiple repositories"""[^4][^5][^9]
    github_analyzer = GitHubAnalyzer()
    ast_analyzer = PythonASTAnalyzer()
    report_generator = ReportGenerator()
    
    all_results = []
    
    for repo in repos:
        print(f"Analyzing repository: {repo}")
        
        try:
            # Get changed Python files
            changed_files = github_analyzer.get_changed_python_files(repo, base_ref, head_ref)
            
            for file_change in changed_files:
                print(f"  Processing: {file_change.filename}")
                
                # Extract functions and classes from old and new versions
                old_definitions = ast_analyzer.extract_functions_and_classes(file_change.old_content)
                new_definitions = ast_analyzer.extract_functions_and_classes(file_change.new_content)
                
                # Find changes
                changes = ast_analyzer.find_changed_definitions(old_definitions, new_definitions)
                
                if changes:
                    file_results = {
                        'repo': repo,
                        'file': file_change.filename,
                        'status': file_change.status,
                        'changes': []
                    }
                    
                    for name, (old_def, new_def) in changes.items():
                        old_code = old_def.source_code if old_def else None
                        new_code = new_def.source_code if new_def else None
                        node_type = (new_def or old_def).node_type
                        
                        comparison = report_generator.generate_side_by_side_comparison(
                            old_code, new_code, name, node_type
                        )
                        
                        file_results['changes'].append({
                            'name': name,
                            'type': node_type,
                            'comparison': comparison
                        })
                    
                    all_results.append(file_results)
        
        except Exception as e:
            print(f"Error analyzing repository {repo}: {e}")
            continue
    
    # Generate final report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("GITHUB REPOSITORY PYTHON CHANGES ANALYSIS REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        for result in all_results:
            f.write(f"Repository: {result['repo']}\n")
            f.write(f"File: {result['file']} (Status: {result['status']})\n")
            f.write("=" * 60 + "\n")
            
            for change in result['changes']:
                f.write(change['comparison'])
                f.write("\n\n")
    
    print(f"\nAnalysis complete! Report saved to: {output_file}")
    print(f"Total files analyzed: {len(all_results)}")

# CLI Integration for GitHub CLI users
def get_repos_from_gh_cli() -> List[str]:
    """Get repositories using GitHub CLI if available"""[^5][^9]
    try:
        # Get repositories the user has access to
        result = subprocess.run(['gh', 'repo', 'list', '--json', 'nameWithOwner'], 
                              capture_output=True, text=True, check=True)
        repos_data = json.loads(result.stdout)
        return [repo['nameWithOwner'] for repo in repos_data[:5]]  # Limit to first 5
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        print("GitHub CLI not available or not authenticated. Please provide repositories manually.")
        return []

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        # Repositories provided as command line arguments
        repositories = sys.argv[1:]
    else:
        # Try to get repositories from GitHub CLI
        repositories = get_repos_from_gh_cli()
        
        if not repositories:
            # Fallback to example repositories
            repositories = [
                "octocat/Hello-World",
                # Add your repositories here
            ]
    
    print("Starting GitHub Repository Analysis...")
    print(f"Repositories to analyze: {repositories}")
    
    # You can customize these parameters:
    # - base_ref: The base commit/branch to compare from (default: HEAD~1)
    # - head_ref: The head commit/branch to compare to (default: HEAD)
    # - output_file: Where to save the report
    
    analyze_repositories(
        repos=repositories,
        base_ref="HEAD~10",  # Look at last 10 commits
        head_ref="HEAD",
        output_file="python_changes_analysis.txt"
    )
```


## Key Features

**GitHub API Integration**

- Uses GitHub REST API to compare commits and get file changes[^1][^2]
- Supports authentication via GitHub token
- Handles file content retrieval at different commit refs

**Python AST Analysis**

- Parses Python files using `ast.parse()` to build Abstract Syntax Trees[^7][^8][^11][^13]
- Extracts `FunctionDef`, `AsyncFunctionDef`, and `ClassDef` nodes
- Identifies function and class boundaries with line numbers

**Change Detection**

- Compares old and new versions of functions/classes
- Identifies added, removed, and modified definitions
- Provides full source code for each definition

**Side-by-Side Comparison**

- Generates comprehensive reports with old/new code side-by-side
- Shows status (ADDED/REMOVED/MODIFIED) for each change
- Outputs to a readable text file format


## Usage Examples

```bash
# Set GitHub token
export GITHUB_TOKEN="your_token_here"

# Analyze specific repositories
python github_analyzer.py owner/repo1 owner/repo2

# Or let it discover repos via GitHub CLI
python github_analyzer.py
```


## Requirements

Install required dependencies:

```bash
pip install requests
```

For GitHub CLI integration, install the [GitHub CLI](https://cli.github.com/)[^5][^9]:

```bash
# Authentication
gh auth login
```

The script will generate a detailed report showing exactly what functions and classes changed, with complete old and new implementations displayed side-by-side for easy comparison.

<div style="text-align: center">⁂</div>

[^1]: https://docs.github.com/rest

[^2]: https://github.com/orgs/community/discussions/153074

[^3]: https://github.com/marketplace/actions/changed-files

[^4]: https://github.com/orgs/community/discussions/38462

[^5]: https://cli.github.com/manual/

[^6]: https://github.com/tj-actions/changed-files

[^7]: https://earthly.dev/blog/python-ast/

[^8]: https://arumoy.me/blogs/python-ast-extract-module-method-names/

[^9]: https://docs.github.com/en/github-cli/github-cli/quickstart

[^10]: https://deepsource.com/blog/python-asts-by-building-your-own-linter

[^11]: https://www.educative.io/answers/what-is-the-astparse-method-in-python

[^12]: https://www.devzery.com/post/guide-to-understanding-python-s-ast-abstract-syntax-trees

[^13]: https://docs.python.org/3/library/ast.html

[^14]: https://github.com/public-apis/public-apis

[^15]: https://github.com/topics/api-documentation

[^16]: https://docs.github.com/en/github-cli

[^17]: https://github.com/cli/cli

[^18]: https://stackoverflow.com/questions/69842270/extract-all-files-changed-in-repo-since-a-certain-date

[^19]: https://www.youtube.com/watch?v=OjPT15y2EpE

[^20]: https://stackoverflow.com/questions/44698193/how-to-get-a-list-of-classes-and-functions-from-a-python-file-without-importing

[^21]: https://docs.python.org/pl/3.7/library/ast.html

[^22]: https://docs.github.com

[^23]: https://superuser.com/questions/1791910/where-is-github-api-reference

[^24]: https://www.reddit.com/r/github/comments/1c6qqc7/how_can_i_get_a_list_of_modified_files_in_github/

[^25]: https://docs.github.com/en/graphql

[^26]: https://docs.github.com/en/github-cli/github-cli/about-github-cli

[^27]: https://www.youtube.com/watch?v=aIf-IYHXBWc

[^28]: https://docs.github.com/en/github-cli/github-cli

[^29]: https://github.com/marketplace/actions/get-all-changed-files

[^30]: https://stackoverflow.com/questions/76352198/how-to-compare-two-python-asts-ignoring-arguments

