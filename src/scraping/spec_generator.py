"""
Scraping specification generator for creating LLM-friendly scraping instructions.
"""

import json
from typing import Dict, List, Any, Optional
from .utils import ScrapingUtils


class ScrapingSpecGenerator:
    """Generates comprehensive scraping specifications for LLM analysis."""
    
    def __init__(self):
        self.utils = ScrapingUtils()
    
    def generate_scraping_spec(self, structure: Dict[str, Any], 
                             interactions: Dict[str, Any], 
                             content: Dict[str, Any],
                             monitoring_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a comprehensive specification an LLM can use to design a scraper."""
        
        spec = {
            'metadata': {
                'url': structure.get('url'),
                'title': structure.get('title'),
                'generation_timestamp': self._get_timestamp(),
                'analysis_version': '1.0'
            },
            
            'site_structure': {
                'static_elements': self._identify_static_elements(structure),
                'dynamic_elements': self._identify_dynamic_elements(structure),
                'interaction_patterns': self._analyze_interaction_patterns(interactions),
                'layout_analysis': self._analyze_layout(structure)
            },
            
            'content_patterns': {
                'main_content_selectors': self._find_content_selectors(content, structure),
                'metadata_selectors': self._find_metadata_selectors(structure),
                'navigation_patterns': self._extract_navigation_patterns(structure),
                'form_patterns': self._analyze_forms(structure)
            },
            
            'dynamic_behavior': {
                'expandable_content': self._analyze_expandable_content(interactions),
                'content_loading_patterns': self._analyze_content_loading(monitoring_data) if monitoring_data else {},
                'user_interaction_requirements': self._determine_interaction_requirements(interactions),
                'timing_requirements': self._analyze_timing_requirements(monitoring_data) if monitoring_data else {}
            },
            
            'scraping_strategy': {
                'required_interactions': self._list_required_interactions(interactions),
                'wait_conditions': self._determine_wait_conditions(content, monitoring_data),
                'content_extraction_order': self._determine_extraction_order(structure, interactions),
                'error_handling': self._generate_error_handling_strategy(interactions)
            },
            
            'technical_requirements': {
                'browser_requirements': self._analyze_browser_requirements(structure),
                'javascript_required': self._check_javascript_requirements(structure, monitoring_data),
                'network_dependencies': self._analyze_network_dependencies(monitoring_data) if monitoring_data else {},
                'performance_considerations': self._analyze_performance_requirements(monitoring_data) if monitoring_data else {}
            },
            
            'edge_cases': self._identify_edge_cases(structure, interactions, monitoring_data),
            
            'example_outputs': self._generate_example_outputs(content),
            
            'implementation_guide': self._generate_implementation_guide(structure, interactions, monitoring_data)
        }
        
        return spec
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def _identify_static_elements(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify elements that are likely static (non-dynamic)."""
        static_elements = []
        
        # Extract from structure analysis
        content_patterns = structure.get('content_patterns', {})
        
        # Headers are usually static
        for heading in content_patterns.get('headings', []):
            static_elements.append({
                'type': 'heading',
                'level': heading.get('level'),
                'text': heading.get('text'),
                'selector': f"{heading.get('level').lower()}" + (f"#{heading.get('id')}" if heading.get('id') else ""),
                'importance': 'high' if heading.get('level') in ['H1', 'H2'] else 'medium'
            })
        
        # Navigation elements are usually static
        for nav in content_patterns.get('navigation', []):
            static_elements.append({
                'type': 'navigation',
                'tagName': nav.get('tagName'),
                'className': nav.get('className'),
                'linkCount': nav.get('linkCount'),
                'importance': 'high'
            })
        
        # Content areas with consistent selectors
        for area in content_patterns.get('contentAreas', []):
            if area.get('selector') in ['main', 'article', '.content', '#content']:
                static_elements.append({
                    'type': 'content_area',
                    'selector': area.get('selector'),
                    'tagName': area.get('tagName'),
                    'textLength': area.get('textLength'),
                    'importance': 'high'
                })
        
        return static_elements
    
    def _identify_dynamic_elements(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify elements that are likely dynamic."""
        dynamic_elements = []
        
        for element in structure.get('interactive_elements', []):
            if element.get('interactionType') in ['expandable', 'clickable']:
                dynamic_elements.append({
                    'type': element.get('interactionType'),
                    'selector': element.get('selector'),
                    'tagName': element.get('tagName'),
                    'text': element.get('text'),
                    'attributes': element.get('attributes', {}),
                    'xpath': element.get('xpath'),
                    'importance': 'high' if element.get('interactionType') == 'expandable' else 'medium'
                })
        
        return dynamic_elements
    
    def _analyze_interaction_patterns(self, interactions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in user interactions."""
        patterns = {
            'expansion_methods': {},
            'success_rates': {},
            'common_selectors': [],
            'interaction_sequences': []
        }
        
        successful_interactions = 0
        total_interactions = len(interactions)
        
        for element_id, interaction_data in interactions.items():
            result = interaction_data.get('interaction_result', {})
            
            if result.get('success'):
                successful_interactions += 1
                method = result.get('method_used', 'unknown')
                patterns['expansion_methods'][method] = patterns['expansion_methods'].get(method, 0) + 1
        
        patterns['success_rates']['overall'] = successful_interactions / total_interactions if total_interactions > 0 else 0
        
        return patterns
    
    def _analyze_layout(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the layout structure of the page."""
        layout = {
            'viewport': structure.get('viewport', {}),
            'content_distribution': {},
            'responsive_indicators': [],
            'layout_type': 'unknown'
        }
        
        # Analyze content areas
        content_areas = structure.get('content_patterns', {}).get('contentAreas', [])
        if content_areas:
            total_area = sum(area.get('position', {}).get('width', 0) * area.get('position', {}).get('height', 0) 
                           for area in content_areas)
            
            layout['content_distribution'] = {
                'primary_content_areas': len([area for area in content_areas if area.get('textLength', 0) > 1000]),
                'total_content_area': total_area
            }
        
        # Determine layout type based on structure
        if any('nav' in str(area.get('selector', '')).lower() for area in content_areas):
            layout['layout_type'] = 'traditional_website'
        elif structure.get('meta_info', {}).get('hasServiceWorker'):
            layout['layout_type'] = 'spa_application'
        else:
            layout['layout_type'] = 'static_website'
        
        return layout
    
    def _find_content_selectors(self, content: Dict[str, Any], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find the best selectors for extracting main content."""
        selectors = []
        
        # From content patterns
        content_areas = structure.get('content_patterns', {}).get('contentAreas', [])
        for area in content_areas:
            if area.get('textLength', 0) > 500:  # Substantial content
                selectors.append({
                    'selector': area.get('selector'),
                    'type': 'content_area',
                    'confidence': 'high' if area.get('textLength', 0) > 2000 else 'medium',
                    'expected_content_length': area.get('textLength'),
                    'description': f"Main content area with {area.get('textLength')} characters"
                })
        
        # Common content selectors
        common_selectors = [
            {'selector': 'main', 'type': 'semantic', 'confidence': 'high'},
            {'selector': 'article', 'type': 'semantic', 'confidence': 'high'},
            {'selector': '.content', 'type': 'class-based', 'confidence': 'medium'},
            {'selector': '#content', 'type': 'id-based', 'confidence': 'medium'},
            {'selector': '[role="main"]', 'type': 'aria-based', 'confidence': 'high'}
        ]
        
        selectors.extend(common_selectors)
        
        return selectors
    
    def _find_metadata_selectors(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find selectors for extracting metadata."""
        metadata_selectors = []
        
        # From meta tags
        for meta in structure.get('meta_info', {}).get('metas', []):
            if meta.get('name') in ['description', 'keywords', 'author', 'title']:
                metadata_selectors.append({
                    'selector': f'meta[name="{meta.get("name")}"]',
                    'attribute': 'content',
                    'type': 'meta_tag',
                    'confidence': 'high',
                    'description': f'Meta {meta.get("name")}'
                })
        
        # From headings
        for heading in structure.get('content_patterns', {}).get('headings', []):
            if heading.get('level') == 'H1':
                metadata_selectors.append({
                    'selector': 'h1',
                    'type': 'title_heading',
                    'confidence': 'high',
                    'description': 'Page title from H1'
                })
        
        return metadata_selectors
    
    def _extract_navigation_patterns(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract navigation patterns from the page."""
        nav_patterns = {
            'main_navigation': [],
            'breadcrumbs': [],
            'pagination': [],
            'internal_links': 0
        }
        
        for nav in structure.get('content_patterns', {}).get('navigation', []):
            nav_patterns['main_navigation'].append({
                'selector': f"{nav.get('tagName').lower()}.{nav.get('className')}".replace(' ', '.'),
                'link_count': nav.get('linkCount'),
                'type': 'primary' if nav.get('linkCount', 0) > 5 else 'secondary'
            })
        
        return nav_patterns
    
    def _analyze_forms(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze forms on the page."""
        form_patterns = []
        
        for form in structure.get('content_patterns', {}).get('forms', []):
            form_patterns.append({
                'action': form.get('action'),
                'method': form.get('method'),
                'field_count': form.get('fieldCount'),
                'type': 'search' if 'search' in form.get('action', '').lower() else 'form',
                'interaction_required': form.get('fieldCount', 0) > 0
            })
        
        return form_patterns
    
    def _analyze_expandable_content(self, interactions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze expandable content patterns."""
        analysis = {
            'total_expandable': len(interactions),
            'successful_expansions': 0,
            'expansion_methods': {},
            'content_reveals': [],
            'nested_levels': 0
        }
        
        for element_id, data in interactions.items():
            result = data.get('interaction_result', {})
            if result.get('success'):
                analysis['successful_expansions'] += 1
                
                method = result.get('method_used', 'unknown')
                analysis['expansion_methods'][method] = analysis['expansion_methods'].get(method, 0) + 1
                
                if result.get('content_changed'):
                    analysis['content_reveals'].append({
                        'element_id': element_id,
                        'method': method,
                        'element_info': data.get('element_info', {})
                    })
            
            if 'nested_expandables' in data:
                analysis['nested_levels'] = max(analysis['nested_levels'], 
                                              max((item.get('depth', 0) for item in data['nested_expandables'].values()), default=0))
        
        return analysis
    
    def _analyze_content_loading(self, monitoring_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content loading patterns."""
        if not monitoring_data:
            return {}
        
        mutations = monitoring_data.get('mutations', [])
        return {
            'dynamic_loading_detected': len(mutations) > 0,
            'mutation_count': len(mutations),
            'loading_timeframe': mutations[-1].get('timestamp', 0) - mutations[0].get('timestamp', 0) if mutations else 0,
            'content_stability': monitoring_data.get('summary', {}).get('activity_level', 'unknown'),
            'api_calls': len(monitoring_data.get('api_calls', []))
        }
    
    def _determine_interaction_requirements(self, interactions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine what interactions are required for full content access."""
        requirements = []
        
        for element_id, data in interactions.items():
            if data.get('interaction_result', {}).get('success') and data.get('interaction_result', {}).get('content_changed'):
                requirements.append({
                    'element_id': element_id,
                    'method': data.get('interaction_result', {}).get('method_used'),
                    'element_info': data.get('element_info', {}),
                    'priority': 'high' if 'nested_expandables' in data else 'medium'
                })
        
        return requirements
    
    def _analyze_timing_requirements(self, monitoring_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze timing requirements for content loading."""
        if not monitoring_data:
            return {}
        
        summary = monitoring_data.get('summary', {})
        return {
            'recommended_wait_time': max(2000, summary.get('time_span_ms', 0)),
            'stability_check_required': summary.get('activity_level') in ['medium', 'high'],
            'network_wait_required': len(monitoring_data.get('api_calls', [])) > 0
        }
    
    def _list_required_interactions(self, interactions: Dict[str, Any]) -> List[str]:
        """List all required interactions for complete scraping."""
        required = []
        
        for element_id, data in interactions.items():
            if data.get('interaction_result', {}).get('success'):
                element_info = data.get('element_info', {})
                required.append(f"Click {element_info.get('tagName', 'element')} with text '{element_info.get('text', '')[:50]}'")
        
        return required
    
    def _determine_wait_conditions(self, content: Dict[str, Any], monitoring_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine what conditions to wait for during scraping."""
        conditions = [
            {
                'type': 'network_idle',
                'description': 'Wait for network requests to complete',
                'timeout': 10000
            },
            {
                'type': 'element_visible',
                'selector': 'body',
                'description': 'Wait for page body to be visible',
                'timeout': 5000
            }
        ]
        
        if monitoring_data and monitoring_data.get('api_calls'):
            conditions.append({
                'type': 'api_complete',
                'description': 'Wait for API calls to complete',
                'timeout': 15000
            })
        
        return conditions
    
    def _determine_extraction_order(self, structure: Dict[str, Any], interactions: Dict[str, Any]) -> List[str]:
        """Determine the optimal order for content extraction."""
        order = [
            "1. Load page and wait for initial content",
            "2. Extract static metadata (title, meta tags)",
            "3. Extract visible static content",
        ]
        
        if interactions:
            order.extend([
                "4. Identify and interact with expandable elements",
                "5. Wait for dynamic content to load",
                "6. Extract newly revealed content"
            ])
        
        order.append("7. Extract navigation and structural elements")
        
        return order
    
    def _generate_error_handling_strategy(self, interactions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate error handling strategies."""
        failed_interactions = sum(1 for data in interactions.values() 
                                if not data.get('interaction_result', {}).get('success'))
        
        return {
            'interaction_failure_rate': failed_interactions / len(interactions) if interactions else 0,
            'recommended_strategies': [
                'Use explicit waits instead of fixed delays',
                'Implement retry logic for failed interactions',
                'Gracefully handle missing elements',
                'Log interaction failures for debugging'
            ],
            'common_failure_points': [
                'Elements not found',
                'Elements not clickable',
                'Content not loading after interaction'
            ]
        }
    
    def _analyze_browser_requirements(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze browser and JavaScript requirements."""
        meta_info = structure.get('meta_info', {})
        
        return {
            'javascript_required': True,  # Assume true for dynamic sites
            'service_worker': meta_info.get('hasServiceWorker', False),
            'recommended_browser': 'chromium',
            'headless_compatible': True,
            'viewport_size': structure.get('viewport', {})
        }
    
    def _check_javascript_requirements(self, structure: Dict[str, Any], monitoring_data: Optional[Dict[str, Any]]) -> bool:
        """Check if JavaScript is required for the site."""
        # If there are mutations or API calls, JavaScript is likely required
        if monitoring_data:
            return len(monitoring_data.get('mutations', [])) > 0 or len(monitoring_data.get('api_calls', [])) > 0
        
        # Check for script tags
        return structure.get('meta_info', {}).get('scripts', 0) > 0
    
    def _analyze_network_dependencies(self, monitoring_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network dependencies."""
        if not monitoring_data:
            return {}
        
        api_calls = monitoring_data.get('api_calls', [])
        return {
            'api_endpoints': [call.get('url') for call in api_calls],
            'request_methods': list(set(call.get('method') for call in api_calls)),
            'concurrent_requests': len(api_calls),
            'requires_network_monitoring': len(api_calls) > 0
        }
    
    def _analyze_performance_requirements(self, monitoring_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance requirements and considerations."""
        if not monitoring_data:
            return {}
        
        summary = monitoring_data.get('summary', {})
        return {
            'page_complexity': summary.get('activity_level', 'unknown'),
            'recommended_timeout': max(10000, summary.get('time_span_ms', 0) * 2),
            'memory_considerations': 'moderate' if summary.get('total_mutations', 0) > 100 else 'low',
            'parallel_processing': 'not_recommended' if summary.get('activity_level') == 'high' else 'possible'
        }
    
    def _identify_edge_cases(self, structure: Dict[str, Any], interactions: Dict[str, Any], 
                           monitoring_data: Optional[Dict[str, Any]]) -> List[str]:
        """Identify potential edge cases and challenges."""
        edge_cases = []
        
        # Check for nested interactions
        nested_count = sum(1 for data in interactions.values() if 'nested_expandables' in data)
        if nested_count > 0:
            edge_cases.append(f"Nested expandable content ({nested_count} elements with nested interactions)")
        
        # Check for high mutation rate
        if monitoring_data and monitoring_data.get('summary', {}).get('activity_level') == 'high':
            edge_cases.append("High dynamic content activity - may require longer wait times")
        
        # Check for complex interactions
        failed_interactions = sum(1 for data in interactions.values() 
                                if not data.get('interaction_result', {}).get('success'))
        if failed_interactions > len(interactions) * 0.3:
            edge_cases.append(f"High interaction failure rate ({failed_interactions}/{len(interactions)})")
        
        # Check for service worker
        if structure.get('meta_info', {}).get('hasServiceWorker'):
            edge_cases.append("Service Worker detected - may affect caching and network requests")
        
        return edge_cases
    
    def _generate_example_outputs(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate example outputs showing what can be extracted."""
        examples = {
            'sample_selectors': [
                {'selector': 'h1', 'expected': 'Page title'},
                {'selector': 'main', 'expected': 'Main content area'},
                {'selector': 'meta[name="description"]', 'attribute': 'content', 'expected': 'Page description'}
            ],
            'content_types': [
                'Text content',
                'Navigation links',
                'Metadata',
                'Dynamic content (after interactions)'
            ]
        }
        
        return examples
    
    def _generate_implementation_guide(self, structure: Dict[str, Any], interactions: Dict[str, Any], 
                                     monitoring_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a practical implementation guide."""
        return {
            'setup_steps': [
                "1. Install Playwright and set up browser automation",
                "2. Configure page timeouts and wait conditions", 
                "3. Set up error handling and retry logic"
            ],
            'scraping_workflow': [
                "1. Navigate to target URL",
                "2. Wait for initial page load",
                "3. Extract static content first",
                "4. Identify and interact with dynamic elements",
                "5. Wait for content changes to complete",
                "6. Extract dynamic content",
                "7. Clean and structure the extracted data"
            ],
            'code_template': self._generate_code_template(),
            'testing_recommendations': [
                "Test with both headless and headed browsers",
                "Verify extraction with different network conditions",
                "Test error handling with unreachable elements",
                "Validate data completeness after interactions"
            ]
        }
    
    def _generate_code_template(self) -> str:
        """Generate a basic code template for implementing the scraper."""
        return """
from playwright.sync_api import sync_playwright

def scrape_dynamic_site(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate and wait for content
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        # Extract static content
        title = page.title()
        
        # Interact with dynamic elements
        expandables = page.query_selector_all('[aria-expanded="false"]')
        for element in expandables:
            try:
                element.click()
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"Interaction failed: {e}")
        
        # Extract final content
        content = page.query_selector('main').inner_text()
        
        browser.close()
        return {'title': title, 'content': content}
"""
    
    def save_spec_to_file(self, spec: Dict[str, Any], filepath: str):
        """Save the specification to a file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        print(f"Scraping specification saved to {filepath}")
    
    def save_spec_as_text(self, spec: Dict[str, Any], filepath: str, structure: Optional[Dict[str, Any]] = None):
        """Save the specification as a human-readable text file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("DYNAMIC WEB SCRAPING SPECIFICATION\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            f.write("METADATA:\n")
            f.write("-" * 20 + "\n")
            for key, value in spec.get('metadata', {}).items():
                f.write(f"{key.replace('_', ' ').title()}: {value}\n")
            f.write("\n")
            
            # Site Structure
            f.write("SITE STRUCTURE:\n")
            f.write("-" * 20 + "\n")
            site_structure = spec.get('site_structure', {})
            f.write(f"Static Elements: {len(site_structure.get('static_elements', []))}\n")
            f.write(f"Dynamic Elements: {len(site_structure.get('dynamic_elements', []))}\n")
            f.write(f"Layout Type: {site_structure.get('layout_analysis', {}).get('layout_type', 'unknown')}\n")
            
            # Detailed Static Elements
            static_elements = site_structure.get('static_elements', [])
            if static_elements:
                f.write(f"\nSTATIC ELEMENTS DETAILS:\n")
                f.write("-" * 30 + "\n")
                for i, element in enumerate(static_elements[:10], 1):  # Show first 10
                    f.write(f"{i}. {element.get('type', 'unknown').title()}\n")
                    f.write(f"   Selector: {element.get('selector', 'N/A')}\n")
                    f.write(f"   Text: {element.get('text', 'N/A')[:100]}...\n")
                    f.write(f"   Importance: {element.get('importance', 'unknown')}\n")
                    f.write("\n")
            
            # Detailed Dynamic Elements  
            dynamic_elements = site_structure.get('dynamic_elements', [])
            if dynamic_elements:
                f.write(f"DYNAMIC ELEMENTS DETAILS:\n")
                f.write("-" * 30 + "\n")
                for i, element in enumerate(dynamic_elements[:10], 1):  # Show first 10
                    f.write(f"{i}. {element.get('type', 'unknown').title()}\n")
                    f.write(f"   Selector: {element.get('selector', 'N/A')}\n")
                    f.write(f"   Tag: {element.get('tagName', 'N/A')}\n")
                    f.write(f"   Text: {element.get('text', 'N/A')[:100]}...\n")
                    f.write(f"   XPath: {element.get('xpath', 'N/A')}\n")
                    f.write(f"   Importance: {element.get('importance', 'unknown')}\n")
                    f.write("\n")
            
            f.write("\n")
            
            # Content Patterns
            f.write("CONTENT PATTERNS:\n")
            f.write("-" * 20 + "\n")
            content_patterns = spec.get('content_patterns', {})
            f.write(f"Main Content Selectors: {len(content_patterns.get('main_content_selectors', []))}\n")
            f.write(f"Navigation Patterns: {len(content_patterns.get('navigation_patterns', {}).get('main_navigation', []))}\n")
            
            # Detailed Content Selectors
            main_selectors = content_patterns.get('main_content_selectors', [])
            if main_selectors:
                f.write(f"\nMAIN CONTENT SELECTORS:\n")
                f.write("-" * 30 + "\n")
                for i, selector in enumerate(main_selectors[:5], 1):
                    f.write(f"{i}. Selector: {selector.get('selector', 'N/A')}\n")
                    f.write(f"   Type: {selector.get('type', 'unknown')}\n")
                    f.write(f"   Confidence: {selector.get('confidence', 'unknown')}\n")
                    f.write(f"   Description: {selector.get('description', 'N/A')}\n")
                    f.write("\n")
            
            # Metadata Selectors
            meta_selectors = content_patterns.get('metadata_selectors', [])
            if meta_selectors:
                f.write(f"METADATA SELECTORS:\n")
                f.write("-" * 30 + "\n")
                for i, selector in enumerate(meta_selectors[:5], 1):
                    f.write(f"{i}. Selector: {selector.get('selector', 'N/A')}\n")
                    f.write(f"   Type: {selector.get('type', 'unknown')}\n")
                    f.write(f"   Description: {selector.get('description', 'N/A')}\n")
                    f.write("\n")
            
            f.write("\n")
            
            # Dynamic Behavior
            f.write("DYNAMIC BEHAVIOR:\n")
            f.write("-" * 20 + "\n")
            dynamic = spec.get('dynamic_behavior', {})
            expandable = dynamic.get('expandable_content', {})
            f.write(f"Expandable Elements: {expandable.get('total_expandable', 0)}\n")
            f.write(f"Successful Expansions: {expandable.get('successful_expansions', 0)}\n")
            f.write(f"Nested Levels: {expandable.get('nested_levels', 0)}\n")
            
            # Content Loading Analysis
            loading_patterns = dynamic.get('content_loading_patterns', {})
            if loading_patterns:
                f.write(f"\nCONTENT LOADING ANALYSIS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Dynamic Loading Detected: {loading_patterns.get('dynamic_loading_detected', False)}\n")
                f.write(f"Mutation Count: {loading_patterns.get('mutation_count', 0)}\n")
                f.write(f"API Calls: {loading_patterns.get('api_calls', 0)}\n")
                f.write(f"Content Stability: {loading_patterns.get('content_stability', 'unknown')}\n")
            
            f.write("\n")
            
            # Technical Requirements
            f.write("TECHNICAL REQUIREMENTS:\n")
            f.write("-" * 20 + "\n")
            tech_req = spec.get('technical_requirements', {})
            browser_req = tech_req.get('browser_requirements', {})
            f.write(f"JavaScript Required: {tech_req.get('javascript_required', 'unknown')}\n")
            f.write(f"Recommended Browser: {browser_req.get('recommended_browser', 'unknown')}\n")
            f.write(f"Headless Compatible: {browser_req.get('headless_compatible', 'unknown')}\n")
            f.write(f"Service Worker: {browser_req.get('service_worker', False)}\n")
            
            # Network Dependencies
            network_deps = tech_req.get('network_dependencies', {})
            if network_deps and network_deps.get('api_endpoints'):
                f.write(f"\nNETWORK DEPENDENCIES:\n")
                f.write("-" * 30 + "\n")
                f.write(f"API Endpoints Found:\n")
                for endpoint in network_deps.get('api_endpoints', [])[:5]:
                    f.write(f"  • {endpoint}\n")
                f.write(f"Request Methods: {', '.join(network_deps.get('request_methods', []))}\n")
            
            f.write("\n")
            
            # Implementation Guide
            f.write("IMPLEMENTATION GUIDE:\n")
            f.write("-" * 20 + "\n")
            impl = spec.get('implementation_guide', {})
            f.write("Setup Steps:\n")
            for step in impl.get('setup_steps', []):
                f.write(f"  {step}\n")
            f.write("\nScraping Workflow:\n")
            for step in impl.get('scraping_workflow', []):
                f.write(f"  {step}\n")
            
            # Wait Conditions
            strategy = spec.get('scraping_strategy', {})
            wait_conditions = strategy.get('wait_conditions', [])
            if wait_conditions:
                f.write(f"\nRECOMMENDED WAIT CONDITIONS:\n")
                f.write("-" * 30 + "\n")
                for condition in wait_conditions:
                    f.write(f"• {condition.get('type', 'unknown')}: {condition.get('description', 'N/A')}\n")
                    f.write(f"  Timeout: {condition.get('timeout', 'N/A')}ms\n")
            
            f.write("\n")
            
            # Edge Cases
            f.write("EDGE CASES AND CHALLENGES:\n")
            f.write("-" * 20 + "\n")
            edge_cases = spec.get('edge_cases', [])
            if edge_cases:
                for case in edge_cases:
                    f.write(f"• {case}\n")
            else:
                f.write("• No specific edge cases detected\n")
            f.write("\n")
            
            # Error Handling Strategy
            error_handling = strategy.get('error_handling', {})
            if error_handling:
                f.write("ERROR HANDLING RECOMMENDATIONS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Interaction Failure Rate: {error_handling.get('interaction_failure_rate', 0):.1%}\n")
                f.write("Strategies:\n")
                for strategy_item in error_handling.get('recommended_strategies', []):
                    f.write(f"  • {strategy_item}\n")
                f.write("\n")
            
            # Raw Page Information (for debugging) - use structure parameter or fallback
            debug_structure = structure or spec.get('metadata', {}).get('debug_structure', {})
            raw_info = debug_structure.get('raw_page_info', {})
            if raw_info and 'error' not in raw_info:
                f.write("DEBUG INFORMATION:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Page Title: {raw_info.get('title', 'N/A')}\n")
                f.write(f"Body Text Length: {raw_info.get('body_text_length', 0)} characters\n")
                f.write(f"Total Elements: {raw_info.get('element_count', 0)}\n")
                f.write(f"Scripts: {raw_info.get('script_count', 0)}\n")
                f.write(f"Buttons: {raw_info.get('button_count', 0)}\n")
                f.write(f"Links: {raw_info.get('link_count', 0)}\n")
                f.write(f"Forms: {raw_info.get('form_count', 0)}\n")
                f.write(f"Images: {raw_info.get('image_count', 0)}\n")
                
                first_chars = raw_info.get('first_200_chars', '')
                if first_chars:
                    f.write(f"\nFirst 200 characters of page text:\n")
                    f.write(f'"{first_chars}"\n')
                
                meta_tags = raw_info.get('meta_tags', [])
                if meta_tags:
                    f.write(f"\nMeta Tags Found:\n")
                    for meta in meta_tags[:5]:  # Show first 5
                        if meta.get('name') and meta.get('content'):
                            f.write(f"  • {meta['name']}: {meta['content'][:100]}...\n")
                
                protection = debug_structure.get('protection_detected')
                if protection:
                    f.write(f"\n⚠️  BOT PROTECTION DETECTED: {protection}\n")
                
                f.write("\n")
            
            # Code Template
            f.write("CODE TEMPLATE:\n")
            f.write("-" * 20 + "\n")
            f.write(impl.get('code_template', ''))
        
        print(f"Human-readable specification saved to {filepath}") 