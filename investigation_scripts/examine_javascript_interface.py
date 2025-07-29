#!/usr/bin/env python3
"""
Script to examine JavaScript interface and understand how the advanced search works
This will help us find the correct way to access search functionality.
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

def examine_page_javascript(browser):
    """Examine the JavaScript and find clues about search functionality"""
    print("=== JAVASCRIPT AND AJAX ANALYSIS ===")
    
    browser.open('https://www.handelsregister.de', timeout=10)
    html = browser.response().read().decode('utf-8')
    
    # Look for JavaScript patterns
    print("Looking for JavaScript patterns...")
    
    # Find script tags
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    search_related_js = []
    for script in scripts:
        if script.string:
            script_content = script.string.lower()
            if any(keyword in script_content for keyword in ['search', 'suche', 'form', 'ajax', 'submit']):
                search_related_js.append(script.string[:500] + "..." if len(script.string) > 500 else script.string)
    
    print(f"Found {len(search_related_js)} search-related JavaScript snippets")
    for i, js in enumerate(search_related_js):
        print(f"\nScript {i}:")
        print(js)
    
    # Look for AJAX endpoints
    ajax_patterns = re.findall(r'url\s*:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
    print(f"\nFound {len(ajax_patterns)} potential AJAX URLs:")
    for url in ajax_patterns:
        if 'search' in url.lower() or 'suche' in url.lower():
            print(f"  Search-related: {url}")
    
    return html

def examine_form_submission_patterns(browser):
    """Look for form submission patterns and JSF specifics"""
    print("\n=== JSF FORM SUBMISSION ANALYSIS ===")
    
    browser.open('https://www.handelsregister.de', timeout=10)
    html = browser.response().read().decode('utf-8')
    
    # Look for JSF patterns
    jsf_patterns = [
        r'javax\.faces\..*',
        r'jsf\.ajax\..*',
        r'PrimeFaces\..*',
        r'mojarra\..*'
    ]
    
    found_patterns = []
    for pattern in jsf_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            found_patterns.extend(matches)
    
    print(f"JSF-related patterns found: {len(found_patterns)}")
    for pattern in set(found_patterns):
        print(f"  {pattern}")
    
    # Look for ViewState and other JSF hidden fields
    soup = BeautifulSoup(html, 'html.parser')
    viewstate_fields = soup.find_all('input', {'name': re.compile(r'.*ViewState.*')})
    print(f"\nViewState fields found: {len(viewstate_fields)}")
    for field in viewstate_fields:
        print(f"  {field.get('name')} (length: {len(field.get('value', ''))})")

def try_menu_navigation(browser):
    """Try to find the actual search page through menu navigation"""
    print("\n=== MENU NAVIGATION ANALYSIS ===")
    
    browser.open('https://www.handelsregister.de', timeout=10)
    
    # Try to find and click menu items
    try:
        # Look for any links that might lead to search
        all_links = []
        for link in browser.links():
            if link.url and link.url != '#':
                all_links.append((link.text.strip(), link.url))
        
        print("Non-hash links found:")
        for text, url in all_links:
            print(f"  '{text}' -> {url}")
            
        # Try following some promising links
        promising_texts = ['Normal search', 'Normale Suche', 'search', 'suche']
        for text in promising_texts:
            try:
                browser.open('https://www.handelsregister.de', timeout=10)
                response = browser.follow_link(text=text)
                print(f"\nFollowed '{text}' -> {browser.geturl()}")
                print(f"Title: {browser.title()}")
                
                # Check for forms on this page
                forms_with_search = []
                for i, form in enumerate(browser.forms()):
                    has_search_field = False
                    for control in form.controls:
                        if 'schlagwort' in control.name.lower() or 'search' in control.name.lower():
                            has_search_field = True
                            break
                    if has_search_field:
                        forms_with_search.append((i, form))
                
                if forms_with_search:
                    print(f"Found {len(forms_with_search)} forms with search fields!")
                    for i, form in forms_with_search:
                        print(f"  Form {i}: name='{form.name}' action='{form.action}'")
                        for control in form.controls:
                            if 'schlagwort' in control.name.lower() or 'search' in control.name.lower():
                                print(f"    Search field: {control.name}")
                
            except mechanize.LinkNotFoundError:
                continue
            except Exception as e:
                print(f"Error following '{text}': {e}")
                continue
                
    except Exception as e:
        print(f"Menu navigation failed: {e}")

def save_detailed_html(browser):
    """Save the full HTML for manual examination"""
    print("\n=== SAVING DETAILED HTML ===")
    
    browser.open('https://www.handelsregister.de', timeout=10)
    html = browser.response().read().decode('utf-8')
    
    with open('handelsregister_homepage.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Homepage HTML saved to handelsregister_homepage.html")
    
    # Try to navigate to advanced search and save that too
    try:
        response = browser.follow_link(text='Advanced search')
        html_advanced = browser.response().read().decode('utf-8')
        
        with open('handelsregister_advanced_search.html', 'w', encoding='utf-8') as f:
            f.write(html_advanced)
        print("Advanced search HTML saved to handelsregister_advanced_search.html")
        
    except Exception as e:
        print(f"Could not save advanced search HTML: {e}")

def main():
    print("Handelsregister.de JavaScript Interface Analysis")
    print("=" * 50)
    
    browser = create_browser()
    
    try:
        # Examine JavaScript
        examine_page_javascript(browser)
        
        # Examine JSF patterns
        examine_form_submission_patterns(browser)
        
        # Try menu navigation
        try_menu_navigation(browser)
        
        # Save HTML for manual examination
        save_detailed_html(browser)
        
        print("\n" + "=" * 50)
        print("ANALYSIS COMPLETE")
        print("Check the saved HTML files for manual examination")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()