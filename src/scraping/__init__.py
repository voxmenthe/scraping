"""
Comprehensive web scraping toolkit for dynamic websites.

This package provides tools for scraping modern web applications with dynamic content,
including LLM chat interfaces and sites with expandable/collapsible content.
"""

from .scraper import DynamicWebScraper
from .structure_capture import PageStructureCapture
from .dynamic_content import DynamicContentHandler
from .content_monitor import ContentMonitor
from .spec_generator import ScrapingSpecGenerator
from .utils import ScrapingUtils
from .github_analyzer import (
    GitHubChangeTracker,
    GitHubAnalyzer,
    PythonASTAnalyzer,
    ReportGenerator,
    FunctionInfo,
    FileChange,
    AnalysisResult,
    get_repos_from_gh_cli
)

__version__ = "0.1.0"
__all__ = [
    "DynamicWebScraper",
    "PageStructureCapture", 
    "DynamicContentHandler",
    "ContentMonitor",
    "ScrapingSpecGenerator",
    "ScrapingUtils",
    "GitHubChangeTracker",
    "GitHubAnalyzer",
    "PythonASTAnalyzer",
    "ReportGenerator",
    "FunctionInfo",
    "FileChange",
    "AnalysisResult",
    "get_repos_from_gh_cli"
] 