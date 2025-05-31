"""
Main dynamic web scraper that orchestrates all components.
"""

import time
import random
from typing import Dict, List, Any, Optional
from playwright.sync_api import sync_playwright

from .structure_capture import PageStructureCapture
from .dynamic_content import DynamicContentHandler
from .content_monitor import ContentMonitor
from .spec_generator import ScrapingSpecGenerator
from .utils import ScrapingUtils


class DynamicWebScraper:
    """Main scraper class that orchestrates the comprehensive scraping process."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000, stealth_mode: bool = True, 
                 use_proxy: Optional[str] = None):
        self.headless = headless
        self.timeout = timeout
        self.stealth_mode = stealth_mode
        self.use_proxy = use_proxy
        
        # Initialize components
        self.structure_capture = PageStructureCapture()
        self.dynamic_handler = DynamicContentHandler()
        self.content_monitor = ContentMonitor()
        self.spec_generator = ScrapingSpecGenerator()
        self.utils = ScrapingUtils()
        
        self.results = {}
    
    def _create_browser_context(self, playwright):
        """Create a browser context with stealth configuration."""
        # Browser launch args for stealth
        launch_args = []
        if self.stealth_mode:
            launch_args.extend([
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--disable-browser-side-navigation',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps'
            ])
        
        # Proxy configuration
        proxy_config = None
        if self.use_proxy:
            proxy_config = {'server': self.use_proxy}
        
        # Launch browser
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
            proxy=proxy_config
        )
        
        # Create context
        context_options = {}
        if self.stealth_mode:
            context_options.update({
                'user_agent': self.utils.get_random_user_agent(),
                'java_script_enabled': True,
                'accept_downloads': False,
                'ignore_https_errors': True,
                'viewport': {
                    'width': random.choice([1920, 1366, 1536, 1440]),
                    'height': random.choice([1080, 768, 864, 900])
                }
            })
        
        context = browser.new_context(**context_options)
        
        # Apply stealth configurations
        if self.stealth_mode:
            context = self.utils.setup_stealth_context(context)
        
        return browser, context
    
    def comprehensive_scrape(self, url: str, monitor_content: bool = True, 
                           interact_with_elements: bool = True, max_retries: int = 3) -> Dict[str, Any]:
        """
        Perform a comprehensive scrape of a dynamic website with bot protection handling.
        
        Args:
            url: Target URL to scrape
            monitor_content: Whether to monitor dynamic content changes
            interact_with_elements: Whether to interact with expandable elements
            max_retries: Number of retries for bot protection
            
        Returns:
            Complete scraping analysis and specification
        """
        
        if not self.utils.is_url_valid(url):
            raise ValueError(f"Invalid URL: {url}")
        
        print(f"Starting comprehensive scrape of: {url}")
        if self.stealth_mode:
            print("🥷 Stealth mode enabled")
        
        last_error = None
        
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"🔄 Retry attempt {attempt + 1}/{max_retries}")
                self.utils.human_delay(2, 5)  # Wait between retries
            
            with sync_playwright() as p:
                browser, context = self._create_browser_context(p)
                
                # Set up request/response monitoring
                api_calls = []
                def handle_route(route):
                    request_info = {
                        'url': route.request.url,
                        'method': route.request.method,
                        'resource_type': route.request.resource_type
                    }
                    if any(keyword in route.request.url.lower() for keyword in ['api', 'ajax', 'json', 'graphql']):
                        api_calls.append(request_info)
                    route.continue_()
                
                context.route('**/*', handle_route)
                page = context.new_page()
                page.set_default_timeout(self.timeout)
                
                # Inject stealth scripts if enabled
                if self.stealth_mode:
                    self.utils.inject_stealth_scripts(page)
                
                try:
                    # Phase 1: Initial page load and structure capture
                    print("Phase 1: Loading page and capturing initial structure...")
                    
                    # Navigate with retry logic
                    page.goto(url, wait_until='domcontentloaded')
                    
                    # Add human-like behavior
                    if self.stealth_mode:
                        self.utils.simulate_human_behavior(page)
                    
                    # Check for bot protection
                    title = page.title()
                    protection_detected = self._detect_bot_protection(page, title)
                    
                    if protection_detected:
                        print(f"⚠️  Bot protection detected: {protection_detected}")
                        
                        # Handle different types of protection
                        if "cloudflare" in protection_detected.lower():
                            if self.utils.wait_for_cloudflare(page, max_wait=30):
                                print("✅ Cloudflare protection bypassed")
                            else:
                                if attempt < max_retries - 1:
                                    print("🔄 Cloudflare bypass failed, retrying...")
                                    browser.close()
                                    continue
                                else:
                                    raise Exception("Failed to bypass Cloudflare protection")
                        
                        # Try IUAM bypass
                        if "checking your browser" in protection_detected.lower():
                            self.utils.bypass_cloudflare_iuam(page)
                    
                    # Try flexible waiting strategies
                    wait_successful = False
                    
                    # Strategy 1: Try networkidle with shorter timeout
                    try:
                        print("🔄 Waiting for network idle...")
                        page.wait_for_load_state('networkidle', timeout=15000)
                        wait_successful = True
                        print("✅ Network idle achieved")
                    except Exception as e:
                        print(f"⚠️ Network idle timeout: {e}")
                    
                    # Strategy 2: If networkidle fails, wait for page to stabilize
                    if not wait_successful:
                        try:
                            print("🔄 Waiting for page to stabilize...")
                            self.utils.wait_for_content_settlement(page, max_wait_time=10000)
                            wait_successful = True
                            print("✅ Page stabilized")
                        except Exception as e:
                            print(f"⚠️ Page stabilization timeout: {e}")
                    
                    # Strategy 3: If still not stable, do a basic wait and continue
                    if not wait_successful:
                        print("⚠️ Using fallback wait strategy...")
                        page.wait_for_timeout(5000)  # Basic 5-second wait
                        print("⏰ Fallback wait completed, proceeding...")
                    
                    # Additional human behavior after loading
                    if self.stealth_mode:
                        self.utils.simulate_human_behavior(page)
                    
                    # Check final state
                    final_title = page.title()
                    print(f"📄 Final page title: '{final_title}'")
                    
                    # Re-check protection after waiting
                    final_protection = self._detect_bot_protection(page, final_title)
                    if final_protection and final_protection != protection_detected:
                        print(f"⚠️ Updated protection status: {final_protection}")
                        protection_detected = final_protection
                    
                    initial_structure = self.structure_capture.capture_page_structure(page)
                    initial_structure['api_endpoints'] = api_calls.copy()
                    initial_structure['protection_detected'] = protection_detected
                    initial_structure['stealth_mode_used'] = self.stealth_mode
                    initial_structure['wait_strategy_used'] = "networkidle" if wait_successful else "fallback"
                    
                    # Phase 2: Content monitoring setup
                    monitoring_data = None
                    if monitor_content:
                        print("Phase 2: Setting up content monitoring...")
                        
                        def interaction_callback(monitored_page):
                            if interact_with_elements:
                                return self.dynamic_handler.explore_expandable_content(monitored_page)
                            return {}
                        
                        monitoring_data = self.content_monitor.monitor_dynamic_content(
                            page, interaction_callback if interact_with_elements else None
                        )
                    
                    # Phase 3: Direct interaction with expandable elements (if not done during monitoring)
                    interaction_results = {}
                    if interact_with_elements and not monitor_content:
                        print("Phase 3: Interacting with expandable elements...")
                        interaction_results = self.dynamic_handler.explore_expandable_content(page)
                    elif monitor_content and interact_with_elements:
                        # Extract interaction results from monitoring data
                        interaction_results = self.dynamic_handler.expanded_states
                    
                    # Phase 4: Final content extraction
                    print("Phase 4: Extracting final content state...")
                    final_structure = self.structure_capture.capture_page_structure(page)
                    final_structure['api_endpoints'] = api_calls.copy()
                    
                    # Add raw DOM information for debugging
                    final_structure['raw_page_info'] = self._extract_raw_page_info(page)
                    final_structure['stealth_mode_used'] = self.stealth_mode
                    
                    # Phase 5: Generate comprehensive specification
                    print("Phase 5: Generating scraping specification...")
                    scraping_spec = self.spec_generator.generate_scraping_spec(
                        structure=final_structure,
                        interactions=interaction_results,
                        content={'final_state': final_structure},
                        monitoring_data=monitoring_data
                    )
                    
                    # Compile comprehensive results
                    self.results = {
                        'url': url,
                        'scraping_timestamp': time.time(),
                        'initial_structure': initial_structure,
                        'final_structure': final_structure,
                        'interaction_results': interaction_results,
                        'monitoring_data': monitoring_data,
                        'scraping_specification': scraping_spec,
                        'summary': self._generate_scraping_summary(
                            initial_structure, final_structure, interaction_results, monitoring_data
                        ),
                        'attempts_made': attempt + 1,
                        'stealth_mode_used': self.stealth_mode
                    }
                    
                    print("✅ Comprehensive scraping completed successfully!")
                    browser.close()
                    return self.results
                    
                except Exception as e:
                    last_error = e
                    print(f"❌ Attempt {attempt + 1} failed: {e}")
                    browser.close()
                    
                    if attempt < max_retries - 1:
                        continue
                    else:
                        break
        
        # If we get here, all attempts failed
        error_result = {
            'url': url,
            'error': str(last_error),
            'partial_results': getattr(self, 'results', {}),
            'timestamp': time.time(),
            'attempts_made': max_retries,
            'stealth_mode_used': self.stealth_mode
        }
        print(f"❌ All {max_retries} attempts failed. Last error: {last_error}")
        return error_result
    
    def _detect_bot_protection(self, page, title: str) -> str:
        """Detect if the page is showing bot protection or blocking."""
        protection_indicators = []
        
        # Check title for common protection messages
        protection_titles = [
            "just a moment", "checking your browser", "cloudflare", 
            "access denied", "blocked", "captcha", "security check",
            "ddos protection", "rate limited"
        ]
        
        for indicator in protection_titles:
            if indicator in title.lower():
                protection_indicators.append(f"Title contains '{indicator}'")
        
        # Check for common protection elements
        try:
            protection_selectors = [
                '.cf-browser-verification',  # Cloudflare
                '#challenge-form',  # Cloudflare
                '.grecaptcha-badge',  # reCAPTCHA
                '[data-sitekey]',  # CAPTCHA
                '.challenge-running',  # Various protection services
                'meta[name="robots"][content*="noindex"]'  # Blocking meta tag
            ]
            
            for selector in protection_selectors:
                if page.query_selector(selector):
                    protection_indicators.append(f"Found protection element: {selector}")
        except Exception:
            pass  # Ignore errors in protection detection
        
        # Check for minimal content (possible sign of protection page)
        try:
            body_text = page.query_selector('body').inner_text()
            if len(body_text.strip()) < 100:
                protection_indicators.append("Very minimal page content")
        except Exception:
            pass
        
        return "; ".join(protection_indicators) if protection_indicators else None
    
    def _extract_raw_page_info(self, page) -> Dict[str, Any]:
        """Extract raw page information for debugging purposes."""
        try:
            return {
                'title': page.title(),
                'url': page.url,
                'body_text_length': len(page.query_selector('body').inner_text() or ''),
                'body_html_length': len(page.query_selector('body').inner_html() or ''),
                'element_count': len(page.query_selector_all('*')),
                'script_count': len(page.query_selector_all('script')),
                'style_count': len(page.query_selector_all('style, link[rel="stylesheet"]')),
                'form_count': len(page.query_selector_all('form')),
                'input_count': len(page.query_selector_all('input')),
                'button_count': len(page.query_selector_all('button')),
                'link_count': len(page.query_selector_all('a')),
                'image_count': len(page.query_selector_all('img')),
                'meta_tags': [
                    {'name': meta.get_attribute('name'), 'content': meta.get_attribute('content')}
                    for meta in page.query_selector_all('meta[name]')
                ],
                'first_200_chars': (page.query_selector('body').inner_text() or '')[:200]
            }
        except Exception as e:
            return {'error': f'Failed to extract raw page info: {str(e)}'}
    
    def quick_scrape(self, url: str) -> Dict[str, Any]:
        """
        Perform a quick scrape focusing on basic structure and content.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            Basic scraping results
        """
        
        print(f"Starting quick scrape of: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(15000)
            
            try:
                page.goto(url)
                page.wait_for_load_state('networkidle')
                
                # Capture basic structure
                structure = self.structure_capture.capture_page_structure(page)
                
                # Try basic interactions
                expandables = page.query_selector_all('[aria-expanded="false"], details:not([open])')
                basic_interactions = {}
                
                for i, element in enumerate(expandables[:5]):  # Limit to 5 elements
                    try:
                        element.click()
                        time.sleep(0.5)
                        basic_interactions[f'element_{i}'] = {'success': True}
                    except Exception as e:
                        basic_interactions[f'element_{i}'] = {'success': False, 'error': str(e)}
                
                # Generate basic spec
                basic_spec = self.spec_generator.generate_scraping_spec(
                    structure=structure,
                    interactions=basic_interactions,
                    content={'structure': structure}
                )
                
                results = {
                    'url': url,
                    'scraping_mode': 'quick',
                    'timestamp': time.time(),
                    'structure': structure,
                    'basic_interactions': basic_interactions,
                    'basic_specification': basic_spec
                }
                
                print("✅ Quick scraping completed!")
                return results
                
            except Exception as e:
                print(f"❌ Quick scraping failed: {e}")
                return {'url': url, 'error': str(e), 'timestamp': time.time()}
                
            finally:
                browser.close()
    
    def analyze_single_page(self, url: str, save_to_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single page and optionally save results to file.
        
        Args:
            url: Target URL to analyze
            save_to_file: Optional filepath to save the specification
            
        Returns:
            Analysis results
        """
        
        results = self.comprehensive_scrape(url)
        
        if save_to_file and 'scraping_specification' in results:
            if save_to_file.endswith('.json'):
                self.spec_generator.save_spec_to_file(results['scraping_specification'], save_to_file)
            else:
                self.spec_generator.save_spec_as_text(
                    results['scraping_specification'], 
                    save_to_file, 
                    structure=results.get('final_structure')
                )
        
        return results
    
    def batch_analyze(self, urls: List[str], output_dir: str = "scraping_specs") -> Dict[str, Any]:
        """
        Analyze multiple URLs in batch.
        
        Args:
            urls: List of URLs to analyze
            output_dir: Directory to save individual specifications
            
        Returns:
            Batch analysis results
        """
        
        import os
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        batch_results = {
            'total_urls': len(urls),
            'successful': 0,
            'failed': 0,
            'results': {},
            'summary': {}
        }
        
        for i, url in enumerate(urls):
            print(f"\nAnalyzing {i+1}/{len(urls)}: {url}")
            
            try:
                result = self.comprehensive_scrape(url)
                
                if 'error' not in result:
                    batch_results['successful'] += 1
                    batch_results['results'][url] = result
                    
                    # Save individual specification
                    safe_filename = url.replace('https://', '').replace('http://', '').replace('/', '_')
                    spec_file = os.path.join(output_dir, f"{safe_filename}_spec.txt")
                    self.spec_generator.save_spec_as_text(result['scraping_specification'], spec_file)
                    
                else:
                    batch_results['failed'] += 1
                    batch_results['results'][url] = result
                    
            except Exception as e:
                batch_results['failed'] += 1
                batch_results['results'][url] = {'error': str(e)}
                print(f"Failed to analyze {url}: {e}")
        
        # Generate batch summary
        batch_results['summary'] = self._generate_batch_summary(batch_results)
        
        return batch_results
    
    def _generate_scraping_summary(self, initial_structure: Dict[str, Any], 
                                 final_structure: Dict[str, Any],
                                 interactions: Dict[str, Any],
                                 monitoring_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the scraping session."""
        
        summary = {
            'page_info': {
                'url': final_structure.get('url'),
                'title': final_structure.get('title'),
                'layout_type': 'unknown'
            },
            'structure_analysis': {
                'total_elements': len(final_structure.get('interactive_elements', [])),
                'expandable_elements': len([el for el in final_structure.get('interactive_elements', []) 
                                          if el.get('interactionType') == 'expandable']),
                'static_content_areas': len(final_structure.get('content_patterns', {}).get('contentAreas', []))
            },
            'interaction_summary': {
                'total_interactions': len(interactions),
                'successful_interactions': sum(1 for data in interactions.values() 
                                             if data.get('interaction_result', {}).get('success')),
                'content_changes_detected': sum(1 for data in interactions.values() 
                                              if data.get('interaction_result', {}).get('content_changed'))
            },
            'dynamic_behavior': {},
            'recommendations': []
        }
        
        # Add monitoring summary if available
        if monitoring_data:
            summary['dynamic_behavior'] = {
                'mutations_detected': len(monitoring_data.get('mutations', [])),
                'api_calls_made': len(monitoring_data.get('api_calls', [])),
                'activity_level': monitoring_data.get('summary', {}).get('activity_level', 'unknown')
            }
        
        # Generate recommendations
        if summary['interaction_summary']['total_interactions'] > 0:
            success_rate = (summary['interaction_summary']['successful_interactions'] / 
                          summary['interaction_summary']['total_interactions'])
            if success_rate < 0.7:
                summary['recommendations'].append("Consider implementing robust error handling for interactions")
            
        if summary['dynamic_behavior'].get('activity_level') == 'high':
            summary['recommendations'].append("Use longer wait times due to high dynamic activity")
            
        if summary['structure_analysis']['expandable_elements'] > 5:
            summary['recommendations'].append("Implement systematic expansion strategy for multiple expandable elements")
        
        return summary
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of batch analysis results."""
        
        successful_results = [result for result in batch_results['results'].values() 
                            if 'error' not in result]
        
        if not successful_results:
            return {'message': 'No successful analyses to summarize'}
        
        # Aggregate statistics
        total_expandables = sum(len(result.get('interaction_results', {})) for result in successful_results)
        total_interactions = sum(result.get('summary', {}).get('interaction_summary', {}).get('total_interactions', 0) 
                               for result in successful_results)
        
        layout_types = {}
        for result in successful_results:
            layout_type = (result.get('scraping_specification', {})
                         .get('site_structure', {})
                         .get('layout_analysis', {})
                         .get('layout_type', 'unknown'))
            layout_types[layout_type] = layout_types.get(layout_type, 0) + 1
        
        return {
            'success_rate': batch_results['successful'] / batch_results['total_urls'],
            'average_expandable_elements': total_expandables / len(successful_results) if successful_results else 0,
            'average_interactions': total_interactions / len(successful_results) if successful_results else 0,
            'common_layout_types': layout_types,
            'common_challenges': [
                'Dynamic content loading',
                'Complex interaction patterns',
                'Network dependencies'
            ]
        }
    
    def get_extraction_results(self) -> Dict[str, Any]:
        """Get the results of the last scraping operation."""
        return self.results
    
    def clear_results(self):
        """Clear stored results to free memory."""
        self.results = {}
        self.dynamic_handler.expanded_states = {}
        self.content_monitor.content_timeline = []
        self.content_monitor.mutation_log = []
        self.content_monitor.api_calls = [] 