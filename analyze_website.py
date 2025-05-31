#!/usr/bin/env python3
"""
Standalone script for analyzing dynamic websites and generating scraping specifications.

Usage:
    python analyze_website.py <URL>
    python analyze_website.py <URL> --output <filename>
    python analyze_website.py <URL> --quick
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraping import DynamicWebScraper


def main():
    """Main function to analyze a website and generate scraping specification."""
    
    parser = argparse.ArgumentParser(
        description="Analyze a dynamic website and generate a comprehensive scraping specification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic analysis
    python analyze_website.py https://example.com
    
    # Save to specific file
    python analyze_website.py https://example.com --output my_spec.txt
    
    # Quick analysis (faster)
    python analyze_website.py https://example.com --quick
    
    # Show browser window
    python analyze_website.py https://example.com --headed
        """
    )
    
    parser.add_argument(
        "url",
        help="URL of the website to analyze"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: auto-generated based on URL and timestamp)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Perform quick analysis (faster but less comprehensive)"
    )
    
    parser.add_argument(
        "--headed",
        action="store_true", 
        help="Show browser window during analysis"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Save output as JSON instead of text"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress information"
    )
    
    args = parser.parse_args()
    
    # Validate URL
    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        if args.verbose:
            print(f"Added protocol: {url}")
    
    # Generate output filename if not provided
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
        extension = '.json' if args.json else '.txt'
        output_file = Path(f"website_analysis_{safe_url}_{timestamp}{extension}")
    
    print(f"🔍 Analyzing website: {url}")
    print(f"📄 Output will be saved to: {output_file}")
    
    # Initialize scraper
    scraper = DynamicWebScraper(
        headless=not args.headed,
        timeout=30000
    )
    
    try:
        # Perform analysis
        if args.quick:
            print("⚡ Running quick analysis...")
            results = scraper.quick_scrape(url)
            spec_key = 'basic_specification'
        else:
            print("🔬 Running comprehensive analysis...")
            results = scraper.comprehensive_scrape(url)
            spec_key = 'scraping_specification'
        
        # Check for errors
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            return 1
        
        # Save specification
        if spec_key in results:
            if args.json:
                scraper.spec_generator.save_spec_to_file(results[spec_key], str(output_file))
            else:
                scraper.spec_generator.save_spec_as_text(results[spec_key], str(output_file))
            
            print(f"✅ Analysis complete! Specification saved to: {output_file}")
            
            # Show summary if verbose
            if args.verbose and 'summary' in results:
                print_analysis_summary(results['summary'])
                
        else:
            print("❌ No specification was generated")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        return 130
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def print_analysis_summary(summary):
    """Print a formatted summary of the analysis results."""
    print("\n" + "="*50)
    print("📊 ANALYSIS SUMMARY")
    print("="*50)
    
    # Page information
    page_info = summary.get('page_info', {})
    print(f"🌐 URL: {page_info.get('url', 'Unknown')}")
    print(f"📰 Title: {page_info.get('title', 'Unknown')}")
    
    # Structure analysis
    structure = summary.get('structure_analysis', {})
    print(f"\n🏗️  STRUCTURE:")
    print(f"   • Total Interactive Elements: {structure.get('total_elements', 0)}")
    print(f"   • Expandable Elements: {structure.get('expandable_elements', 0)}")
    print(f"   • Static Content Areas: {structure.get('static_content_areas', 0)}")
    
    # Interaction summary
    interactions = summary.get('interaction_summary', {})
    if interactions.get('total_interactions', 0) > 0:
        print(f"\n🔄 INTERACTIONS:")
        print(f"   • Total Attempted: {interactions.get('total_interactions', 0)}")
        print(f"   • Successful: {interactions.get('successful_interactions', 0)}")
        print(f"   • Content Changes: {interactions.get('content_changes_detected', 0)}")
    
    # Dynamic behavior
    dynamic = summary.get('dynamic_behavior', {})
    if dynamic:
        print(f"\n⚡ DYNAMIC BEHAVIOR:")
        print(f"   • Activity Level: {dynamic.get('activity_level', 'Unknown')}")
        print(f"   • DOM Mutations: {dynamic.get('mutations_detected', 0)}")
        print(f"   • API Calls: {dynamic.get('api_calls_made', 0)}")
    
    # Recommendations
    recommendations = summary.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print("="*50)


if __name__ == "__main__":
    sys.exit(main()) 