#!/usr/bin/env python3
"""
Script to examine the website's JavaScript and find actual form submission endpoints
that might work with mechanize
"""

import mechanize
import sys
from bs4 import BeautifulSoup
import time
import json
import re

def create_browser():
    """Create a mechanize browser with the same settings as the main script"""
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.set_handle_equiv(True)
    browser.set_handle_gzip(True)
    browser.set_handle_refresh(False)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)

    browser.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15'),
        ('Accept-Language', 'en-GB,en;q=0.9'),
        ('Accept-Encoding', 'gzip, deflate, br'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Connection', 'keep-alive'),
    ]
    return browser

def extract_javascript_urls(html):
    """Extract URLs and form actions from JavaScript code"""
    print("=== EXTRACTING JAVASCRIPT URLS ===")
    
    # Look for URL patterns in JavaScript
    url_patterns = [
        r'["\']([^"\']*(?:suche|search)[^"\']*\.xhtml[^"\']*)["\']',
        r'url\s*:\s*["\']([^"\']+)["\']',
        r'action\s*:\s*["\']([^"\']+)["\']',
        r'location\.href\s*=\s*["\']([^"\']+)["\']',
        r'window\.open\s*\(\s*["\']([^"\']+)["\']',
    ]
    
    found_urls = set()
    
    for pattern in url_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            if 'suche' in match.lower() or 'search' in match.lower():
                found_urls.add(match)
    
    print(f"Found {len(found_urls)} potential search URLs in JavaScript:")
    for url in sorted(found_urls):
        print(f"  {url}")
    
    return list(found_urls)

def examine_form_actions(browser):
    """Examine all form actions and hidden fields"""
    print("\n=== EXAMINING FORM ACTIONS ===")
    
    browser.open('https://www.handelsregister.de', timeout=10)
    
    # Get all forms and their potential actions
    form_actions = []
    
    for i, form in enumerate(browser.forms()):
        action_info = {
            'index': i,
            'name': form.name,
            'action': form.action,
            'method': form.method,
            'hidden_fields': [],
            'potential_search_triggers': []
        }
        
        # Examine all controls
        for control in form.controls:
            if control.type == 'hidden':
                action_info['hidden_fields'].append({
                    'name': control.name,
                    'value': getattr(control, 'value', '')
                })
            elif control.type in ['submit', 'button']:
                action_info['potential_search_triggers'].append({
                    'name': control.name,
                    'type': control.type,
                    'value': getattr(control, 'value', '')
                })
        
        form_actions.append(action_info)
    
    print(f"Found {len(form_actions)} forms:")
    for form in form_actions:
        print(f"\nForm {form['index']} ({form['name']}):")
        print(f"  Action: {form['action']}")
        print(f"  Method: {form['method']}")
        print(f"  Hidden fields: {len(form['hidden_fields'])}")
        print(f"  Submit buttons: {len(form['potential_search_triggers'])}")
        
        # Show relevant hidden fields
        for hf in form['hidden_fields']:
            if 'faces' in hf['name'].lower() or 'view' in hf['name'].lower():
                print(f"    Hidden: {hf['name']} = {hf['value'][:50]}...")
    
    return form_actions

def try_alternative_endpoints(browser):
    """Try alternative search endpoints"""
    print("\n=== TRYING ALTERNATIVE ENDPOINTS ===")
    
    # First establish session
    browser.open('https://www.handelsregister.de', timeout=10)
    base_url = browser.geturl()
    
    # Extract base path and session if available
    base_match = re.match(r'(https://[^/]+/[^/]+/[^/]+)/', base_url)
    base_path = base_match.group(1) if base_match else 'https://www.handelsregister.de/rp_web'
    
    session_match = re.search(r'jsessionid=([^&?]+)', base_url)
    session_id = session_match.group(1) if session_match else None
    
    # Alternative endpoints to try
    alternative_urls = [
        f"{base_path}/search.xhtml",
        f"{base_path}/suche.xhtml", 
        f"{base_path}/register_search.xhtml",
        f"{base_path}/company_search.xhtml",
        f"{base_path}/firmen_suche.xhtml",
    ]
    
    if session_id:
        alternative_urls.extend([
            f"{base_path}/normalesuche.xhtml;jsessionid={session_id}",
            f"{base_path}/erweitertesuche.xhtml;jsessionid={session_id}",
        ])
    
    working_endpoints = []
    
    for url in alternative_urls:
        try:
            print(f"\nTrying: {url}")
            browser.open(url, timeout=5)
            print(f"  ✓ Success! Title: {browser.title()}")
            
            # Check for search forms
            search_forms = 0
            for form in browser.forms():
                for control in form.controls:
                    if any(keyword in control.name.lower() for keyword in ['schlagwort', 'search', 'firma']):
                        search_forms += 1
                        break
            
            print(f"  Search forms: {search_forms}")
            working_endpoints.append({
                'url': url,
                'title': browser.title(),
                'search_forms': search_forms
            })
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    return working_endpoints

def check_post_endpoints(browser):
    """Check if we can POST directly to known endpoints"""
    print("\n=== CHECKING POST ENDPOINTS ===")
    
    # First get a session
    browser.open('https://www.handelsregister.de', timeout=10)
    
    # Try to find JSF endpoint patterns
    html = browser.response().read().decode('utf-8')
    
    # Look for form actions
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')
    
    post_endpoints = []
    
    for form in forms:
        action = form.get('action', '')
        if action and action != '#':
            post_endpoints.append(action)
    
    print(f"Found {len(post_endpoints)} POST endpoints:")
    for endpoint in post_endpoints:
        print(f"  {endpoint}")
    
    # Try posting a search to these endpoints
    search_attempts = []
    
    for endpoint in post_endpoints:
        try:
            if endpoint.startswith('/'):
                full_url = f"https://www.handelsregister.de{endpoint}"
            else:
                full_url = endpoint
            
            print(f"\nTrying POST to: {full_url}")
            
            # Get viewstate and other required fields
            browser.open('https://www.handelsregister.de', timeout=10)
            
            viewstate = None
            for form in browser.forms():
                for control in form.controls:
                    if 'viewstate' in control.name.lower():
                        viewstate = control.value
                        break
                if viewstate:
                    break
            
            if viewstate:
                print(f"  Found ViewState: {viewstate[:50]}...")
                
                # Try a simple POST with search data
                data = {
                    'javax.faces.ViewState': viewstate,
                    'schlagwoerter': 'test search'
                }
                
                # This would require more complex handling...
                print("  POST test would require complex JSF handling")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    return post_endpoints

def main():
    print("Handelsregister.de Form Endpoints Investigation")
    print("=" * 60)
    
    browser = create_browser()
    
    try:
        # Get homepage HTML
        browser.open('https://www.handelsregister.de', timeout=10)
        html = browser.response().read().decode('utf-8')
        
        # Extract JavaScript URLs
        js_urls = extract_javascript_urls(html)
        
        # Examine form actions
        form_actions = examine_form_actions(browser)
        
        # Try alternative endpoints
        working_endpoints = try_alternative_endpoints(browser)
        
        # Check POST endpoints
        post_endpoints = check_post_endpoints(browser)
        
        # Summary
        print(f"\n{'=' * 60}")
        print("INVESTIGATION SUMMARY")
        print(f"JavaScript URLs found: {len(js_urls)}")
        print(f"Forms analyzed: {len(form_actions)}")
        print(f"Working endpoints: {len(working_endpoints)}")
        print(f"POST endpoints: {len(post_endpoints)}")
        
        if working_endpoints:
            print(f"\n✓ Working endpoints found:")
            for ep in working_endpoints:
                print(f"  {ep['url']} - {ep['search_forms']} search forms")
        
        # Save results
        results = {
            'timestamp': time.time(),
            'javascript_urls': js_urls,
            'form_actions': form_actions,
            'working_endpoints': working_endpoints,
            'post_endpoints': post_endpoints
        }
        
        with open('form_endpoints_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: form_endpoints_analysis.json")
        
    except Exception as e:
        print(f"Investigation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()