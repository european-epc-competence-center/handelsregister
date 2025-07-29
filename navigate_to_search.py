#!/usr/bin/env python3
"""
Script to properly navigate to search pages by following the website's session flow
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


def establish_session_and_navigate(browser):
    """Establish a proper session and try to navigate to search pages"""
    print("=== ESTABLISHING SESSION ===")

    # Start from homepage
    browser.open('https://www.handelsregister.de', timeout=10)
    print(f"Homepage loaded: {browser.title()}")
    print(f"Session URL: {browser.geturl()}")

    # Extract session info if available
    current_url = browser.geturl()
    session_match = re.search(r'jsessionid=([A-F0-9]+\.[\w]+)', current_url)
    session_id = session_match.group(1) if session_match else None
    print(f"Session ID: {session_id}")

    return session_id


def try_navigation_links(browser):
    """Try to navigate to search pages using the menu links"""
    print("\n=== TRYING NAVIGATION LINKS ===")

    # Reset to homepage
    browser.open('https://www.handelsregister.de', timeout=10)

    # Try different navigation approaches
    navigation_attempts = [
        ('Normal search link', 'Normal search'),
        ('Advanced search link', 'Advanced search'),
        ('Normale Suche', 'Normale Suche'),
        ('Erweiterte Suche', 'Erweiterte Suche'),
    ]

    successful_navigations = []

    for attempt_name, link_text in navigation_attempts:
        try:
            print(f"\nTrying {attempt_name}: '{link_text}'")
            browser.open('https://www.handelsregister.de', timeout=10)

            # Look for the link
            found_link = False
            for link in browser.links():
                if link.text and link_text.lower() in link.text.lower():
                    print(f"  Found matching link: '{
                          link.text}' -> {link.url}")
                    found_link = True

                    if link.url != '#':
                        try:
                            response = browser.follow_link(link)
                            print(f"  ✓ Successfully navigated to: {
                                  browser.geturl()}")
                            print(f"  Title: {browser.title()}")

                            # Analyze this page
                            forms_info = analyze_current_page_forms(browser)
                            successful_navigations.append({
                                'attempt': attempt_name,
                                'url': browser.geturl(),
                                'title': browser.title(),
                                'forms': forms_info
                            })
                            break

                        except Exception as e:
                            print(f"  ✗ Navigation failed: {e}")
                    else:
                        print(f"  Link points to # (JavaScript link)")

            if not found_link:
                print(f"  No matching link found for '{link_text}'")

        except Exception as e:
            print(f"  Error during navigation attempt: {e}")

    return successful_navigations


def analyze_current_page_forms(browser):
    """Analyze forms on the current page"""
    forms_info = []

    try:
        for i, form in enumerate(browser.forms()):
            form_info = {
                'index': i,
                'name': form.name,
                'action': form.action,
                'method': form.method,
                'controls': []
            }

            # Analyze controls
            for control in form.controls:
                control_info = {
                    'name': control.name,
                    'type': control.type,
                }

                # Check if it's a search-related field
                if any(keyword in control.name.lower() for keyword in ['schlagwort', 'search', 'suche', 'firma']):
                    control_info['is_search_field'] = True
                else:
                    control_info['is_search_field'] = False

                form_info['controls'].append(control_info)

            forms_info.append(form_info)

    except Exception as e:
        print(f"Error analyzing forms: {e}")

    return forms_info


def try_constructed_urls_with_session(browser, session_id):
    """Try the target URLs with proper session context"""
    print(f"\n=== TRYING CONSTRUCTED URLS WITH SESSION ===")

    if not session_id:
        print("No session ID available, trying without")
        session_param = ""
    else:
        session_param = f";jsessionid={session_id}"

    target_urls = [
        f"https://www.handelsregister.de/rp_web/normalesuche.xhtml{
            session_param}",
        f"https://www.handelsregister.de/rp_web/erweitertesuche.xhtml{
            session_param}?cid=2"
    ]

    successful_urls = []

    for url in target_urls:
        try:
            print(f"\nTrying: {url}")
            browser.open(url, timeout=10)
            print(f"✓ Success! Title: {browser.title()}")
            print(f"Final URL: {browser.geturl()}")

            # Analyze forms
            forms_info = analyze_current_page_forms(browser)
            search_forms = [f for f in forms_info if any(
                c['is_search_field'] for c in f['controls'])]

            print(f"Forms with search fields: {len(search_forms)}")
            for form in search_forms:
                search_controls = [
                    c for c in form['controls'] if c['is_search_field']]
                print(f"  Form '{form['name']}': {
                      len(search_controls)} search fields")
                for control in search_controls:
                    print(f"    - {control['name']} ({control['type']})")

            # Save the HTML
            html = browser.response().read().decode('utf-8')
            filename = f"working_search_page_{len(successful_urls)}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML saved to: {filename}")

            successful_urls.append({
                'url': url,
                'final_url': browser.geturl(),
                'title': browser.title(),
                'forms': forms_info,
                'search_forms': search_forms,
                'html_file': filename
            })

        except Exception as e:
            print(f"✗ Failed: {e}")

    return successful_urls


def main():
    print("Handelsregister.de Navigation Analysis")
    print("=" * 50)

    browser = create_browser()

    try:
        # Establish session
        session_id = establish_session_and_navigate(browser)

        # Try navigation via links
        nav_results = try_navigation_links(browser)

        # Try constructed URLs with session
        url_results = try_constructed_urls_with_session(browser, session_id)

        # Summary
        print(f"\n{'=' * 50}")
        print("NAVIGATION ANALYSIS SUMMARY")
        print(f"Successful link navigations: {len(nav_results)}")
        print(f"Successful direct URLs: {len(url_results)}")

        all_working = nav_results + url_results
        if all_working:
            print(f"\n✓ Found {len(all_working)} working approaches:")
            for i, result in enumerate(all_working):
                print(f"  {i+1}. {result.get('attempt', 'Direct URL')}")
                print(f"     URL: {result['url']}")
                if 'search_forms' in result:
                    search_count = len(result['search_forms'])
                    print(f"     Search forms: {search_count}")

        # Save comprehensive results
        results = {
            'timestamp': time.time(),
            'session_id': session_id,
            'navigation_results': nav_results,
            'url_results': url_results
        }

        with open('navigation_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: navigation_analysis.json")

    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
