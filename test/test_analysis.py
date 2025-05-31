#!/usr/bin/env python3
"""
Test script to demonstrate improved analysis output.
Try with different websites to see detailed element information.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraping import DynamicWebScraper


def test_analysis():
    """Test the analysis with different websites."""
    
    # Test URLs - try these to see different types of output
    test_urls = [
        "https://example.com",  # Simple static site
        "https://httpbin.org/html",  # Simple HTML for testing
        "https://quotes.toscrape.com",  # Scraping practice site
    ]
    
    scraper = DynamicWebScraper(headless=True)
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"TESTING: {url}")
        print(f"{'='*60}")
        
        try:
            # Quick analysis to start
            results = scraper.quick_scrape(url)
            
            if 'error' in results:
                print(f"❌ Failed: {results['error']}")
                continue
            
            # Show some basic info
            structure = results.get('structure', {})
            print(f"✅ Success!")
            print(f"Title: {structure.get('title', 'N/A')}")
            print(f"Interactive elements found: {len(structure.get('interactive_elements', []))}")
            print(f"Content areas: {len(structure.get('content_patterns', {}).get('contentAreas', []))}")
            
            # Show some detailed element info
            interactive = structure.get('interactive_elements', [])
            if interactive:
                print(f"\nFirst few interactive elements:")
                for i, elem in enumerate(interactive[:3], 1):
                    print(f"  {i}. {elem.get('tagName', 'unknown')} - {elem.get('text', 'no text')[:50]}...")
            
            # Save the analysis
            output_file = f"test_analysis_{url.replace('https://', '').replace('/', '_')}.txt"
            scraper.spec_generator.save_spec_as_text(results['basic_specification'], output_file)
            print(f"📄 Detailed analysis saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided URL
        url = sys.argv[1]
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        scraper = DynamicWebScraper(headless=True)
        print(f"🔍 Analyzing: {url}")
        
        try:
            results = scraper.comprehensive_scrape(url)
            
            if 'error' in results:
                print(f"❌ Failed: {results['error']}")
            else:
                output_file = f"detailed_analysis_{url.replace('https://', '').replace('/', '_')}.txt"
                scraper.spec_generator.save_spec_as_text(
                    results['scraping_specification'], 
                    output_file, 
                    structure=results.get('final_structure')
                )
                print(f"✅ Analysis complete! Check: {output_file}")
                
                # Show protection info if detected
                protection = results.get('final_structure', {}).get('protection_detected')
                if protection:
                    print(f"⚠️  Protection detected: {protection}")
                
                # Show raw page info
                raw_info = results.get('final_structure', {}).get('raw_page_info', {})
                if raw_info and 'error' not in raw_info:
                    print(f"📊 Page stats: {raw_info.get('element_count', 0)} elements, "
                          f"{raw_info.get('body_text_length', 0)} chars of text")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        test_analysis() 