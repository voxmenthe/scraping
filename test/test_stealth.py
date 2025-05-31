#!/usr/bin/env python3
"""
Test script specifically for testing stealth mode and bot protection bypass.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraping import DynamicWebScraper


def test_stealth_mode():
    """Test stealth mode against various protection systems."""
    
    # Test URLs that commonly have bot protection
    test_sites = [
        {
            'url': 'https://www.hims.com',
            'description': 'HIMS (likely has Cloudflare protection)',
            'expected_protection': 'cloudflare'
        },
        {
            'url': 'https://httpbin.org/user-agent',
            'description': 'HTTPBin User Agent (tests user agent spoofing)',
            'expected_protection': None
        },
        {
            'url': 'https://whatismyipaddress.com/',
            'description': 'IP detection site (tests headers)',
            'expected_protection': None
        }
    ]
    
    print("🧪 STEALTH MODE TESTING")
    print("=" * 50)
    
    for test_case in test_sites:
        url = test_case['url']
        description = test_case['description']
        
        print(f"\n🎯 Testing: {description}")
        print(f"URL: {url}")
        print("-" * 30)
        
        # Test without stealth mode first
        print("1️⃣ Testing WITHOUT stealth mode...")
        scraper_normal = DynamicWebScraper(
            headless=True, 
            stealth_mode=False,
            timeout=20000
        )
        
        try:
            results_normal = scraper_normal.comprehensive_scrape(url, max_retries=1)
            
            if 'error' in results_normal:
                print(f"❌ Normal mode failed: {results_normal['error']}")
                normal_success = False
            else:
                print("✅ Normal mode succeeded")
                protection = results_normal.get('final_structure', {}).get('protection_detected')
                if protection:
                    print(f"⚠️ Protection detected: {protection}")
                normal_success = True
                
        except Exception as e:
            print(f"❌ Normal mode error: {e}")
            normal_success = False
        
        # Test with stealth mode
        print("\n2️⃣ Testing WITH stealth mode...")
        scraper_stealth = DynamicWebScraper(
            headless=True, 
            stealth_mode=True,
            timeout=30000
        )
        
        try:
            results_stealth = scraper_stealth.comprehensive_scrape(url, max_retries=3)
            
            if 'error' in results_stealth:
                print(f"❌ Stealth mode failed: {results_stealth['error']}")
                stealth_success = False
            else:
                print("✅ Stealth mode succeeded")
                protection = results_stealth.get('final_structure', {}).get('protection_detected')
                if protection:
                    print(f"⚠️ Protection detected but bypassed: {protection}")
                else:
                    print("🎉 No protection detected")
                
                # Show some stats
                raw_info = results_stealth.get('final_structure', {}).get('raw_page_info', {})
                if raw_info and 'error' not in raw_info:
                    print(f"📊 Page stats: {raw_info.get('element_count', 0)} elements, "
                          f"{raw_info.get('body_text_length', 0)} chars")
                
                attempts = results_stealth.get('attempts_made', 1)
                print(f"🔄 Completed in {attempts} attempt(s)")
                
                stealth_success = True
                
        except Exception as e:
            print(f"❌ Stealth mode error: {e}")
            stealth_success = False
        
        # Summary
        print(f"\n📋 Summary for {description}:")
        print(f"   Normal mode: {'✅ Success' if normal_success else '❌ Failed'}")
        print(f"   Stealth mode: {'✅ Success' if stealth_success else '❌ Failed'}")
        
        if stealth_success and not normal_success:
            print("   🎯 Stealth mode provided improvement!")
        elif stealth_success and normal_success:
            print("   ✨ Both modes worked")
        elif not stealth_success and not normal_success:
            print("   ⚠️ Site may have strong protection")
        
        print("\n" + "="*50)


def test_single_site_stealth(url: str):
    """Test a single site with detailed stealth analysis."""
    
    print(f"🔍 DETAILED STEALTH ANALYSIS")
    print(f"Target: {url}")
    print("=" * 50)
    
    scraper = DynamicWebScraper(
        headless=False,  # Show browser for debugging
        stealth_mode=True,
        timeout=30000
    )
    
    try:
        print("🚀 Starting stealth analysis...")
        results = scraper.comprehensive_scrape(url, max_retries=3)
        
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            return False
        
        # Save detailed results
        output_file = f"stealth_analysis_{url.replace('https://', '').replace('/', '_')}.txt"
        scraper.spec_generator.save_spec_as_text(
            results['scraping_specification'], 
            output_file, 
            structure=results.get('final_structure')
        )
        
        print(f"✅ Analysis complete! Saved to: {output_file}")
        
        # Show key information
        protection = results.get('final_structure', {}).get('protection_detected')
        if protection:
            print(f"⚠️ Protection detected: {protection}")
        
        attempts = results.get('attempts_made', 1)
        print(f"🔄 Completed in {attempts} attempt(s)")
        
        raw_info = results.get('final_structure', {}).get('raw_page_info', {})
        if raw_info and 'error' not in raw_info:
            print(f"📊 Final stats:")
            print(f"   Elements: {raw_info.get('element_count', 0)}")
            print(f"   Text length: {raw_info.get('body_text_length', 0)} chars")
            print(f"   Links: {raw_info.get('link_count', 0)}")
            print(f"   Forms: {raw_info.get('form_count', 0)}")
            print(f"   Scripts: {raw_info.get('script_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific URL
        url = sys.argv[1]
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        test_single_site_stealth(url)
    else:
        # Run comprehensive stealth tests
        test_stealth_mode() 