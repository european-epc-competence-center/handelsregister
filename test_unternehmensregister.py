#!/usr/bin/env python3
"""
Test script to check if unternehmensregister.de can be used as an alternative
to handelsregister.de for automated company searches using mechanize.
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

def analyze_homepage(browser):
    """Analyze the unternehmensregister.de homepage"""
    print("=== ANALYZING UNTERNEHMENSREGISTER.DE HOMEPAGE ===")
    
    url = "https://www.unternehmensregister.de/ureg/"
    browser.open(url, timeout=10)
    
    print(f"Title: {browser.title()}")
    print(f"URL: {browser.geturl()}")
    
    # Analyze forms
    print(f"\nForms found:")
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
            print(f"    {control.type}: name='{control.name}' id='{getattr(control, 'id', 'N/A')}'")
            
            # Check if this looks like a search field
            control_name_lower = control.name.lower() if control.name else ''
            if any(keyword in control_name_lower for keyword in ['search', 'suche', 'query', 'firma', 'company', 'unternehmen']):
                search_controls.append({
                    'name': control.name,
                    'type': control.type,
                    'id': getattr(control, 'id', 'N/A')
                })
        
        if search_controls:
            print(f"  >>> SEARCH CONTROLS FOUND: {len(search_controls)}")
            search_forms.append({
                'form_index': i,
                'form_name': form.name,
                'form_action': form.action,
                'search_controls': search_controls
            })
    
    return search_forms

def test_search_functionality(browser, search_term="european epc competence center"):
    """Test if we can perform a search"""
    print(f"\n=== TESTING SEARCH FUNCTIONALITY ===")
    print(f"Search term: '{search_term}'")
    
    url = "https://www.unternehmensregister.de/ureg/"
    browser.open(url, timeout=10)
    
    # Try to find and use search forms
    search_attempts = []
    
    for i, form in enumerate(browser.forms()):
        # Look for search fields in this form
        search_field = None
        for control in form.controls:
            if control.type in ['text', 'search']:
                control_name_lower = control.name.lower() if control.name else ''
                if any(keyword in control_name_lower for keyword in ['search', 'suche', 'query', 'firma', 'company', 'unternehmen']):
                    search_field = control.name
                    break
        
        if search_field:
            try:
                print(f"\nTesting form {i} (name: {form.name})")
                print(f"Search field: {search_field}")
                
                browser.select_form(nr=i)
                browser[search_field] = search_term
                
                print("Submitting search...")
                response = browser.submit()
                
                print(f"✓ Search submitted successfully!")
                print(f"Result URL: {browser.geturl()}")
                print(f"Result title: {browser.title()}")
                
                # Analyze results
                html = response.read().decode('utf-8')
                results_info = analyze_search_results(html)
                
                search_attempts.append({
                    'form_index': i,
                    'form_name': form.name,
                    'search_field': search_field,
                    'success': True,
                    'result_url': browser.geturl(),
                    'results_info': results_info
                })
                
                # Save the result HTML for inspection
                with open('unternehmensregister_results.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print("Results HTML saved to: unternehmensregister_results.html")
                
                return True, search_attempts
                
            except Exception as e:
                print(f"✗ Search failed: {e}")
                search_attempts.append({
                    'form_index': i,
                    'form_name': form.name,
                    'search_field': search_field,
                    'success': False,
                    'error': str(e)
                })
    
    return False, search_attempts

def analyze_search_results(html):
    """Analyze the search results HTML"""
    print("\n=== ANALYZING SEARCH RESULTS ===")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for common result patterns
    results_info = {
        'total_results': 0,
        'company_entries': [],
        'result_patterns': []
    }
    
    # Look for result counts
    result_count_patterns = [
        r'(\d+)\s*(?:Treffer|Ergebnisse|Results)',
        r'Gefunden:\s*(\d+)',
        r'(\d+)\s*Unternehmen'
    ]
    
    for pattern in result_count_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            results_info['total_results'] = int(match.group(1))
            print(f"Found {results_info['total_results']} results")
            break
    
    # Look for company entries
    # Common patterns for company listings
    company_patterns = [
        'table[role="grid"]',
        '.result-item',
        '.company-entry',
        '.search-result',
        'tr[data-ri]'  # This was the pattern from handelsregister.de
    ]
    
    for pattern in company_patterns:
        elements = soup.select(pattern)
        if elements:
            print(f"Found {len(elements)} elements matching pattern: {pattern}")
            results_info['result_patterns'].append({
                'pattern': pattern,
                'count': len(elements)
            })
            
            # Try to extract company info from first few results
            for i, element in enumerate(elements[:3]):
                company_info = extract_company_info(element)
                if company_info:
                    results_info['company_entries'].append(company_info)
                    print(f"Company {i+1}: {company_info}")
    
    return results_info

def extract_company_info(element):
    """Extract company information from a result element"""
    try:
        # Try to extract text content and look for company-like patterns
        text = element.get_text(strip=True)
        
        # Look for typical company information patterns
        company_info = {
            'text': text[:200] + "..." if len(text) > 200 else text,
            'links': []
        }
        
        # Extract any links
        links = element.find_all('a')
        for link in links:
            if link.get('href') and link.get_text(strip=True):
                company_info['links'].append({
                    'text': link.get_text(strip=True),
                    'href': link.get('href')
                })
        
        return company_info if company_info['text'] else None
        
    except Exception as e:
        print(f"Error extracting company info: {e}")
        return None

def try_advanced_search(browser):
    """Try to find and use advanced search functionality"""
    print("\n=== TESTING ADVANCED SEARCH ===")
    
    url = "https://www.unternehmensregister.de/ureg/"
    browser.open(url, timeout=10)
    
    # Look for advanced search links
    advanced_search_links = []
    for link in browser.links():
        if link.text and any(keyword in link.text.lower() for keyword in ['erweiterte', 'advanced', 'extended']):
            advanced_search_links.append(link)
            print(f"Found advanced search link: '{link.text}' -> {link.url}")
    
    # Try to follow advanced search links
    for link in advanced_search_links:
        try:
            if link.url and link.url != '#':
                print(f"\nTrying advanced search link: {link.text}")
                response = browser.follow_link(link)
                print(f"Advanced search page loaded: {browser.title()}")
                print(f"URL: {browser.geturl()}")
                
                # Analyze forms on advanced search page
                advanced_forms = []
                for i, form in enumerate(browser.forms()):
                    print(f"\nAdvanced form {i}:")
                    print(f"  Name: {form.name}")
                    print(f"  Action: {form.action}")
                    
                    search_controls = []
                    for control in form.controls:
                        if control.type in ['text', 'search', 'select']:
                            control_name_lower = control.name.lower() if control.name else ''
                            if any(keyword in control_name_lower for keyword in ['search', 'suche', 'firma', 'company', 'unternehmen', 'name']):
                                search_controls.append(control.name)
                                print(f"    Search control: {control.name} ({control.type})")
                    
                    if search_controls:
                        advanced_forms.append({
                            'form_index': i,
                            'form_name': form.name,
                            'search_controls': search_controls
                        })
                
                return True, advanced_forms
                
        except Exception as e:
            print(f"Failed to access advanced search: {e}")
    
    return False, []

def main():
    print("Unternehmensregister.de Compatibility Test")
    print("=" * 50)
    
    browser = create_browser()
    
    results = {
        'timestamp': time.time(),
        'homepage_analysis': None,
        'search_test': None,
        'advanced_search': None,
        'compatible': False,
        'recommended_approach': None
    }
    
    try:
        # Analyze homepage
        search_forms = analyze_homepage(browser)
        results['homepage_analysis'] = {
            'search_forms_found': len(search_forms),
            'forms': search_forms
        }
        
        # Test search functionality
        search_success, search_attempts = test_search_functionality(browser)
        results['search_test'] = {
            'success': search_success,
            'attempts': search_attempts
        }
        
        # Try advanced search
        advanced_success, advanced_forms = try_advanced_search(browser)
        results['advanced_search'] = {
            'success': advanced_success,
            'forms': advanced_forms
        }
        
        # Determine compatibility
        results['compatible'] = search_success or advanced_success
        
        if results['compatible']:
            results['recommended_approach'] = "mechanize with unternehmensregister.de"
        else:
            results['recommended_approach'] = "browser automation (Selenium/Playwright)"
        
        # Summary
        print(f"\n{'=' * 50}")
        print("COMPATIBILITY TEST SUMMARY")
        print(f"Homepage search forms: {len(search_forms)}")
        print(f"Search test successful: {'YES' if search_success else 'NO'}")
        print(f"Advanced search available: {'YES' if advanced_success else 'NO'}")
        print(f"Overall compatible: {'YES' if results['compatible'] else 'NO'}")
        print(f"Recommended approach: {results['recommended_approach']}")
        
        if results['compatible']:
            print(f"\n✓ Great news! unternehmensregister.de appears to be compatible with mechanize!")
            print("This can be used as a drop-in replacement for handelsregister.de")
        else:
            print(f"\n✗ unternehmensregister.de also requires browser automation")
        
        # Save results
        with open('unternehmensregister_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: unternehmensregister_test_results.json")
        
        return results['compatible']
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    compatible = main()
    sys.exit(0 if compatible else 1)