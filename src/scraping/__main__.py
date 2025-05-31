#!/usr/bin/env python3
"""
Main entry point for the scraping package
"""

import sys
from . import github_cli

if __name__ == '__main__':
    # For now, default to the GitHub CLI
    # In the future, could add routing to different CLIs based on arguments
    github_cli.main() 