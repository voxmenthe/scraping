# GitHub Repository Change Analyzer

A comprehensive Python module for tracking and analyzing changes to Python files across GitHub repositories. This tool identifies modified functions and classes, providing detailed side-by-side comparisons and downloading old/new versions to output files.

## Features

- **GitHub API Integration**: Uses GitHub REST API to analyze repository changes
- **Python AST Analysis**: Parses Python files using Abstract Syntax Trees to identify functions and classes
- **Change Detection**: Identifies added, removed, and modified functions/classes
- **Side-by-Side Comparisons**: Generates comprehensive reports with old/new code comparisons
- **File Version Downloads**: Saves old and new versions of changed files to disk
- **Flexible Analysis**: Support for commit ranges, repository history, and custom comparisons
- **CLI Interface**: Easy-to-use command-line interface
- **Rate Limiting**: Built-in GitHub API rate limiting and error handling

## Installation

This module is part of the `scraping` package. Make sure you have the required dependencies:

```bash
pip install requests
```

## Setup

1. **Get a GitHub Token**: 
   - Go to https://github.com/settings/tokens
   - Generate a new token with appropriate permissions
   - Set it as an environment variable:

```bash
export GITHUB_TOKEN="your_token_here"
```

2. **Optional GitHub CLI** (for auto-discovery):
```bash
# Install GitHub CLI
brew install gh  # macOS
# or follow instructions at https://cli.github.com/

# Authenticate
gh auth login
```

## Usage

### Command Line Interface

```bash
# Analyze specific repositories
python -m scraping owner/repo1 owner/repo2

# Analyze with custom commit range
python -m scraping owner/repo --base HEAD~5 --head HEAD

# Auto-discover repositories using GitHub CLI
python -m scraping --auto-discover

# Analyze repository history (last 7 days)
python -m scraping owner/repo --history --days 7

# Custom output directory
python -m scraping owner/repo --output-dir my_analysis

# Don't save individual file versions
python -m scraping owner/repo --no-save-files

# Verbose output
python -m scraping owner/repo --verbose
```

### Programmatic Usage

```python
from scraping import GitHubChangeTracker

# Initialize tracker
tracker = GitHubChangeTracker(output_dir="analysis_output")

# Analyze repositories
results = tracker.analyze_repositories(
    repos=["owner/repo1", "owner/repo2"],
    base_ref="HEAD~3",
    head_ref="HEAD",
    save_files=True
)

# Process results
for result in results:
    print(f"Repository: {result.repo}")
    print(f"Files changed: {result.total_files_changed}")
    print(f"Functions/classes changed: {result.total_functions_changed}")
    
    # Examine specific changes
    for filename, changes in result.function_changes.items():
        for func_name, (old_def, new_def) in changes.items():
            if old_def is None:
                print(f"Added: {func_name}")
            elif new_def is None:
                print(f"Removed: {func_name}")
            else:
                print(f"Modified: {func_name}")
```

### Advanced Usage

```python
# Analyze repository history
results = tracker.analyze_repository_history("owner/repo", days_back=14)

# Custom commit analysis
result = tracker.github_analyzer.analyze_repository(
    repo="owner/repo",
    base_ref="commit_sha_1",
    head_ref="commit_sha_2"
)

# Filter results
for result in results:
    # Show only added functions
    for filename, changes in result.function_changes.items():
        added_functions = [
            (name, new_def) for name, (old_def, new_def) in changes.items()
            if old_def is None and new_def is not None
        ]
        
        for name, func_def in added_functions:
            print(f"Added {func_def.node_type}: {name}")
            if func_def.decorators:
                print(f"  Decorators: {func_def.decorators}")
```

## Output Structure

The analyzer creates the following output structure:

```
output_directory/
├── github_changes_comprehensive_report.txt     # Main analysis report
├── file_versions_HEAD~1_HEAD/                 # Saved file versions
│   └── owner_repo/
│       ├── module_old.py                      # Old version
│       └── module_new.py                      # New version
└── history_analysis_7days.txt                 # History analysis (if used)
```

## Data Structures

### FunctionInfo
```python
@dataclass
class FunctionInfo:
    name: str                    # Function/class name
    start_line: int             # Starting line number
    end_line: int               # Ending line number
    source_code: str            # Full source code
    node_type: str              # 'function', 'async_function', or 'class'
    decorators: List[str]       # List of decorators
    docstring: Optional[str]    # Docstring if present
```

### FileChange
```python
@dataclass
class FileChange:
    filename: str               # File path
    repo: str                   # Repository name
    old_content: str           # Old file content
    new_content: str           # New file content
    status: str                # 'added', 'modified', 'removed'
    old_sha: Optional[str]     # Old commit SHA
    new_sha: Optional[str]     # New commit SHA
```

### AnalysisResult
```python
@dataclass
class AnalysisResult:
    repo: str                           # Repository name
    file_changes: List[FileChange]      # All changed files
    function_changes: Dict[str, Dict]   # Function/class changes by file
    total_files_changed: int           # Total changed files count
    total_functions_changed: int       # Total changed functions count
```

## API Classes

### GitHubChangeTracker
Main interface for the analyzer.

```python
tracker = GitHubChangeTracker(token=None, output_dir="output")

# Analyze multiple repositories
results = tracker.analyze_repositories(repos, base_ref, head_ref, save_files=True)

# Analyze repository history
results = tracker.analyze_repository_history(repo, days_back=7)
```

### GitHubAnalyzer
Low-level GitHub API interface.

```python
analyzer = GitHubAnalyzer(token=None, output_dir="output")

# Get changed files
files = analyzer.get_changed_python_files(repo, base_ref, head_ref)

# Get file content
content, sha = analyzer.get_file_content(repo, path, ref)

# Get commits
commits = analyzer.get_commits_in_range(repo, since=None, until=None)
```

### PythonASTAnalyzer
Python AST parsing and analysis.

```python
# Extract functions and classes
definitions = PythonASTAnalyzer.extract_functions_and_classes(source_code)

# Find changes between versions
changes = PythonASTAnalyzer.find_changed_definitions(old_defs, new_defs)
```

### ReportGenerator
Generate comprehensive reports and save files.

```python
generator = ReportGenerator(output_dir)

# Generate side-by-side comparison
comparison = generator.generate_side_by_side_comparison(old_def, new_def, name)

# Save file versions
old_path, new_path = generator.save_file_versions(file_change, subdir)

# Generate comprehensive report
report_path = generator.generate_comprehensive_report(results, filename)
```

## Error Handling

The module includes comprehensive error handling:

- **GitHub API Errors**: Rate limiting, authentication, network issues
- **Python Syntax Errors**: Graceful handling of unparseable Python files
- **File Access Errors**: Missing files, permission issues
- **Network Errors**: Connection timeouts, DNS issues

## Rate Limiting

The module respects GitHub API rate limits:
- Maximum 5000 requests per hour for authenticated requests
- Built-in request counting and rate limit detection
- Graceful degradation when limits are reached

## Examples

See `github_example.py` for comprehensive usage examples including:
- Basic repository analysis
- History analysis
- Custom commit ranges
- Result filtering

## Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure `GITHUB_TOKEN` is set
2. **Rate Limit Exceeded**: Wait for rate limit reset or use a different token
3. **Repository Not Found**: Check repository name format (`owner/repo`)
4. **Empty Results**: Verify the commit range has actual changes

### Debug Mode

Use `--verbose` flag for detailed output:
```bash
python -m scraping owner/repo --verbose
```

## Contributing

When adding new features:
1. Follow the existing code structure
2. Add comprehensive error handling
3. Include type hints
4. Update this documentation
5. Add examples for new functionality

## License

This module is part of the scraping package. See the main package license for details. 