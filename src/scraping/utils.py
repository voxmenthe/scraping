"""
Utility functions for web scraping operations.
"""

import time
import json
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse


class ScrapingUtils:
    """Utility class with helper methods for web scraping operations."""
    
    # Realistic user agents for different browsers and OS
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        # Firefox on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        # Safari on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Get a random realistic user agent."""
        return random.choice(ScrapingUtils.USER_AGENTS)
    
    @staticmethod
    def get_stealth_headers() -> Dict[str, str]:
        """Get realistic browser headers to avoid detection."""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    @staticmethod
    def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add human-like random delay."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    @staticmethod
    def setup_stealth_context(context):
        """Configure browser context for stealth operation."""
        # Add extra headers
        context.set_extra_http_headers(ScrapingUtils.get_stealth_headers())
        
        # Set geolocation (optional)
        try:
            context.set_geolocation({'latitude': 40.7128, 'longitude': -74.0060})  # New York
            context.grant_permissions(['geolocation'])
        except Exception:
            pass  # Ignore geolocation errors
        
        return context
    
    @staticmethod
    def inject_stealth_scripts(page):
        """Inject scripts to mask automation indicators."""
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock languages and plugins
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock screen properties
        Object.defineProperty(screen, 'colorDepth', {
            get: () => 24,
        });
        
        // Mock chrome object
        window.chrome = {
            runtime: {},
        };
        
        // Mock permission API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        """
        
        page.add_init_script(stealth_script)
    
    @staticmethod
    def simulate_human_behavior(page):
        """Simulate human-like behavior on the page."""
        try:
            # Random mouse movements
            page.mouse.move(
                random.randint(100, 800), 
                random.randint(100, 600)
            )
            
            # Random scroll
            page.evaluate(f"""
                window.scrollTo({{
                    top: {random.randint(0, 500)},
                    behavior: 'smooth'
                }});
            """)
            
            # Small delay
            ScrapingUtils.human_delay(0.5, 1.5)
            
            # Sometimes click on a safe element (like body)
            if random.random() < 0.3:  # 30% chance
                page.mouse.click(
                    random.randint(100, 200), 
                    random.randint(100, 200)
                )
                
        except Exception:
            pass  # Ignore errors in behavior simulation
    
    @staticmethod
    def wait_for_cloudflare(page, max_wait: int = 30):
        """Wait for Cloudflare protection to complete."""
        print("⏳ Waiting for Cloudflare protection...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                title = page.title().lower()
                
                # Check if we're past the protection
                if not any(indicator in title for indicator in 
                          ['just a moment', 'checking your browser', 'cloudflare']):
                    print("✅ Cloudflare protection completed")
                    return True
                
                # Wait and check again
                time.sleep(1)
                
            except Exception:
                time.sleep(1)
        
        print("⚠️ Cloudflare protection timeout")
        return False
    
    @staticmethod
    def bypass_cloudflare_iuam(page):
        """Attempt to bypass Cloudflare I'm Under Attack Mode."""
        try:
            # Wait for the challenge to appear
            page.wait_for_selector('#challenge-form', timeout=5000)
            print("🔄 Detected Cloudflare IUAM challenge")
            
            # Wait for the challenge to auto-complete
            # Most IUAM challenges complete automatically after 5 seconds
            for i in range(10):
                if page.url != page.url:  # URL changed (redirect happened)
                    break
                time.sleep(1)
                print(f"⏳ Waiting for challenge completion... {i+1}/10")
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def get_xpath(element) -> str:
        """Generate XPath for a given element."""
        js_code = """
        function getXPath(element) {
            if (element.id !== '') {
                return 'id("' + element.id + '")';
            }
            if (element === document.body) {
                return element.tagName;
            }
            
            var ix = 0;
            var siblings = element.parentNode.childNodes;
            for (var i = 0; i < siblings.length; i++) {
                var sibling = siblings[i];
                if (sibling === element) {
                    return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                    ix++;
                }
            }
        }
        return getXPath(arguments[0]);
        """
        return element.evaluate(js_code)
    
    @staticmethod
    def wait_for_content_settlement(page, max_wait_time: int = 10000, stability_duration: int = 1000):
        """Wait for page content to stabilize after dynamic changes."""
        try:
            page.evaluate(f"""
                new Promise((resolve) => {{
                    let lastHeight = document.body ? document.body.scrollHeight : 0;
                    let stableFor = 0;
                    let iterations = 0;
                    const maxIterations = {max_wait_time // 100};
                    
                    const checkStability = () => {{
                        iterations++;
                        if (iterations >= maxIterations) {{
                            resolve();
                            return;
                        }}
                        
                        const currentHeight = document.body ? document.body.scrollHeight : 0;
                        if (currentHeight === lastHeight) {{
                            stableFor += 100;
                            if (stableFor >= {stability_duration}) {{
                                resolve();
                                return;
                            }}
                        }} else {{
                            stableFor = 0;
                            lastHeight = currentHeight;
                        }}
                        setTimeout(checkStability, 100);
                    }};
                    
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', checkStability);
                    }} else {{
                        checkStability();
                    }}
                    
                    // Fallback timeout
                    setTimeout(resolve, {max_wait_time});
                }})
            """)
        except Exception as e:
            print(f"Content settlement error: {e}")
            # Fallback to simple timeout
            time.sleep(max_wait_time / 1000)
    
    @staticmethod
    def safe_interact(page, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """Safely interact with an element and capture the result."""
        result = {
            'element_id': element_info.get('id', 'unknown'),
            'success': False,
            'error': None,
            'content_before': None,
            'content_after': None
        }
        
        try:
            # Capture content before interaction
            if 'selector' in element_info:
                element = page.query_selector(element_info['selector'])
                if element:
                    result['content_before'] = element.inner_html()
                    
                    # Add human-like delay before interaction
                    ScrapingUtils.human_delay(0.2, 0.8)
                    
                    # Perform interaction
                    element.click()
                    
                    # Add delay after interaction
                    ScrapingUtils.human_delay(0.3, 1.0)
                    
                    # Capture content after interaction
                    result['content_after'] = element.inner_html()
                    result['success'] = True
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    @staticmethod
    def is_url_valid(url: str) -> bool:
        """Check if a URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize and resolve URLs."""
        if base_url:
            return urljoin(base_url, url)
        return url
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Remove extra whitespace and normalize line breaks
        return " ".join(text.strip().split())
    
    @staticmethod
    def save_json(data: Any, filepath: str):
        """Save data to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_json(filepath: str) -> Any:
        """Load data from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def generate_element_signature(element_info: Dict[str, Any]) -> str:
        """Generate a unique signature for an element."""
        signature_parts = []
        
        if element_info.get('id'):
            signature_parts.append(f"id:{element_info['id']}")
        if element_info.get('tagName'):
            signature_parts.append(f"tag:{element_info['tagName']}")
        if element_info.get('className'):
            signature_parts.append(f"class:{element_info['className']}")
        
        return "|".join(signature_parts) if signature_parts else "unknown" 