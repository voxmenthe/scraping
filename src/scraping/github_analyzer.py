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
import difflib
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


class DiffAnnotator:
    """Creates annotated versions of old and new files showing changes"""
    
    def __init__(self, old_content: str, new_content: str, annotation_style: str = "comment"):
        self.old_content = old_content
        self.new_content = new_content
        self.annotation_style = annotation_style
        self.diff_info = self._compute_diff()
    
    def _compute_diff(self) -> Dict:
        """Compute line-by-line differences between old and new content"""
        old_lines = self.old_content.splitlines() if self.old_content else []
        new_lines = self.new_content.splitlines() if self.new_content else []
        
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        changes = {
            'old_line_status': {},  # line_num -> 'unchanged'|'changed'|'removed'
            'new_line_status': {},  # line_num -> 'unchanged'|'changed'|'added'
            'line_mappings': {}     # old_line_num -> new_line_num for changed lines
        }
        
        # Initialize all lines as unchanged
        for i in range(len(old_lines)):
            changes['old_line_status'][i] = 'unchanged'
        for i in range(len(new_lines)):
            changes['new_line_status'][i] = 'unchanged'
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are identical - already marked as unchanged
                continue
            elif tag == 'replace':
                # Lines were changed
                for i in range(i1, i2):
                    changes['old_line_status'][i] = 'changed'
                for j in range(j1, j2):
                    changes['new_line_status'][j] = 'changed'
                # Create mappings for changed lines
                for idx, (i, j) in enumerate(zip(range(i1, i2), range(j1, j2))):
                    changes['line_mappings'][i] = j
            elif tag == 'delete':
                # Lines were removed from old
                for i in range(i1, i2):
                    changes['old_line_status'][i] = 'removed'
            elif tag == 'insert':
                # Lines were added to new
                for j in range(j1, j2):
                    changes['new_line_status'][j] = 'added'
        
        return changes
    
    def _get_annotation_markers(self) -> Dict[str, str]:
        """Get annotation markers based on style"""
        if self.annotation_style == "comment":
            return {
                'changed': '# [CHANGED] ',
                'removed': '# [REMOVED] ',
                'added': '# [ADDED] '
            }
        elif self.annotation_style == "inline":
            return {
                'changed': '>>> [CHANGED] ',
                'removed': '>>> [REMOVED] ',
                'added': '>>> [ADDED] '
            }
        elif self.annotation_style == "html":
            return {
                'changed': '<span class="changed-line">',
                'removed': '<span class="removed-line">',
                'added': '<span class="added-line">'
            }
        else:
            # Default to comment style
            return {
                'changed': '# [CHANGED] ',
                'removed': '# [REMOVED] ',
                'added': '# [ADDED] '
            }
    
    def create_annotated_old_file(self) -> str:
        """Create annotated version of old file showing changes and removals"""
        if not self.old_content:
            return ""
        
        old_lines = self.old_content.splitlines()
        annotated_lines = []
        markers = self._get_annotation_markers()
        
        for i, line in enumerate(old_lines):
            status = self.diff_info['old_line_status'].get(i, 'unchanged')
            
            # Escape HTML entities if using HTML style
            if self.annotation_style == "html":
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if status == 'changed':
                if self.annotation_style == "html":
                    annotated_lines.append(f'<span class="changed-line">{line}</span>')
                else:
                    annotated_lines.append(f'{markers["changed"]}{line}')
            elif status == 'removed':
                if self.annotation_style == "html":
                    annotated_lines.append(f'<span class="removed-line">{line}</span>')
                else:
                    annotated_lines.append(f'{markers["removed"]}{line}')
            else:
                if self.annotation_style == "html":
                    annotated_lines.append(f'<span class="unchanged-line">{line}</span>')
                else:
                    annotated_lines.append(line)
        
        result = '\n'.join(annotated_lines)
        
        # Add HTML closing tags if needed
        if self.annotation_style == "html":
            result += '\n        </pre>\n    </div>\n</body>\n</html>'
        
        return result
    
    def create_annotated_new_file(self) -> str:
        """Create annotated version of new file showing additions and changes"""
        if not self.new_content:
            return ""
        
        new_lines = self.new_content.splitlines()
        annotated_lines = []
        markers = self._get_annotation_markers()
        
        for i, line in enumerate(new_lines):
            status = self.diff_info['new_line_status'].get(i, 'unchanged')
            
            # Escape HTML entities if using HTML style
            if self.annotation_style == "html":
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if status == 'added':
                if self.annotation_style == "html":
                    annotated_lines.append(f'<span class="added-line">{line}</span>')
                else:
                    annotated_lines.append(f'{markers["added"]}{line}')
            elif status == 'changed':
                if self.annotation_style == "html":
                    annotated_lines.append(f'<span class="changed-line">{line}</span>')
                else:
                    annotated_lines.append(f'{markers["changed"]}{line}')
            else:
                if self.annotation_style == "html":
                    annotated_lines.append(f'<span class="unchanged-line">{line}</span>')
                else:
                    annotated_lines.append(line)
        
        result = '\n'.join(annotated_lines)
        
        # Add HTML closing tags if needed
        if self.annotation_style == "html":
            result += '\n        </pre>\n    </div>\n</body>\n</html>'
        
        return result
    
    def get_change_summary(self) -> Dict[str, int]:
        """Get summary of changes"""
        summary = {
            'lines_added': 0,
            'lines_removed': 0,
            'lines_changed': 0,
            'lines_unchanged': 0
        }
        
        for status in self.diff_info['old_line_status'].values():
            if status == 'removed':
                summary['lines_removed'] += 1
            elif status == 'changed':
                summary['lines_changed'] += 1
            else:
                summary['lines_unchanged'] += 1
        
        for status in self.diff_info['new_line_status'].values():
            if status == 'added':
                summary['lines_added'] += 1
        
        return summary


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
    
    def get_commits_affecting_file(self, repo: str, base_ref: str, head_ref: str, file_path: str) -> List[Dict]:
        """Get commits between two refs that affected a specific file"""
        url = f"https://api.github.com/repos/{repo}/commits"
        params = {
            'sha': head_ref,
            'path': file_path,
            'per_page': 100  # Get more commits to ensure we capture all relevant ones
        }
        
        response = self._make_request(url, params)
        all_commits = response.json()
        
        # Get the base commit to determine the cutoff point
        try:
            base_commit_response = self._make_request(f"https://api.github.com/repos/{repo}/commits/{base_ref}")
            base_commit_date = base_commit_response.json()['commit']['committer']['date']
        except:
            # If we can't get base commit, return all commits (fallback)
            return all_commits
        
        # Filter commits to only include those after the base commit
        relevant_commits = []
        for commit in all_commits:
            commit_date = commit['commit']['committer']['date']
            if commit_date > base_commit_date:
                relevant_commits.append(commit)
            else:
                # Once we reach the base commit date, we can stop
                break
        
        return relevant_commits
    
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
    
    def __init__(self, output_dir: Path, annotation_style: str = "comment"):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.annotation_style = annotation_style
    
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
    
    def generate_unified_diff(self, old_def: Optional[FunctionInfo], 
                            new_def: Optional[FunctionInfo], name: str, 
                            filename: str) -> str:
        """Generate unified diff for function/class changes"""
        old_code = old_def.source_code if old_def else ""
        new_code = new_def.source_code if new_def else ""
        
        # Split into lines for difflib
        old_lines = old_code.splitlines(keepends=True) if old_code else []
        new_lines = new_code.splitlines(keepends=True) if new_code else []
        
        # Generate unified diff
        node_type = (new_def or old_def).node_type
        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{filename} (old) - {node_type}: {name}",
            tofile=f"{filename} (new) - {node_type}: {name}",
            lineterm=""
        )
        
        return '\n'.join(diff_lines)
    
    def save_diff_files(self, file_change: FileChange, function_changes: Dict[str, Tuple[Optional[FunctionInfo], Optional[FunctionInfo]]], 
                       output_subdir: str, commits_info: Optional[List[Dict]] = None) -> List[str]:
        """Save individual diff files for each changed function/class"""
        repo_name = file_change.repo.replace('/', '_')
        file_base = Path(file_change.filename).stem
        
        output_path = self.output_dir / output_subdir / repo_name / "diffs"
        output_path.mkdir(parents=True, exist_ok=True)
        
        diff_files = []
        
        for name, (old_def, new_def) in function_changes.items():
            # Generate diff content
            diff_content = self.generate_unified_diff(old_def, new_def, name, file_change.filename)
            
            # Skip empty diffs (shouldn't happen, but just in case)
            if not diff_content.strip():
                continue
            
            # Create filename for this diff
            node_type = (new_def or old_def).node_type
            safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
            diff_filename = f"{file_base}_{node_type}_{safe_name}.diff"
            diff_path = output_path / diff_filename
            
            # Write diff file
            with open(diff_path, 'w', encoding='utf-8') as f:
                # Write header with basic info
                f.write(f"# Diff for {node_type}: {name}\n")
                f.write(f"# File: {file_change.filename}\n")
                f.write(f"# Repository: {file_change.repo}\n")
                f.write(f"# Status: {file_change.status}\n")
                if old_def:
                    f.write(f"# Old SHA: {file_change.old_sha}\n")
                if new_def:
                    f.write(f"# New SHA: {file_change.new_sha}\n")
                f.write("#" + "="*60 + "\n")
                
                # Add commit information if available
                if commits_info:
                    f.write("#\n")
                    f.write("# RELATED COMMITS:\n")
                    f.write("#" + "-"*40 + "\n")
                    for commit in commits_info:
                        commit_info = commit['commit']
                        author = commit_info['author']
                        committer = commit_info['committer']
                        
                        f.write(f"# Commit: {commit['sha'][:8]}\n")
                        f.write(f"# Date: {committer['date']}\n")
                        f.write(f"# Author: {author['name']} <{author['email']}>\n")
                        if committer['name'] != author['name']:
                            f.write(f"# Committer: {committer['name']} <{committer['email']}>\n")
                        
                        # Clean up commit message (remove extra whitespace, limit length)
                        message = commit_info['message'].strip()
                        # Split into lines and add # prefix to each line
                        message_lines = message.split('\n')
                        f.write(f"# Message: {message_lines[0]}\n")
                        # Add additional lines if they exist (for multi-line commit messages)
                        for line in message_lines[1:]:
                            if line.strip():  # Skip empty lines
                                f.write(f"#          {line.strip()}\n")
                        f.write("#\n")
                    f.write("#" + "="*60 + "\n")
                
                f.write("\n")
                f.write(diff_content)
            
            diff_files.append(str(diff_path))
        
        return diff_files
    
    def save_file_versions(self, file_change: FileChange, output_subdir: str, 
                          save_annotated: bool = True) -> Dict[str, Optional[str]]:
        """Save old and new versions of a file to disk, including annotated versions"""
        repo_name = file_change.repo.replace('/', '_')
        file_base = Path(file_change.filename).stem
        file_ext = Path(file_change.filename).suffix
        
        output_path = self.output_dir / output_subdir / repo_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        result = {
            'old': None,
            'new': None,
            'old_annotated': None,
            'new_annotated': None
        }
        
        # Save original files
        if file_change.old_content:
            old_file_path = output_path / f"{file_base}_old{file_ext}"
            with open(old_file_path, 'w', encoding='utf-8') as f:
                f.write(file_change.old_content)
            result['old'] = str(old_file_path)
        
        if file_change.new_content:
            new_file_path = output_path / f"{file_base}_new{file_ext}"
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(file_change.new_content)
            result['new'] = str(new_file_path)
        
        # Save annotated files if requested
        if save_annotated and (file_change.old_content or file_change.new_content):
            annotator = DiffAnnotator(
                file_change.old_content, 
                file_change.new_content, 
                self.annotation_style
            )
            
            # Get change summary for informative file headers
            change_summary = annotator.get_change_summary()
            
            # Save annotated old file
            if file_change.old_content:
                annotated_old_content = annotator.create_annotated_old_file()
                if annotated_old_content:
                    # Add header with change summary
                    header = self._create_annotation_header(file_change, change_summary, "old")
                    annotated_old_content = header + annotated_old_content
                    
                    # Use appropriate file extension
                    ext = ".html" if self.annotation_style == "html" else file_ext
                    old_annotated_path = output_path / f"{file_base}_old_diff{ext}"
                    with open(old_annotated_path, 'w', encoding='utf-8') as f:
                        f.write(annotated_old_content)
                    result['old_annotated'] = str(old_annotated_path)
            
            # Save annotated new file
            if file_change.new_content:
                annotated_new_content = annotator.create_annotated_new_file()
                if annotated_new_content:
                    # Add header with change summary
                    header = self._create_annotation_header(file_change, change_summary, "new")
                    annotated_new_content = header + annotated_new_content
                    
                    # Use appropriate file extension
                    ext = ".html" if self.annotation_style == "html" else file_ext
                    new_annotated_path = output_path / f"{file_base}_new_diff{ext}"
                    with open(new_annotated_path, 'w', encoding='utf-8') as f:
                        f.write(annotated_new_content)
                    result['new_annotated'] = str(new_annotated_path)
        
        return result
    
    def _create_annotation_header(self, file_change: FileChange, change_summary: Dict[str, int], 
                                 file_type: str) -> str:
        """Create informative header for annotated files"""
        if self.annotation_style == "html":
            # Get the CSS file path
            css_path = Path(__file__).parent / "diff_styles.css"
            css_content = ""
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
            except FileNotFoundError:
                pass  # Use inline styles if CSS file not found
            
            header = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Annotated {file_type.upper()} - {file_change.filename}</title>
    <style>
{css_content}
    </style>
</head>
<body>
    <div class="file-header">
        <h2>ANNOTATED {file_type.upper()} VERSION - {file_change.filename}</h2>
        <p><strong>Repository:</strong> {file_change.repo}</p>
        <p><strong>Status:</strong> {file_change.status}</p>
"""
        else:
            header = f"""# 
# ANNOTATED {file_type.upper()} VERSION - {file_change.filename}
# Repository: {file_change.repo}
# Status: {file_change.status}
"""
        
        if file_type == "old":
            if self.annotation_style == "html":
                header += f"""        <p><strong>Old SHA:</strong> {file_change.old_sha}</p>
    </div>
    
    <div class="legend">
        <h3>Legend:</h3>
        <div class="legend-item legend-changed">[CHANGED] Modified in new version</div>
        <div class="legend-item legend-removed">[REMOVED] Deleted in new version</div>
        <div>Lines without markers: Unchanged</div>
        
        <h4>Change Summary:</h4>
        <ul>
            <li>Lines changed: {change_summary['lines_changed']}</li>
            <li>Lines removed: {change_summary['lines_removed']}</li>
            <li>Lines unchanged: {change_summary['lines_unchanged']}</li>
        </ul>
    </div>
    
    <div class="code-content">
        <pre>"""
            else:
                header += f"""# Old SHA: {file_change.old_sha}
# Lines marked [CHANGED]: Modified in new version
# Lines marked [REMOVED]: Deleted in new version
# Lines without markers: Unchanged
#
# Change Summary:
# - Lines changed: {change_summary['lines_changed']}
# - Lines removed: {change_summary['lines_removed']}
# - Lines unchanged: {change_summary['lines_unchanged']}
#
# ============================================================================

"""
        else:  # new
            if self.annotation_style == "html":
                header += f"""        <p><strong>New SHA:</strong> {file_change.new_sha}</p>
    </div>
    
    <div class="legend">
        <h3>Legend:</h3>
        <div class="legend-item legend-added">[ADDED] New in this version</div>
        <div class="legend-item legend-changed">[CHANGED] Modified from old version</div>
        <div>Lines without markers: Unchanged</div>
        
        <h4>Change Summary:</h4>
        <ul>
            <li>Lines added: {change_summary['lines_added']}</li>
            <li>Lines changed: {change_summary['lines_changed']}</li>
            <li>Lines unchanged: {change_summary['lines_unchanged']}</li>
        </ul>
    </div>
    
    <div class="code-content">
        <pre>"""
            else:
                header += f"""# New SHA: {file_change.new_sha}
# Lines marked [ADDED]: New in this version
# Lines marked [CHANGED]: Modified from old version
# Lines without markers: Unchanged
#
# Change Summary:
# - Lines added: {change_summary['lines_added']}
# - Lines changed: {change_summary['lines_changed']}
# - Lines unchanged: {change_summary['lines_unchanged']}
#
# ============================================================================

"""
        
        return header
    
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
    
    def __init__(self, token: Optional[str] = None, output_dir: str = "github_analysis_output", 
                 annotation_style: str = "comment"):
        # If no token provided, try to get from environment
        if token is None:
            token = os.getenv('GITHUB_TOKEN')
        
        self.github_analyzer = GitHubAnalyzer(token, output_dir)
        self.report_generator = ReportGenerator(Path(output_dir), annotation_style)
        self.output_dir = Path(output_dir)
        self.annotation_style = annotation_style
    
    def analyze_repositories(self, repos: List[str], base_ref: str = "HEAD~1", 
                           head_ref: str = "HEAD", save_files: bool = True, save_diffs: bool = True,
                           save_annotated: bool = True) -> List[AnalysisResult]:
        """Analyze multiple repositories and generate comprehensive reports"""
        all_results = []
        
        for repo in repos:
            try:
                result = self.github_analyzer.analyze_repository(repo, base_ref, head_ref)
                all_results.append(result)
                
                # Save individual file versions and diffs if requested
                if save_files:
                    for file_change in result.file_changes:
                        # Save old and new file versions (including annotated versions)
                        file_paths = self.report_generator.save_file_versions(
                            file_change, f"file_versions_{base_ref}_{head_ref}", save_annotated
                        )
                        
                        if file_paths['old']:
                            print(f"  Saved old version: {file_paths['old']}")
                        if file_paths['new']:
                            print(f"  Saved new version: {file_paths['new']}")
                        if file_paths['old_annotated']:
                            print(f"  Saved annotated old version: {file_paths['old_annotated']}")
                        if file_paths['new_annotated']:
                            print(f"  Saved annotated new version: {file_paths['new_annotated']}")
                        
                        # Save diff files for function/class changes
                        if save_diffs and file_change.filename in result.function_changes:
                            commits_info = self.github_analyzer.get_commits_affecting_file(repo, base_ref, head_ref, file_change.filename)
                            diff_files = self.report_generator.save_diff_files(
                                file_change, 
                                result.function_changes[file_change.filename],
                                f"file_versions_{base_ref}_{head_ref}",
                                commits_info
                            )
                            for diff_file in diff_files:
                                print(f"  Saved diff: {diff_file}")
                
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