#!/usr/bin/env python3
"""
Command-line interface for the dynamic web scraping toolkit.
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

from .scraper import DynamicWebScraper


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dynamic Web Scraping Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze a website and save specification to file
    python -m scraping.cli https://example.com
    
    # Specify custom output file
    python -m scraping.cli https://example.com --output my_analysis.txt
    
    # Quick analysis mode (faster, less comprehensive)
    python -m scraping.cli https://example.com --quick
    
    # Run in headed mode (show browser window)
    python -m scraping.cli https://example.com --headed
    
    # Analyze multiple URLs
    python -m scraping.cli https://site1.com https://site2.com --batch
        """
    )
    
    parser.add_argument(
        "url",
        nargs="+",
        help="URL(s) to analyze"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: auto-generated based on URL and timestamp)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="scraping_analysis",
        help="Output directory for analysis files (default: scraping_analysis)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Perform quick analysis (faster but less comprehensive)"
    )
    
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (show browser window)"
    )
    
    parser.add_argument(
        "--no-interactions",
        action="store_true",
        help="Skip interaction with expandable elements"
    )
    
    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        help="Skip content change monitoring"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode for multiple URLs"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format instead of text"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Browser timeout in milliseconds (default: 30000)"
    )
    
    parser.add_argument(
        "--stealth",
        action="store_true",
        default=True,
        help="Enable stealth mode to bypass bot protection (default: enabled)"
    )
    
    parser.add_argument(
        "--no-stealth",
        action="store_true",
        help="Disable stealth mode"
    )
    
    parser.add_argument(
        "--proxy",
        help="Use proxy server (format: http://proxy:port or socks5://proxy:port)"
    )
    
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts for bot protection (default: 3)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate URLs
    urls = args.url
    if not urls:
        print("Error: At least one URL is required")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Determine stealth mode
    stealth_mode = args.stealth and not args.no_stealth
    
    # Initialize scraper
    scraper = DynamicWebScraper(
        headless=not args.headed,
        timeout=args.timeout,
        stealth_mode=stealth_mode,
        use_proxy=args.proxy
    )
    
    if args.verbose:
        print(f"Initialized scraper with headless={not args.headed}, timeout={args.timeout}ms")
        print(f"Stealth mode: {'enabled' if stealth_mode else 'disabled'}")
        if args.proxy:
            print(f"Using proxy: {args.proxy}")
        print(f"Max retries: {args.retries}")
    
    try:
        if len(urls) == 1 and not args.batch:
            # Single URL analysis
            url = urls[0]
            print(f"🔍 Analyzing: {url}")
            
            if args.quick:
                results = scraper.quick_scrape(url)
                spec_key = 'basic_specification'
            else:
                results = scraper.comprehensive_scrape(
                    url,
                    monitor_content=not args.no_monitoring,
                    interact_with_elements=not args.no_interactions,
                    max_retries=args.retries
                )
                spec_key = 'scraping_specification'
            
            if 'error' in results:
                print(f"❌ Analysis failed: {results['error']}")
                sys.exit(1)
            
            # Generate output filename if not provided
            if args.output:
                output_file = Path(args.output)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
                extension = '.json' if args.json else '.txt'
                output_file = output_dir / f"{safe_url}_{timestamp}{extension}"
            
            # Save results
            if spec_key in results:
                if args.json:
                    scraper.spec_generator.save_spec_to_file(results[spec_key], str(output_file))
                else:
                    scraper.spec_generator.save_spec_as_text(results[spec_key], str(output_file))
                
                print(f"✅ Analysis complete! Specification saved to: {output_file}")
                
                # Print summary
                if args.verbose and 'summary' in results:
                    print_summary(results['summary'])
            else:
                print("❌ No specification generated")
                sys.exit(1)
        
        else:
            # Batch analysis
            print(f"🔍 Batch analyzing {len(urls)} URLs...")
            
            batch_results = scraper.batch_analyze(urls, str(output_dir))
            
            print(f"\n📊 Batch Analysis Complete!")
            print(f"Successfully analyzed: {batch_results['successful']}/{batch_results['total_urls']}")
            print(f"Failed: {batch_results['failed']}/{batch_results['total_urls']}")
            
            if batch_results['successful'] > 0:
                print(f"Specifications saved to: {output_dir}")
                
                # Save batch summary
                summary_file = output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                import json
                with open(summary_file, 'w') as f:
                    json.dump(batch_results, f, indent=2, default=str)
                print(f"Batch summary saved to: {summary_file}")
            
            if args.verbose:
                print_batch_summary(batch_results.get('summary', {}))
    
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_summary(summary: dict):
    """Print a formatted summary of the analysis."""
    print("\n📋 Analysis Summary:")
    print("-" * 40)
    
    page_info = summary.get('page_info', {})
    print(f"Page Title: {page_info.get('title', 'Unknown')}")
    
    structure = summary.get('structure_analysis', {})
    print(f"Total Interactive Elements: {structure.get('total_elements', 0)}")
    print(f"Expandable Elements: {structure.get('expandable_elements', 0)}")
    
    interactions = summary.get('interaction_summary', {})
    print(f"Interactions Attempted: {interactions.get('total_interactions', 0)}")
    print(f"Successful Interactions: {interactions.get('successful_interactions', 0)}")
    
    dynamic = summary.get('dynamic_behavior', {})
    if dynamic:
        print(f"Dynamic Activity Level: {dynamic.get('activity_level', 'Unknown')}")
        print(f"Mutations Detected: {dynamic.get('mutations_detected', 0)}")
    
    recommendations = summary.get('recommendations', [])
    if recommendations:
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")


def print_batch_summary(summary: dict):
    """Print a formatted summary of batch analysis."""
    if not summary or 'message' in summary:
        return
    
    print("\n📊 Batch Summary:")
    print("-" * 40)
    print(f"Success Rate: {summary.get('success_rate', 0):.1%}")
    print(f"Average Expandable Elements: {summary.get('average_expandable_elements', 0):.1f}")
    print(f"Average Interactions: {summary.get('average_interactions', 0):.1f}")
    
    layout_types = summary.get('common_layout_types', {})
    if layout_types:
        print("\nCommon Layout Types:")
        for layout_type, count in layout_types.items():
            print(f"  • {layout_type}: {count}")


if __name__ == "__main__":
    main() 