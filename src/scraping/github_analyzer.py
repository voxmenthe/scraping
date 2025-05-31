#!/usr/bin/env python3
"""
GitHub Repository Python File Change Analyzer

This module analyzes changes to *.py files across GitHub repositories,
identifies modified functions/classes, and provides side-by-side comparisons.
"""

import ast
import json
import os
import base64
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set, Union
from pathlib import Path
import requests
import subprocess

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip


@dataclass
class FunctionInfo:
    """Information about a function or class definition"""
    name: str
    start_line: int
    end_line: int
    source_code: str
    node_type: str  # 'function' or 'class'
    decorators: List[str] = None
    docstring: Optional[str] = None

    def __post_init__(self):
        if self.decorators is None:
            self.decorators = []


@dataclass
class FileChange:
    """Information about a changed file"""
    filename: str
    repo: str
    old_content: str
    new_content: str
    status: str  # 'added', 'modified', 'removed'
    old_sha: Optional[str] = None
    new_sha: Optional[str] = None


@dataclass
class AnalysisResult:
    """Results of analyzing a repository"""
    repo: str
    file_changes: List[FileChange]
    function_changes: Dict[str, Dict[str, Tuple[Optional[FunctionInfo], Optional[FunctionInfo]]]]
    total_files_changed: int
    total_functions_changed: int


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    pass


class GitHubAnalyzer:
    """Analyzes GitHub repositories for Python file changes"""
    
    def __init__(self, token: Optional[str] = None, output_dir: str = "output"):
        """Initialize with GitHub token for API access"""
        github_api_token = os.getenv('GITHUB_TOKEN')
        self.token = token or github_api_token
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass token parameter.")
        
        # Debug: Show token source (remove this in production)
        if token:
            print(f"Debug: Using provided token (length: {len(token)})")
        elif github_api_token:
            print(f"Debug: Using environment token (length: {len(github_api_token)})")
        else:
            print("Debug: No token found")
        
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Python-Analyzer/1.0'
        }
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Rate limiting
        self.request_count = 0
        self.max_requests_per_hour = 5000
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make a rate-limited request to GitHub API"""
        self.request_count += 1
        if self.request_count > self.max_requests_per_hour:
            raise GitHubAPIError("Rate limit exceeded")
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 403 and 'rate limit' in response.text.lower():
            raise GitHubAPIError("GitHub API rate limit exceeded")
        elif response.status_code == 401:
            raise GitHubAPIError("GitHub API authentication failed")
        elif response.status_code != 200:
            raise GitHubAPIError(f"GitHub API error: {response.status_code} - {response.text}")
        
        return response
    
    def get_repository_comparison(self, repo: str, base_ref: str, head_ref: str) -> Dict:
        """Get comparison between two refs using GitHub REST API"""
        url = f"https://api.github.com/repos/{repo}/compare/{base_ref}...{head_ref}"
        response = self._make_request(url)
        return response.json()
    
    def get_file_content(self, repo: str, path: str, ref: str) -> Tuple[str, Optional[str]]:
        """Get file content at specific commit/ref, returns (content, sha)"""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        params = {'ref': ref}
        
        try:
            response = self._make_request(url, params)
            content_data = response.json()
            
            if isinstance(content_data, list):
                # Path is a directory, not a file
                return "", None
            
            # Decode base64 content
            content = base64.b64decode(content_data['content']).decode('utf-8')
            sha = content_data.get('sha')
            return content, sha
            
        except GitHubAPIError as e:
            if "404" in str(e):
                return "", None  # File doesn't exist at this ref
            raise
    
    def get_commits_in_range(self, repo: str, since: Optional[str] = None, until: Optional[str] = None, 
                           path: Optional[str] = None) -> List[Dict]:
        """Get commits in a repository, optionally filtered by date range and path"""
        url = f"https://api.github.com/repos/{repo}/commits"
        params = {}
        
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        if path:
            params['path'] = path
        
        response = self._make_request(url, params)
        return response.json()
    
    def get_changed_python_files(self, repo: str, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> List[FileChange]:
        """Get all changed Python files between two refs"""
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
            old_sha = None
            new_sha = None
            
            try:
                if status != 'added':
                    old_content, old_sha = self.get_file_content(repo, filename, base_ref)
                if status != 'removed':
                    new_content, new_sha = self.get_file_content(repo, filename, head_ref)
                
                changed_files.append(FileChange(
                    filename=filename,
                    repo=repo,
                    old_content=old_content,
                    new_content=new_content,
                    status=status,
                    old_sha=old_sha,
                    new_sha=new_sha
                ))
            except Exception as e:
                print(f"Warning: Could not process {filename}: {e}")
                continue
        
        return changed_files
    
    def analyze_repository(self, repo: str, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> AnalysisResult:
        """Analyze a single repository for changes"""
        print(f"Analyzing repository: {repo}")
        
        changed_files = self.get_changed_python_files(repo, base_ref, head_ref)
        function_changes = {}
        total_functions_changed = 0
        
        for file_change in changed_files:
            print(f"  Processing: {file_change.filename}")
            
            # Extract functions and classes from old and new versions
            ast_analyzer = PythonASTAnalyzer()
            old_definitions = ast_analyzer.extract_functions_and_classes(file_change.old_content)
            new_definitions = ast_analyzer.extract_functions_and_classes(file_change.new_content)
            
            # Find changes
            changes = ast_analyzer.find_changed_definitions(old_definitions, new_definitions)
            
            if changes:
                function_changes[file_change.filename] = changes
                total_functions_changed += len(changes)
        
        return AnalysisResult(
            repo=repo,
            file_changes=changed_files,
            function_changes=function_changes,
            total_files_changed=len(changed_files),
            total_functions_changed=total_functions_changed
        )


class PythonASTAnalyzer:
    """Analyzer for Python AST to extract functions and classes"""
    
    @staticmethod
    def extract_functions_and_classes(source_code: str) -> List[FunctionInfo]:
        """Extract function and class definitions from Python source code"""
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
                self._extract_definition(node, 'async_function')
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
                
                # Extract decorators
                decorators = []
                for decorator in getattr(node, 'decorator_list', []):
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        decorators.append(ast.unparse(decorator))
                    else:
                        decorators.append(ast.unparse(decorator))
                
                # Extract docstring
                docstring = None
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Str)):
                    docstring = node.body[0].value.s
                elif (node.body and isinstance(node.body[0], ast.Expr) and 
                      isinstance(node.body[0].value, ast.Constant) and 
                      isinstance(node.body[0].value.value, str)):
                    docstring = node.body[0].value.value
                
                definitions.append(FunctionInfo(
                    name=node.name,
                    start_line=start_line,
                    end_line=end_line,
                    source_code=source_code,
                    node_type=node_type,
                    decorators=decorators,
                    docstring=docstring
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
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_side_by_side_comparison(self, old_def: Optional[FunctionInfo], 
                                       new_def: Optional[FunctionInfo], name: str) -> str:
        """Generate side-by-side comparison of old and new code"""
        result = [f"\n{'='*80}"]
        
        node_type = (new_def or old_def).node_type.upper()
        result.append(f"{node_type}: {name}")
        result.append('='*80)
        
        if old_def is None:
            result.append("STATUS: ADDED")
            result.append(f"Decorators: {new_def.decorators}")
            if new_def.docstring:
                result.append(f"Docstring: {new_def.docstring[:100]}...")
            result.append("\nNEW VERSION:")
            result.append("-" * 40)
            result.append(new_def.source_code)
        elif new_def is None:
            result.append("STATUS: REMOVED")
            result.append(f"Decorators: {old_def.decorators}")
            if old_def.docstring:
                result.append(f"Docstring: {old_def.docstring[:100]}...")
            result.append("\nOLD VERSION:")
            result.append("-" * 40)
            result.append(old_def.source_code)
        else:
            result.append("STATUS: MODIFIED")
            result.append(f"Old decorators: {old_def.decorators}")
            result.append(f"New decorators: {new_def.decorators}")
            result.append("\nOLD VERSION:")
            result.append("-" * 40)
            result.append(old_def.source_code)
            result.append("\nNEW VERSION:")
            result.append("-" * 40)
            result.append(new_def.source_code)
        
        return '\n'.join(result)
    
    def save_file_versions(self, file_change: FileChange, output_subdir: str) -> Tuple[Optional[str], Optional[str]]:
        """Save old and new versions of a file to disk"""
        repo_name = file_change.repo.replace('/', '_')
        file_base = Path(file_change.filename).stem
        file_ext = Path(file_change.filename).suffix
        
        output_path = self.output_dir / output_subdir / repo_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        old_file_path = None
        new_file_path = None
        
        if file_change.old_content:
            old_file_path = output_path / f"{file_base}_old{file_ext}"
            with open(old_file_path, 'w', encoding='utf-8') as f:
                f.write(file_change.old_content)
        
        if file_change.new_content:
            new_file_path = output_path / f"{file_base}_new{file_ext}"
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(file_change.new_content)
        
        return str(old_file_path) if old_file_path else None, str(new_file_path) if new_file_path else None
    
    def generate_comprehensive_report(self, results: List[AnalysisResult], 
                                    output_filename: str = "github_changes_comprehensive_report.txt") -> str:
        """Generate a comprehensive report with all analysis results"""
        report_path = self.output_dir / output_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("GITHUB REPOSITORY PYTHON CHANGES COMPREHENSIVE ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            total_repos = len(results)
            total_files = sum(r.total_files_changed for r in results)
            total_functions = sum(r.total_functions_changed for r in results)
            
            f.write(f"SUMMARY:\n")
            f.write(f"Repositories analyzed: {total_repos}\n")
            f.write(f"Total Python files changed: {total_files}\n")
            f.write(f"Total functions/classes changed: {total_functions}\n\n")
            
            # Detailed analysis for each repository
            for result in results:
                f.write(f"Repository: {result.repo}\n")
                f.write(f"Files changed: {result.total_files_changed}\n")
                f.write(f"Functions/classes changed: {result.total_functions_changed}\n")
                f.write("=" * 60 + "\n\n")
                
                for file_change in result.file_changes:
                    if file_change.filename in result.function_changes:
                        f.write(f"File: {file_change.filename} (Status: {file_change.status})\n")
                        f.write(f"Old SHA: {file_change.old_sha}\n")
                        f.write(f"New SHA: {file_change.new_sha}\n")
                        f.write("-" * 40 + "\n")
                        
                        changes = result.function_changes[file_change.filename]
                        for name, (old_def, new_def) in changes.items():
                            comparison = self.generate_side_by_side_comparison(old_def, new_def, name)
                            f.write(comparison)
                            f.write("\n\n")
                
                f.write("\n" + "="*80 + "\n\n")
        
        return str(report_path)


class GitHubChangeTracker:
    """Main class for tracking GitHub repository changes"""
    
    def __init__(self, token: Optional[str] = None, output_dir: str = "github_analysis_output"):
        # If no token provided, try to get from environment
        if token is None:
            token = os.getenv('GITHUB_TOKEN')
        
        self.github_analyzer = GitHubAnalyzer(token, output_dir)
        self.report_generator = ReportGenerator(Path(output_dir))
        self.output_dir = Path(output_dir)
    
    def analyze_repositories(self, repos: List[str], base_ref: str = "HEAD~1", 
                           head_ref: str = "HEAD", save_files: bool = True) -> List[AnalysisResult]:
        """Analyze multiple repositories and generate comprehensive reports"""
        all_results = []
        
        for repo in repos:
            try:
                result = self.github_analyzer.analyze_repository(repo, base_ref, head_ref)
                all_results.append(result)
                
                # Save individual file versions if requested
                if save_files:
                    for file_change in result.file_changes:
                        old_path, new_path = self.report_generator.save_file_versions(
                            file_change, f"file_versions_{base_ref}_{head_ref}"
                        )
                        if old_path:
                            print(f"  Saved old version: {old_path}")
                        if new_path:
                            print(f"  Saved new version: {new_path}")
                
            except Exception as e:
                print(f"Error analyzing repository {repo}: {e}")
                continue
        
        # Generate comprehensive report
        report_path = self.report_generator.generate_comprehensive_report(all_results)
        print(f"\nComprehensive report saved to: {report_path}")
        
        return all_results
    
    def analyze_repository_history(self, repo: str, days_back: int = 7) -> List[AnalysisResult]:
        """Analyze recent history of a repository"""
        from datetime import datetime, timedelta
        
        since_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        commits = self.github_analyzer.get_commits_in_range(repo, since=since_date)
        
        results = []
        for i in range(len(commits) - 1):
            base_sha = commits[i + 1]['sha']
            head_sha = commits[i]['sha']
            
            try:
                result = self.github_analyzer.analyze_repository(repo, base_sha, head_sha)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing commit range {base_sha}..{head_sha}: {e}")
                continue
        
        return results


def get_repos_from_gh_cli() -> List[str]:
    """Get repositories using GitHub CLI if available"""
    try:
        result = subprocess.run(['gh', 'repo', 'list', '--json', 'nameWithOwner'], 
                              capture_output=True, text=True, check=True)
        repos_data = json.loads(result.stdout)
        return [repo['nameWithOwner'] for repo in repos_data[:5]]  # Limit to first 5
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        print("GitHub CLI not available or not authenticated. Please provide repositories manually.")
        return [] 