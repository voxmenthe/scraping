"""
Content monitoring module for tracking dynamic content changes.
"""

import time
from typing import Dict, List, Any, Optional, Callable


class ContentMonitor:
    """Monitors and tracks dynamic content changes on web pages."""
    
    def __init__(self):
        self.content_timeline = []
        self.mutation_log = []
        self.api_calls = []
        self.monitoring_active = False
    
    def start_monitoring(self, page, monitor_network: bool = True):
        """Start monitoring content changes and network requests."""
        self.monitoring_active = True
        
        # Set up mutation observer for DOM changes
        self._setup_mutation_observer(page)
        
        # Set up network monitoring if requested
        if monitor_network:
            self._setup_network_monitoring(page)
        
        print("Content monitoring started")
    
    def stop_monitoring(self, page) -> Dict[str, Any]:
        """Stop monitoring and return collected data."""
        self.monitoring_active = False
        
        # Retrieve mutation log from page
        mutations = self._retrieve_mutations(page)
        
        monitoring_data = {
            'mutations': mutations,
            'api_calls': self.api_calls,
            'timeline': self.content_timeline,
            'monitoring_duration': len(self.content_timeline),
            'summary': self._generate_monitoring_summary(mutations)
        }
        
        print(f"Content monitoring stopped. Collected {len(mutations)} mutations and {len(self.api_calls)} API calls")
        
        return monitoring_data
    
    def monitor_dynamic_content(self, page, interaction_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Monitor content as it loads dynamically with optional interactions."""
        
        # Start monitoring
        self.start_monitoring(page)
        
        # Take initial snapshot
        initial_snapshot = self._capture_content_snapshot(page, "initial")
        
        # Perform interactions if callback provided
        if interaction_callback:
            print("Performing interactions while monitoring...")
            try:
                interaction_callback(page)
            except Exception as e:
                print(f"Error during interactions: {e}")
        
        # Wait for content to settle
        self._wait_for_content_stability(page)
        
        # Take final snapshot
        final_snapshot = self._capture_content_snapshot(page, "final")
        
        # Stop monitoring and collect data
        monitoring_data = self.stop_monitoring(page)
        
        # Add snapshots to monitoring data
        monitoring_data['snapshots'] = {
            'initial': initial_snapshot,
            'final': final_snapshot
        }
        
        # Analyze content changes
        monitoring_data['content_analysis'] = self._analyze_content_changes(
            initial_snapshot, final_snapshot, monitoring_data['mutations']
        )
        
        return monitoring_data
    
    def _setup_mutation_observer(self, page):
        """Set up mutation observer to track DOM changes."""
        page.evaluate("""
            () => {
                window.contentChanges = [];
                window.mutationStartTime = Date.now();
                
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        window.contentChanges.push({
                            type: mutation.type,
                            target: {
                                tagName: mutation.target.tagName,
                                id: mutation.target.id,
                                className: mutation.target.className,
                                textContent: mutation.target.textContent?.substring(0, 100)
                            },
                            timestamp: Date.now() - window.mutationStartTime,
                            addedNodes: Array.from(mutation.addedNodes).map(node => ({
                                nodeType: node.nodeType,
                                tagName: node.tagName,
                                textContent: node.textContent?.substring(0, 50)
                            })),
                            removedNodes: Array.from(mutation.removedNodes).map(node => ({
                                nodeType: node.nodeType,
                                tagName: node.tagName,
                                textContent: node.textContent?.substring(0, 50)
                            })),
                            attributeName: mutation.attributeName,
                            oldValue: mutation.oldValue
                        });
                    });
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeOldValue: true,
                    characterData: true,
                    characterDataOldValue: true
                });
                
                window.mutationObserver = observer;
            }
        """)
    
    def _setup_network_monitoring(self, page):
        """Set up network request monitoring."""
        def handle_request(request):
            request_info = {
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'timestamp': time.time(),
                'resource_type': request.resource_type
            }
            
            # Track API-like requests
            if any(keyword in request.url.lower() for keyword in ['api', 'ajax', 'json', 'graphql']):
                self.api_calls.append(request_info)
        
        def handle_response(response):
            # You could also track responses here
            pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
    
    def _retrieve_mutations(self, page) -> List[Dict[str, Any]]:
        """Retrieve mutation log from the page."""
        try:
            return page.evaluate("window.contentChanges || []")
        except Exception as e:
            print(f"Error retrieving mutations: {e}")
            return []
    
    def _capture_content_snapshot(self, page, snapshot_type: str) -> Dict[str, Any]:
        """Capture a snapshot of page content at a specific time."""
        timestamp = time.time()
        
        snapshot = {
            'type': snapshot_type,
            'timestamp': timestamp,
            'url': page.url,
            'title': page.title(),
            'content_metrics': self._get_content_metrics(page),
            'visible_elements': self._get_visible_elements(page)
        }
        
        self.content_timeline.append(snapshot)
        return snapshot
    
    def _get_content_metrics(self, page) -> Dict[str, Any]:
        """Get quantitative metrics about page content."""
        return page.evaluate("""
            () => {
                const textNodes = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.trim().length > 0) {
                        textNodes.push(node);
                    }
                }
                
                return {
                    totalElements: document.querySelectorAll('*').length,
                    visibleElements: Array.from(document.querySelectorAll('*')).filter(el => {
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }).length,
                    textNodes: textNodes.length,
                    totalTextLength: textNodes.reduce((sum, node) => sum + node.textContent.length, 0),
                    links: document.querySelectorAll('a').length,
                    buttons: document.querySelectorAll('button').length,
                    inputs: document.querySelectorAll('input, select, textarea').length,
                    images: document.querySelectorAll('img').length,
                    scripts: document.querySelectorAll('script').length,
                    pageHeight: document.body.scrollHeight,
                    viewportHeight: window.innerHeight
                };
            }
        """)
    
    def _get_visible_elements(self, page) -> List[Dict[str, Any]]:
        """Get information about currently visible elements."""
        return page.evaluate("""
            () => {
                const visibleElements = [];
                const elements = document.querySelectorAll('*');
                
                for (let i = 0; i < Math.min(elements.length, 100); i++) {
                    const el = elements[i];
                    const rect = el.getBoundingClientRect();
                    
                    if (rect.width > 10 && rect.height > 10 && rect.top < window.innerHeight) {
                        visibleElements.push({
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className,
                            textContent: el.textContent?.trim().substring(0, 100),
                            position: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            zIndex: window.getComputedStyle(el).zIndex
                        });
                    }
                }
                
                return visibleElements;
            }
        """)
    
    def _wait_for_content_stability(self, page, max_wait: int = 10000, stability_duration: int = 2000):
        """Wait for content to stabilize (no changes for a specified duration)."""
        stable_start = time.time()
        last_mutation_count = 0
        
        while (time.time() - stable_start) * 1000 < max_wait:
            current_mutations = len(self._retrieve_mutations(page))
            
            if current_mutations == last_mutation_count:
                # No new mutations, check if we've been stable long enough
                time.sleep(0.5)
                if (time.time() - stable_start) * 1000 >= stability_duration:
                    print("Content appears stable")
                    break
            else:
                # New mutations detected, reset stability timer
                stable_start = time.time()
                last_mutation_count = current_mutations
                time.sleep(0.1)
    
    def _analyze_content_changes(self, initial_snapshot: Dict[str, Any], 
                                final_snapshot: Dict[str, Any], 
                                mutations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the changes that occurred during monitoring."""
        
        initial_metrics = initial_snapshot.get('content_metrics', {})
        final_metrics = final_snapshot.get('content_metrics', {})
        
        changes = {}
        for key in initial_metrics:
            if key in final_metrics:
                change = final_metrics[key] - initial_metrics[key]
                if change != 0:
                    changes[key] = {
                        'initial': initial_metrics[key],
                        'final': final_metrics[key],
                        'change': change
                    }
        
        # Analyze mutation patterns
        mutation_types = {}
        target_elements = {}
        
        for mutation in mutations:
            mut_type = mutation.get('type', 'unknown')
            mutation_types[mut_type] = mutation_types.get(mut_type, 0) + 1
            
            target = mutation.get('target', {})
            target_tag = target.get('tagName', 'unknown')
            target_elements[target_tag] = target_elements.get(target_tag, 0) + 1
        
        return {
            'content_metric_changes': changes,
            'mutation_analysis': {
                'total_mutations': len(mutations),
                'mutation_types': mutation_types,
                'affected_elements': target_elements,
                'timeline_span': mutations[-1].get('timestamp', 0) - mutations[0].get('timestamp', 0) if mutations else 0
            },
            'significant_changes': self._identify_significant_changes(changes, mutations)
        }
    
    def _identify_significant_changes(self, changes: Dict[str, Any], mutations: List[Dict[str, Any]]) -> List[str]:
        """Identify the most significant content changes."""
        significant = []
        
        # Check for major content additions
        if 'totalElements' in changes and changes['totalElements']['change'] > 10:
            significant.append(f"Added {changes['totalElements']['change']} new elements")
        
        if 'totalTextLength' in changes and changes['totalTextLength']['change'] > 1000:
            significant.append(f"Added {changes['totalTextLength']['change']} characters of text")
        
        # Check for new interactive elements
        if 'buttons' in changes and changes['buttons']['change'] > 0:
            significant.append(f"Added {changes['buttons']['change']} new buttons")
        
        if 'links' in changes and changes['links']['change'] > 0:
            significant.append(f"Added {changes['links']['change']} new links")
        
        # Check for layout changes
        if 'pageHeight' in changes and abs(changes['pageHeight']['change']) > 500:
            significant.append(f"Page height changed by {changes['pageHeight']['change']}px")
        
        return significant
    
    def _generate_monitoring_summary(self, mutations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the monitoring session."""
        if not mutations:
            return {'total_mutations': 0, 'activity_level': 'none'}
        
        # Calculate activity level
        mutation_count = len(mutations)
        time_span = mutations[-1].get('timestamp', 0) - mutations[0].get('timestamp', 0)
        
        if time_span > 0:
            mutations_per_second = mutation_count / (time_span / 1000)
        else:
            mutations_per_second = 0
        
        activity_level = (
            'high' if mutations_per_second > 5 else
            'medium' if mutations_per_second > 1 else
            'low'
        )
        
        return {
            'total_mutations': mutation_count,
            'time_span_ms': time_span,
            'mutations_per_second': round(mutations_per_second, 2),
            'activity_level': activity_level,
            'api_calls_detected': len(self.api_calls)
        } 