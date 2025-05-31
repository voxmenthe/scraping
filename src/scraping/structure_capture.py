"""
Page structure capture module for comprehensive DOM analysis.
"""

from typing import Dict, List, Any, Optional
from .utils import ScrapingUtils


class PageStructureCapture:
    """Captures comprehensive page structure for LLM analysis."""
    
    def __init__(self):
        self.utils = ScrapingUtils()
    
    def capture_page_structure(self, page) -> Dict[str, Any]:
        """Capture comprehensive page structure for LLM analysis."""
        
        structure_data = {
            'url': page.url,
            'title': page.title(),
            'viewport': page.viewport_size,
            
            # Get full DOM structure with computed styles
            'dom_snapshot': self._capture_dom_snapshot(page),
            
            # Capture all interactive elements
            'interactive_elements': self._capture_interactive_elements(page),
            
            # Network requests made by the page
            'api_endpoints': [],  # Will be populated by network monitoring
            
            # Meta information
            'meta_info': self._capture_meta_info(page),
            
            # Content patterns
            'content_patterns': self._analyze_content_patterns(page)
        }
        
        return structure_data
    
    def _capture_dom_snapshot(self, page) -> Dict[str, Any]:
        """Capture detailed DOM structure with styles and positioning."""
        return page.evaluate("""
            () => {
                function traverseDOM(element, depth = 0) {
                    if (depth > 10) return null; // Prevent infinite recursion
                    
                    const computed = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    
                    return {
                        tagName: element.tagName,
                        id: element.id,
                        className: element.className,
                        attributes: Array.from(element.attributes).map(attr => ({
                            name: attr.name,
                            value: attr.value
                        })),
                        text: element.textContent?.trim().substring(0, 200),
                        isVisible: computed.display !== 'none' && 
                                  computed.visibility !== 'hidden' &&
                                  rect.width > 0 && rect.height > 0,
                        isExpandable: element.getAttribute('aria-expanded') !== null ||
                                     element.classList.contains('collapsible') ||
                                     element.classList.contains('expandable') ||
                                     element.querySelector('[aria-expanded]') !== null,
                        position: {
                            x: Math.round(rect.x), 
                            y: Math.round(rect.y), 
                            width: Math.round(rect.width), 
                            height: Math.round(rect.height)
                        },
                        styles: {
                            display: computed.display,
                            position: computed.position,
                            overflow: computed.overflow,
                            cursor: computed.cursor
                        },
                        children: Array.from(element.children)
                            .slice(0, 50) // Limit children to prevent excessive data
                            .map(child => traverseDOM(child, depth + 1))
                            .filter(child => child !== null)
                    };
                }
                return traverseDOM(document.body);
            }
        """)
    
    def _capture_interactive_elements(self, page) -> List[Dict[str, Any]]:
        """Capture all interactive elements on the page."""
        return page.evaluate("""
            () => {
                const selectors = [
                    'button', 'a', '[role="button"]', '[onclick]',
                    '[aria-expanded]', '.expandable', '.collapsible',
                    'details', 'summary', 'input', 'select', 'textarea',
                    '[tabindex]', '[data-toggle]', '[data-collapse]'
                ];
                
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
                
                const elements = new Set();
                const results = [];
                
                selectors.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach(el => {
                            if (!elements.has(el)) {
                                elements.add(el);
                                const rect = el.getBoundingClientRect();
                                results.push({
                                    selector: selector,
                                    tagName: el.tagName,
                                    text: el.textContent?.trim().substring(0, 100),
                                    attributes: Object.fromEntries(
                                        Array.from(el.attributes).map(attr => [attr.name, attr.value])
                                    ),
                                    xpath: getXPath(el),
                                    isVisible: rect.width > 0 && rect.height > 0,
                                    position: {
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    },
                                    interactionType: el.getAttribute('aria-expanded') !== null ? 'expandable' :
                                                    el.tagName === 'A' ? 'link' :
                                                    el.tagName === 'BUTTON' ? 'button' :
                                                    el.onclick ? 'clickable' : 'interactive'
                                });
                            }
                        });
                    } catch (e) {
                        console.warn('Error with selector:', selector, e);
                    }
                });
                
                return results;
            }
        """)
    
    def _capture_meta_info(self, page) -> Dict[str, Any]:
        """Capture meta information about the page."""
        return page.evaluate("""
            () => {
                const metas = Array.from(document.querySelectorAll('meta')).map(meta => ({
                    name: meta.getAttribute('name') || meta.getAttribute('property'),
                    content: meta.getAttribute('content')
                })).filter(meta => meta.name);
                
                const links = Array.from(document.querySelectorAll('link')).map(link => ({
                    rel: link.getAttribute('rel'),
                    href: link.getAttribute('href'),
                    type: link.getAttribute('type')
                })).filter(link => link.rel);
                
                return {
                    metas: metas,
                    links: links,
                    scripts: Array.from(document.querySelectorAll('script')).length,
                    stylesheets: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).length,
                    hasServiceWorker: 'serviceWorker' in navigator,
                    userAgent: navigator.userAgent,
                    language: document.documentElement.lang || 'unknown'
                };
            }
        """)
    
    def _analyze_content_patterns(self, page) -> Dict[str, Any]:
        """Analyze content patterns on the page."""
        return page.evaluate("""
            () => {
                // Find common content containers
                const contentSelectors = [
                    'main', 'article', '.content', '#content', '.main',
                    '.container', '.wrapper', '[role="main"]'
                ];
                
                const contentAreas = [];
                contentSelectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                contentAreas.push({
                                    selector: selector,
                                    tagName: el.tagName,
                                    textLength: el.textContent?.length || 0,
                                    childCount: el.children.length,
                                    position: {
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    }
                                });
                            }
                        });
                    } catch (e) {
                        console.warn('Error with content selector:', selector);
                    }
                });
                
                // Find navigation patterns
                const navElements = Array.from(document.querySelectorAll('nav, .nav, .navigation, [role="navigation"]'))
                    .map(nav => ({
                        tagName: nav.tagName,
                        className: nav.className,
                        linkCount: nav.querySelectorAll('a').length,
                        text: nav.textContent?.trim().substring(0, 200)
                    }));
                
                return {
                    contentAreas: contentAreas,
                    navigation: navElements,
                    headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
                        level: h.tagName,
                        text: h.textContent?.trim(),
                        id: h.id
                    })),
                    forms: Array.from(document.querySelectorAll('form')).map(form => ({
                        action: form.action,
                        method: form.method,
                        fieldCount: form.querySelectorAll('input, select, textarea').length
                    }))
                };
            }
        """)
    
    def identify_static_elements(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify elements that are likely static (non-dynamic)."""
        static_elements = []
        
        def analyze_element(element):
            if not element or not isinstance(element, dict):
                return
                
            # Consider static if:
            # - No dynamic attributes
            # - Not expandable
            # - Simple content container
            is_static = (
                not element.get('isExpandable', False) and
                element.get('isVisible', False) and
                not any(attr.get('name', '').startswith('data-') 
                       for attr in element.get('attributes', []))
            )
            
            if is_static:
                static_elements.append({
                    'tagName': element.get('tagName'),
                    'id': element.get('id'),
                    'className': element.get('className'),
                    'text': element.get('text', '')[:100],
                    'position': element.get('position')
                })
            
            # Recursively analyze children
            for child in element.get('children', []):
                analyze_element(child)
        
        if 'dom_snapshot' in structure:
            analyze_element(structure['dom_snapshot'])
        
        return static_elements
    
    def identify_dynamic_elements(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify elements that are likely dynamic."""
        dynamic_elements = []
        
        # Extract from interactive elements
        for element in structure.get('interactive_elements', []):
            if element.get('interactionType') in ['expandable', 'clickable']:
                dynamic_elements.append(element)
        
        return dynamic_elements 