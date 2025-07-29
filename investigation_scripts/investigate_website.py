#!/usr/bin/env python3
"""
Diagnostic script to investigate handelsregister.de website structure
This script checks for forms, links, and current page structure to help
fix the mechanize form selection issue.
"""

import mechanize
import sys
from bs4 import BeautifulSoup
import time
import json

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

def investigate_homepage(browser):
    """Investigate the homepage structure"""
    print("=== HOMEPAGE INVESTIGATION ===")
    browser.open('https://www.handelsregister.de', timeout=10)
    print(f"Title: {browser.title()}")
    print(f"URL: {browser.geturl()}")
    
    # Check for forms
    print("\nForms on homepage:")
    forms_found = False
    for i, form in enumerate(browser.forms()):
        forms_found = True
        print(f"Form {i}:")
        print(f"  Name: {form.name}")
        print(f"  Action: {form.action}")
        print(f"  Method: {form.method}")
        print("  Controls:")
        for control in form.controls:
            print(f"    {control.type}: name='{control.name}' id='{getattr(control, 'id', 'N/A')}'")
    
    if not forms_found:
        print("  No forms found via mechanize")
    
    # Check HTML source for forms
    html = browser.response().read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\nForms in HTML source:")
    forms = soup.find_all('form')
    for i, form in enumerate(forms):
        print(f"Form {i}:")
        print(f"  ID: {form.get('id')}")
        print(f"  Name: {form.get('name')}")
        print(f"  Action: {form.get('action')}")
        print(f"  Method: {form.get('method')}")
        
        inputs = form.find_all(['input', 'select', 'textarea'])
        if inputs:
            print("  Input fields:")
            for inp in inputs:
                print(f"    {inp.name}: name='{inp.get('name')}' id='{inp.get('id')}' type='{inp.get('type')}'")
    
    return html

def investigate_links(browser):
    """Find all available links, especially search-related ones"""
    print("\n=== LINKS INVESTIGATION ===")
    
    search_related_links = []
    all_links = []
    
    for link in browser.links():
        link_info = {
            'text': link.text.strip() if link.text else '',
            'url': link.url,
            'absolute_url': link.absolute_url
        }
        all_links.append(link_info)
        
        # Check if it's search related
        text_lower = link_info['text'].lower()
        url_lower = link_info['url'].lower()
        
        if any(keyword in text_lower for keyword in ['search', 'suche', 'erweiterte', 'advanced']):
            search_related_links.append(link_info)
        elif any(keyword in url_lower for keyword in ['search', 'suche', 'erweiterte', 'advanced']):
            search_related_links.append(link_info)
    
    print("Search-related links found:")
    for link in search_related_links:
        print(f"  '{link['text']}' -> {link['url']}")
    
    return search_related_links, all_links

def try_advanced_search_navigation(browser):
    """Try different ways to navigate to advanced search"""
    print("\n=== ADVANCED SEARCH NAVIGATION ===")
    
    navigation_attempts = [
        ('German text', 'Erweiterte Suche'),
        ('English text', 'Advanced search'),
        ('Partial German', 'erweiterte'),
        ('Partial English', 'advanced'),
    ]
    
    for attempt_name, link_text in navigation_attempts:
        try:
            print(f"\nTrying {attempt_name}: '{link_text}'")
            # Return to homepage first
            browser.open('https://www.handelsregister.de', timeout=10)
            
            response = browser.follow_link(text=link_text)
            print(f"  SUCCESS! Title: {browser.title()}")
            print(f"  URL: {browser.geturl()}")
            
            # Check forms on this page
            print("  Forms found:")
            for i, form in enumerate(browser.forms()):
                print(f"    Form {i}: name='{form.name}' action='{form.action}'")
                
            return True, browser.geturl()
            
        except mechanize.LinkNotFoundError:
            print(f"  Failed: Link not found")
        except Exception as e:
            print(f"  Failed: {e}")
    
    return False, None

def try_direct_urls(browser):
    """Try common advanced search URLs directly"""
    print("\n=== DIRECT URL ATTEMPTS ===")
    
    possible_urls = [
        'https://www.handelsregister.de/rp_web/erweitertesuche.xhtml',
        'https://www.handelsregister.de/rp_web/search.xhtml', 
        'https://www.handelsregister.de/rp_web/erweiterte_suche.xhtml',
        'https://www.handelsregister.de/rp_web/advanced_search.xhtml',
        'https://www.handelsregister.de/rp_web/suche.xhtml',
        'https://www.handelsregister.de/rp_web/normalsuche.xhtml',
        'https://www.handelsregister.de/rp_web/normalesuche.xhtml',
    ]
    
    working_urls = []
    
    for url in possible_urls:
        try:
            print(f"\nTrying URL: {url}")
            browser.open(url, timeout=10)
            print(f"  SUCCESS! Title: {browser.title()}")
            print(f"  Final URL: {browser.geturl()}")
            
            # Check forms
            forms_found = False
            for i, form in enumerate(browser.forms()):
                forms_found = True
                print(f"  Form {i}: name='{form.name}' action='{form.action}'")
                
                # Look for search-related controls
                for control in form.controls:
                    if 'schlagwort' in control.name.lower() or 'search' in control.name.lower():
                        print(f"    Search field found: {control.name}")
            
            if not forms_found:
                print("  No forms found")
                
            working_urls.append(url)
            
        except Exception as e:
            print(f"  Failed: {e}")
    
    return working_urls

def save_results(results):
    """Save investigation results to a file"""
    with open('website_investigation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to website_investigation_results.json")

def main():
    print("Handelsregister.de Website Structure Investigation")
    print("=" * 50)
    
    browser = create_browser()
    results = {
        'timestamp': time.time(),
        'homepage_forms': [],
        'search_links': [],
        'working_urls': [],
        'navigation_success': False,
        'final_url': None
    }
    
    try:
        # Investigate homepage
        homepage_html = investigate_homepage(browser)
        
        # Find links
        search_links, all_links = investigate_links(browser)
        results['search_links'] = search_links
        
        # Try navigation
        nav_success, final_url = try_advanced_search_navigation(browser)
        results['navigation_success'] = nav_success
        results['final_url'] = final_url
        
        # Try direct URLs
        working_urls = try_direct_urls(browser)
        results['working_urls'] = working_urls
        
        print("\n" + "=" * 50)
        print("SUMMARY:")
        print(f"Search-related links found: {len(search_links)}")
        print(f"Navigation to advanced search: {'SUCCESS' if nav_success else 'FAILED'}")
        print(f"Working direct URLs: {len(working_urls)}")
        
        if working_urls:
            print("Working URLs:")
            for url in working_urls:
                print(f"  - {url}")
        
        save_results(results)
        
    except Exception as e:
        print(f"Investigation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()