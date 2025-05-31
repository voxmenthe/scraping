#!/usr/bin/env python3
"""
Debug script specifically for testing HIMS with detailed logging.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraping import DynamicWebScraper


def debug_hims():
    """Debug HIMS specifically with detailed logging."""
    
    url = "https://www.hims.com"
    
    print("🔍 HIMS DEBUG ANALYSIS")
    print("=" * 50)
    print(f"Target: {url}")
    print("Strategy: Step-by-step with flexible timeouts")
    print("=" * 50)
    
    # Use non-headless mode for debugging
    scraper = DynamicWebScraper(
        headless=False,  # Show browser
        stealth_mode=True,
        timeout=45000    # Longer timeout
    )
    
    try:
        print("🚀 Starting debug analysis...")
        results = scraper.comprehensive_scrape(
            url, 
            max_retries=1,  # Single attempt for debugging
            monitor_content=False,  # Skip monitoring for now
            interact_with_elements=False  # Skip interactions for now
        )
        
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            
            # Try to get partial results
            if 'partial_results' in results:
                print("🔍 Checking partial results...")
                partial = results['partial_results']
                if partial:
                    print(f"Partial data available: {list(partial.keys())}")
            
            return False
        
        print("✅ Analysis succeeded!")
        
        # Save results
        output_file = "hims_debug_analysis.txt"
        scraper.spec_generator.save_spec_as_text(
            results['scraping_specification'], 
            output_file, 
            structure=results.get('final_structure')
        )
        
        print(f"📄 Analysis saved to: {output_file}")
        
        # Show key findings
        final_structure = results.get('final_structure', {})
        protection = final_structure.get('protection_detected')
        wait_strategy = final_structure.get('wait_strategy_used')
        
        print(f"\n📊 KEY FINDINGS:")
        print(f"   Protection detected: {protection or 'None'}")
        print(f"   Wait strategy used: {wait_strategy}")
        print(f"   Attempts made: {results.get('attempts_made', 1)}")
        print(f"   Stealth mode: {results.get('stealth_mode_used', False)}")
        
        raw_info = final_structure.get('raw_page_info', {})
        if raw_info and 'error' not in raw_info:
            print(f"\n📈 PAGE STATS:")
            print(f"   Title: {raw_info.get('title', 'Unknown')}")
            print(f"   Elements: {raw_info.get('element_count', 0)}")
            print(f"   Text length: {raw_info.get('body_text_length', 0)} chars")
            print(f"   Links: {raw_info.get('link_count', 0)}")
            print(f"   Scripts: {raw_info.get('script_count', 0)}")
            print(f"   Forms: {raw_info.get('form_count', 0)}")
            
            first_chars = raw_info.get('first_200_chars', '')
            if first_chars:
                print(f"\n📝 FIRST 200 CHARACTERS:")
                print(f'"{first_chars}"')
        
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False


def quick_hims_check():
    """Quick check of HIMS with minimal processing."""
    
    url = "https://www.hims.com"
    
    print("⚡ QUICK HIMS CHECK")
    print("=" * 30)
    
    scraper = DynamicWebScraper(
        headless=True,  # Headless for speed
        stealth_mode=True,
        timeout=20000
    )
    
    try:
        results = scraper.quick_scrape(url)
        
        if 'error' in results:
            print(f"❌ Quick check failed: {results['error']}")
            return False
        
        print("✅ Quick check succeeded!")
        
        structure = results.get('structure', {})
        print(f"Title: {structure.get('title', 'Unknown')}")
        print(f"Interactive elements: {len(structure.get('interactive_elements', []))}")
        print(f"Content areas: {len(structure.get('content_patterns', {}).get('contentAreas', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick check error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        quick_hims_check()
    else:
        debug_hims() 