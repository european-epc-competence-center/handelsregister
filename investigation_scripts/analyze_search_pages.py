#!/usr/bin/env python3
"""
Script to analyze the specific search pages on handelsregister.de
Using the URLs provided: normalesuche.xhtml and erweitertesuche.xhtml?cid=2
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

def analyze_search_page(browser, url, page_name):
    """Analyze a specific search page"""
    print(f"\n=== ANALYZING {page_name.upper()} ===")
    print(f"URL: {url}")
    
    try:
        browser.open(url, timeout=10)
        print(f"Title: {browser.title()}")
        print(f"Final URL: {browser.geturl()}")
        
        # Analyze forms
        print(f"\nForms found on {page_name}:")
        search_forms = []
        
        for i, form in enumerate(browser.forms()):
            print(f"\nForm {i}:")
            print(f"  Name: {form.name}")
            print(f"  Action: {form.action}")
            print(f"  Method: {form.method}")
            
            # Look for search-related controls
            search_controls = []
            print("  Controls:")
            for control in form.controls:
                control_info = {
                    'name': control.name,
                    'type': control.type,
                    'id': getattr(control, 'id', 'N/A')
                }
                
                # Try to get value if available
                try:
                    control_info['value'] = getattr(control, 'value', 'N/A')
                except:
                    control_info['value'] = 'N/A'
                
                print(f"    {control.type}: name='{control.name}' id='{control_info['id']}' value='{control_info['value']}'")
                
                # Check if this looks like a search field
                if any(keyword in control.name.lower() for keyword in ['schlagwort', 'search', 'suche', 'firma', 'company']):
                    search_controls.append(control_info)
            
            if search_controls:
                print(f"  >>> SEARCH CONTROLS FOUND: {len(search_controls)}")
                search_forms.append({
                    'form_index': i,
                    'form_name': form.name,
                    'form_action': form.action,
                    'search_controls': search_controls
                })
        
        # Save HTML for manual inspection
        html = browser.response().read().decode('utf-8')
        filename = f"{page_name.replace(' ', '_').lower()}_page.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\nHTML saved to: {filename}")
        
        return search_forms
        
    except Exception as e:
        print(f"Error analyzing {page_name}: {e}")
        return []

def test_form_submission(browser, url, page_name):
    """Test if we can submit a search form"""
    print(f"\n=== TESTING FORM SUBMISSION FOR {page_name.upper()} ===")
    
    try:
        browser.open(url, timeout=10)
        
        # Look for forms with search fields
        for i, form in enumerate(browser.forms()):
            has_search_field = False
            search_field_name = None
            
            for control in form.controls:
                if any(keyword in control.name.lower() for keyword in ['schlagwort', 'search', 'suche']):
                    has_search_field = True
                    search_field_name = control.name
                    break
            
            if has_search_field:
                print(f"\nTesting form {i} (name: {form.name})")
                print(f"Search field: {search_field_name}")
                
                try:
                    browser.select_form(nr=i)
                    browser[search_field_name] = "test search"
                    
                    print("Form submission test...")
                    # Don't actually submit, just see if we can fill the form
                    print("✓ Form can be selected and filled")
                    return True, i, form.name, search_field_name
                    
                except Exception as e:
                    print(f"✗ Form submission test failed: {e}")
        
        print("No suitable search forms found for testing")
        return False, None, None, None
        
    except Exception as e:
        print(f"Error testing form submission: {e}")
        return False, None, None, None

def main():
    print("Handelsregister.de Search Pages Analysis")
    print("=" * 50)
    
    browser = create_browser()
    
    # URLs to analyze
    search_pages = [
        ('https://www.handelsregister.de/rp_web/normalesuche.xhtml', 'Normal Search'),
        ('https://www.handelsregister.de/rp_web/erweitertesuche.xhtml?cid=2', 'Advanced Search')
    ]
    
    results = {
        'timestamp': time.time(),
        'pages_analyzed': []
    }
    
    for url, page_name in search_pages:
        # Analyze the page structure
        search_forms = analyze_search_page(browser, url, page_name)
        
        # Test form submission
        can_submit, form_index, form_name, search_field = test_form_submission(browser, url, page_name)
        
        page_result = {
            'url': url,
            'name': page_name,
            'search_forms': search_forms,
            'can_submit': can_submit,
            'working_form_index': form_index,
            'working_form_name': form_name,
            'search_field_name': search_field
        }
        
        results['pages_analyzed'].append(page_result)
        
        print(f"\n{page_name} Analysis Summary:")
        print(f"  Forms with search fields: {len(search_forms)}")
        print(f"  Can submit search: {'YES' if can_submit else 'NO'}")
        if can_submit:
            print(f"  Working form: {form_name} (index {form_index})")
            print(f"  Search field: {search_field}")
    
    # Save results
    with open('search_pages_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 50}")
    print("ANALYSIS COMPLETE")
    print("Results saved to: search_pages_analysis.json")
    print("HTML files saved for manual inspection")
    
    # Summary
    working_pages = [p for p in results['pages_analyzed'] if p['can_submit']]
    if working_pages:
        print(f"\n✓ Found {len(working_pages)} working search page(s):")
        for page in working_pages:
            print(f"  - {page['name']}: {page['url']}")
            print(f"    Form: {page['working_form_name']} (field: {page['search_field_name']})")
    else:
        print("\n✗ No working search pages found")

if __name__ == "__main__":
    main()