"""
Dynamic content handler for expandable/collapsible elements.
"""

import time
from typing import Dict, List, Any, Optional
from .utils import ScrapingUtils


class DynamicContentHandler:
    """Handles interaction with expandable/collapsible content."""
    
    def __init__(self):
        self.utils = ScrapingUtils()
        self.expanded_states = {}
    
    def explore_expandable_content(self, page) -> Dict[str, Any]:
        """Systematically expand all collapsible sections."""
        
        # Find all expandable elements
        expandables = self._find_expandable_elements(page)
        
        print(f"Found {len(expandables)} expandable elements")
        
        for element_info in expandables:
            element_id = self._generate_element_id(element_info)
            
            # Capture state before expansion
            self.expanded_states[element_id] = {
                'element_info': element_info,
                'collapsed_content': self._capture_element_content(page, element_info),
                'expanded_content': None,
                'interaction_result': None,
                'errors': []
            }
            
            # Attempt to expand the element
            try:
                interaction_result = self._expand_element(page, element_info)
                self.expanded_states[element_id]['interaction_result'] = interaction_result
                
                if interaction_result['success']:
                    # Wait for content to settle
                    self.utils.wait_for_content_settlement(page)
                    
                    # Capture expanded state
                    expanded_content = self._capture_element_content(page, element_info)
                    self.expanded_states[element_id]['expanded_content'] = expanded_content
                    
                    # Check for newly revealed expandable elements
                    new_expandables = self._find_nested_expandables(page, element_info)
                    if new_expandables:
                        # Recursively handle nested expandables (limited depth)
                        nested_results = self._handle_nested_expandables(page, new_expandables, depth=1)
                        self.expanded_states[element_id]['nested_expandables'] = nested_results
                        
            except Exception as e:
                error_msg = f"Error expanding element {element_id}: {str(e)}"
                self.expanded_states[element_id]['errors'].append(error_msg)
                print(f"Warning: {error_msg}")
        
        return self.expanded_states
    
    def _find_expandable_elements(self, page) -> List[Dict[str, Any]]:
        """Find all expandable elements on the page."""
        return page.evaluate("""
            () => {
                const expandableSelectors = [
                    '[aria-expanded="false"]',
                    '[aria-expanded="true"]',
                    'details:not([open])',
                    '.expandable:not(.expanded)',
                    '.collapsible:not(.expanded)',
                    '.accordion-header',
                    '[data-toggle="collapse"]',
                    '[data-bs-toggle="collapse"]',
                    '.dropdown-toggle:not(.show)',
                    '[role="button"][aria-expanded]'
                ];
                
                const elements = [];
                const seenElements = new Set();
                
                expandableSelectors.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach(el => {
                            if (!seenElements.has(el)) {
                                seenElements.add(el);
                                const rect = el.getBoundingClientRect();
                                
                                // Only include visible elements
                                if (rect.width > 0 && rect.height > 0) {
                                    elements.push({
                                        selector: selector,
                                        tagName: el.tagName,
                                        id: el.id,
                                        className: el.className,
                                        text: el.textContent?.trim().substring(0, 100),
                                        ariaExpanded: el.getAttribute('aria-expanded'),
                                        attributes: Object.fromEntries(
                                            Array.from(el.attributes)
                                                .filter(attr => attr.name.startsWith('data-') || 
                                                               attr.name.startsWith('aria-') ||
                                                               ['id', 'class', 'role'].includes(attr.name))
                                                .map(attr => [attr.name, attr.value])
                                        ),
                                        position: {
                                            x: Math.round(rect.x),
                                            y: Math.round(rect.y),
                                            width: Math.round(rect.width),
                                            height: Math.round(rect.height)
                                        },
                                        isCurrentlyExpanded: el.getAttribute('aria-expanded') === 'true' ||
                                                           el.hasAttribute('open') ||
                                                           el.classList.contains('expanded') ||
                                                           el.classList.contains('show')
                                    });
                                }
                            }
                        });
                    } catch (e) {
                        console.warn('Error with expandable selector:', selector, e);
                    }
                });
                
                return elements;
            }
        """)
    
    def _capture_element_content(self, page, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """Capture the current content of an element."""
        try:
            return page.evaluate("""
                (elementInfo) => {
                    let element = null;
                    
                    // Try to find element by ID first
                    if (elementInfo.id) {
                        element = document.getElementById(elementInfo.id);
                    }
                    
                    // Fall back to other methods
                    if (!element) {
                        // Try by className and tagName
                        const candidates = document.querySelectorAll(
                            elementInfo.tagName + (elementInfo.className ? '.' + elementInfo.className.replace(/\\s+/g, '.') : '')
                        );
                        
                        // Find the one that matches our text content
                        for (let candidate of candidates) {
                            if (candidate.textContent?.trim().includes(elementInfo.text?.substring(0, 50))) {
                                element = candidate;
                                break;
                            }
                        }
                    }
                    
                    if (!element) {
                        return { error: 'Element not found' };
                    }
                    
                    return {
                        innerHTML: element.innerHTML,
                        textContent: element.textContent?.trim(),
                        attributes: Object.fromEntries(
                            Array.from(element.attributes).map(attr => [attr.name, attr.value])
                        ),
                        childElementCount: element.childElementCount,
                        scrollHeight: element.scrollHeight,
                        clientHeight: element.clientHeight
                    };
                }
            """, element_info)
        except Exception as e:
            return {'error': f'Failed to capture content: {str(e)}'}
    
    def _expand_element(self, page, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to expand an element."""
        result = {
            'success': False,
            'method_used': None,
            'error': None,
            'content_changed': False
        }
        
        try:
            # Get content before interaction
            content_before = self._capture_element_content(page, element_info)
            
            # Try different expansion methods
            expansion_result = page.evaluate("""
                (elementInfo) => {
                    let element = null;
                    
                    // Find the element
                    if (elementInfo.id) {
                        element = document.getElementById(elementInfo.id);
                    }
                    
                    if (!element) {
                        const candidates = document.querySelectorAll(
                            elementInfo.tagName + (elementInfo.className ? '.' + elementInfo.className.replace(/\\s+/g, '.') : '')
                        );
                        
                        for (let candidate of candidates) {
                            if (candidate.textContent?.trim().includes(elementInfo.text?.substring(0, 50))) {
                                element = candidate;
                                break;
                            }
                        }
                    }
                    
                    if (!element) {
                        return { success: false, error: 'Element not found' };
                    }
                    
                    try {
                        // Method 1: Click the element
                        element.click();
                        return { success: true, method: 'click' };
                        
                    } catch (e1) {
                        try {
                            // Method 2: Set aria-expanded
                            if (element.hasAttribute('aria-expanded')) {
                                element.setAttribute('aria-expanded', 'true');
                                element.dispatchEvent(new Event('change', { bubbles: true }));
                                return { success: true, method: 'aria-expanded' };
                            }
                            
                            // Method 3: Add open attribute for details
                            if (element.tagName === 'DETAILS') {
                                element.open = true;
                                return { success: true, method: 'details-open' };
                            }
                            
                            // Method 4: Trigger data-toggle behavior
                            if (element.hasAttribute('data-toggle') || element.hasAttribute('data-bs-toggle')) {
                                element.dispatchEvent(new Event('click', { bubbles: true }));
                                return { success: true, method: 'data-toggle' };
                            }
                            
                            return { success: false, error: 'No suitable expansion method found' };
                            
                        } catch (e2) {
                            return { success: false, error: e2.message };
                        }
                    }
                }
            """, element_info)
            
            result.update(expansion_result)
            
            if result['success']:
                # Wait for changes to take effect
                time.sleep(0.5)
                
                # Check if content actually changed
                content_after = self._capture_element_content(page, element_info)
                result['content_changed'] = content_before != content_after
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _find_nested_expandables(self, page, parent_element_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find expandable elements that may have been revealed after expanding a parent."""
        try:
            return page.evaluate("""
                (parentInfo) => {
                    let parentElement = null;
                    
                    // Find parent element
                    if (parentInfo.id) {
                        parentElement = document.getElementById(parentInfo.id);
                    }
                    
                    if (!parentElement) {
                        return [];
                    }
                    
                    // Look for new expandable elements within the parent
                    const nestedSelectors = [
                        '[aria-expanded="false"]',
                        'details:not([open])',
                        '.expandable:not(.expanded)',
                        '.collapsible:not(.expanded)'
                    ];
                    
                    const nestedElements = [];
                    
                    nestedSelectors.forEach(selector => {
                        parentElement.querySelectorAll(selector).forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                nestedElements.push({
                                    selector: selector,
                                    tagName: el.tagName,
                                    id: el.id,
                                    className: el.className,
                                    text: el.textContent?.trim().substring(0, 100),
                                    ariaExpanded: el.getAttribute('aria-expanded'),
                                    position: {
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    }
                                });
                            }
                        });
                    });
                    
                    return nestedElements;
                }
            """, parent_element_info)
        except Exception as e:
            print(f"Error finding nested expandables: {e}")
            return []
    
    def _handle_nested_expandables(self, page, nested_elements: List[Dict[str, Any]], depth: int = 1, max_depth: int = 3) -> Dict[str, Any]:
        """Handle nested expandable elements with limited recursion depth."""
        if depth > max_depth:
            return {'skipped': 'Max depth reached'}
        
        nested_results = {}
        
        for element_info in nested_elements[:5]:  # Limit to 5 nested elements per level
            element_id = self._generate_element_id(element_info)
            
            try:
                interaction_result = self._expand_element(page, element_info)
                nested_results[element_id] = {
                    'element_info': element_info,
                    'interaction_result': interaction_result,
                    'depth': depth
                }
                
                if interaction_result['success']:
                    self.utils.wait_for_content_settlement(page, max_wait_time=3000)
                    
            except Exception as e:
                nested_results[element_id] = {
                    'error': str(e),
                    'depth': depth
                }
        
        return nested_results
    
    def _generate_element_id(self, element_info: Dict[str, Any]) -> str:
        """Generate a unique ID for an element."""
        if element_info.get('id'):
            return f"id_{element_info['id']}"
        
        parts = [
            element_info.get('tagName', 'unknown'),
            element_info.get('className', '').replace(' ', '_'),
            str(hash(element_info.get('text', '')[:50]))[:8]
        ]
        
        return "_".join(filter(None, parts))
    
    def get_expansion_summary(self) -> Dict[str, Any]:
        """Get a summary of all expansion operations."""
        summary = {
            'total_elements': len(self.expanded_states),
            'successful_expansions': 0,
            'failed_expansions': 0,
            'content_changes': 0,
            'nested_discoveries': 0,
            'expansion_methods': {}
        }
        
        for element_id, state in self.expanded_states.items():
            if state.get('interaction_result', {}).get('success'):
                summary['successful_expansions'] += 1
                
                # Track expansion methods
                method = state['interaction_result'].get('method_used', 'unknown')
                summary['expansion_methods'][method] = summary['expansion_methods'].get(method, 0) + 1
                
                if state['interaction_result'].get('content_changed'):
                    summary['content_changes'] += 1
            else:
                summary['failed_expansions'] += 1
            
            if 'nested_expandables' in state:
                summary['nested_discoveries'] += len(state['nested_expandables'])
        
        return summary 