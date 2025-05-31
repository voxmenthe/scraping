# Partial Diff View Feature Guide

## Overview

The GitHub Repository Change Analyzer now includes a powerful **Partial Diff View** feature that makes it much easier to spot changes in Python files at a glance. Instead of comparing raw old and new files, you now get annotated versions that highlight exactly what changed, what was added, and what was removed.

## What Problem Does This Solve?

Previously, when analyzing repository changes, you would get:
- `filename_old.py` - The original file
- `filename_new.py` - The modified file  
- `filename_function_diff.diff` - Traditional diff files (only for detected function/class changes)

**The problem:** It was hard to quickly scan files and spot changes, especially for files with many lines or subtle modifications.

**The solution:** Annotated diff files that preserve the original code structure while clearly marking what changed.

## New File Types Generated

For each changed Python file, you now get:

### Original Files (unchanged)
- `filename_old.py` - Original version
- `filename_new.py` - New version

### New Annotated Files
- `filename_old_diff.py` - Annotated old version showing what will change/be removed
- `filename_new_diff.py` - Annotated new version showing what was added/changed
- `filename_old_diff.html` - HTML version with visual styling (if using HTML style)
- `filename_new_diff.html` - HTML version with visual styling (if using HTML style)

## Annotation Styles

### 1. Comment Style (Default)
```python
# [CHANGED] def calculate_sum(a, b, c=0):  # Added parameter
# [ADDED] import math  # New import
# [REMOVED] def old_function():  # This will be deleted
    unchanged_code_here
```

### 2. Inline Style
```python
>>> [CHANGED] def calculate_sum(a, b, c=0):  # Added parameter
>>> [ADDED] import math  # New import
>>> [REMOVED] def old_function():  # This will be deleted
    unchanged_code_here
```

### 3. HTML Style
Generates beautiful HTML files with:
- Color-coded highlighting
- Visual legends
- Change summaries
- Professional styling
- Easy browser viewing

## How to Use

### Command Line Interface

```bash
# Basic usage (comment style by default)
python -m scraping.github_cli owner/repo

# Use different annotation styles
python -m scraping.github_cli owner/repo --annotation-style=inline
python -m scraping.github_cli owner/repo --annotation-style=html

# Disable annotated files if you don't want them
python -m scraping.github_cli owner/repo --no-annotate-diffs

# Combine with other options
python -m scraping.github_cli owner/repo --base HEAD~5 --annotation-style=html
```

### Programmatic Usage

```python
from scraping.github_analyzer import GitHubChangeTracker

# Initialize with annotation style
tracker = GitHubChangeTracker(
    token="your_github_token",
    output_dir="analysis_output",
    annotation_style="html"  # or "comment", "inline"
)

# Analyze repositories with annotations
results = tracker.analyze_repositories(
    repos=["owner/repo1", "owner/repo2"],
    base_ref="HEAD~1",
    head_ref="HEAD",
    save_files=True,
    save_diffs=True,
    save_annotated=True  # Enable annotated files
)
```

### Direct DiffAnnotator Usage

```python
from scraping.github_analyzer import DiffAnnotator

# Create annotator
annotator = DiffAnnotator(old_content, new_content, "comment")

# Get annotated versions
annotated_old = annotator.create_annotated_old_file()
annotated_new = annotator.create_annotated_new_file()

# Get change summary
summary = annotator.get_change_summary()
print(f"Lines added: {summary['lines_added']}")
print(f"Lines changed: {summary['lines_changed']}")
print(f"Lines removed: {summary['lines_removed']}")
```

## Understanding the Annotations

### In Old Files (`*_old_diff.*`)
- **`[CHANGED]`** - This line will be modified in the new version
- **`[REMOVED]`** - This line will be deleted in the new version
- **No marker** - This line remains unchanged

### In New Files (`*_new_diff.*`)
- **`[ADDED]`** - This line is new in this version
- **`[CHANGED]`** - This line was modified from the old version  
- **No marker** - This line was unchanged from the old version

## File Headers

Each annotated file includes a helpful header with:
- File information (name, repository, status)
- SHA hashes for old/new versions
- Change summary statistics
- Legend explaining the markers

### Example Header (Comment Style)
```python
# 
# ANNOTATED OLD VERSION - calculator.py
# Repository: demo/example
# Status: modified
# Old SHA: abc123
# Lines marked [CHANGED]: Modified in new version
# Lines marked [REMOVED]: Deleted in new version
# Lines without markers: Unchanged
#
# Change Summary:
# - Lines changed: 11
# - Lines removed: 0
# - Lines unchanged: 27
#
# ============================================================================
```

## HTML Output Features

When using `--annotation-style=html`, you get:
- **Professional styling** with color-coded changes
- **Visual legend** showing what each color means
- **Change statistics** prominently displayed
- **Monospace font** for proper code formatting
- **Responsive design** that works on any screen size

### HTML Color Scheme
- 🟡 **Yellow background** - Changed lines
- 🟢 **Green background** - Added lines  
- 🔴 **Red background** - Removed lines (with strikethrough)
- ⚪ **White background** - Unchanged lines

## Output Directory Structure

```
github_analysis_output/
├── file_versions_HEAD~1_HEAD/
│   └── owner_repo/
│       ├── module_old.py                    # Original old file
│       ├── module_new.py                    # Original new file
│       ├── module_old_diff.py               # Annotated old file
│       ├── module_new_diff.py               # Annotated new file
│       ├── module_old_diff.html             # HTML old file (if HTML style)
│       ├── module_new_diff.html             # HTML new file (if HTML style)
│       └── diffs/
│           └── module_function_name.diff    # Traditional function diffs
└── github_changes_comprehensive_report.txt  # Summary report
```

## Benefits

1. **Quick Visual Scanning** - Immediately see what changed without comparing files side-by-side
2. **Context Preservation** - See changes in their original code context
3. **Multiple Formats** - Choose the format that works best for your workflow
4. **Detailed Statistics** - Get quantified change summaries
5. **Professional Output** - HTML files perfect for sharing or documentation
6. **Backward Compatible** - Original files and diff files still generated

## Tips for Best Results

1. **Use HTML style for sharing** - Great for code reviews or documentation
2. **Use comment style for development** - Preserves Python syntax for easy reading
3. **Use inline style for quick scanning** - Markers stand out more prominently
4. **Combine with function diffs** - Get both file-level and function-level change views
5. **Check change summaries** - Quickly assess the scope of modifications

## Example Workflow

1. **Analyze changes:**
   ```bash
   python -m scraping.github_cli myorg/myrepo --annotation-style=html
   ```

2. **Review annotated files:**
   - Open `*_old_diff.html` to see what's changing/being removed
   - Open `*_new_diff.html` to see what's being added/changed

3. **Share results:**
   - Send HTML files to team members for review
   - Use in documentation or change logs
   - Archive for future reference

## Troubleshooting

**Q: Annotated files not being generated?**
A: Make sure you're not using `--no-annotate-diffs` flag

**Q: HTML files look unstyled?**
A: Ensure `src/scraping/diff_styles.css` exists and is readable

**Q: Too many lines marked as changed?**
A: This is normal for files with significant restructuring - the diff algorithm detects line-level changes

**Q: Want to disable annotations temporarily?**
A: Use `--no-annotate-diffs` flag to skip annotation generation

---

The Partial Diff View feature makes code change analysis much more intuitive and efficient. Whether you're doing code reviews, tracking project evolution, or documenting changes, these annotated files provide the perfect balance of detail and readability. 