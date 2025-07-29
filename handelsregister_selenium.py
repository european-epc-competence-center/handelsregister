#!/usr/bin/env python3
"""
Selenium-based handelsregister CLI - handles JavaScript navigation
This replaces the mechanize-based approach with browser automation
to work with the modern handelsregister.de website.
"""

import argparse
import sys
import pathlib
import time
import json
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Dictionaries to map arguments to values (same as original)
schlagwortOptionen = {
    "all": 1,
    "min": 2,
    "exact": 3
}


class HandelsRegisterSelenium:
    def __init__(self, args):
        if not SELENIUM_AVAILABLE:
            raise ImportError(
                "Selenium is required for this script. Install with: pip install selenium\n"
                "You'll also need to install a browser driver (e.g., chromedriver)"
            )

        self.args = args
        self.driver = None
        self.wait = None

        self.cachedir = pathlib.Path("cache")
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def setup_driver(self):
        """Set up the Selenium WebDriver"""
        chrome_options = Options()

        # Add options for better automation
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Run headless if not in debug mode
        if not self.args.debug:
            chrome_options.add_argument("--headless")
            # Set a proper window size for headless mode
            chrome_options.add_argument("--window-size=1920,1080")
            # Disable GPU acceleration issues in headless mode
            chrome_options.add_argument("--disable-gpu")

        # Add user agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"
        )

        try:
            # Use webdriver-manager to automatically handle chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)

            # Remove webdriver property to appear more human-like
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to start Chrome WebDriver: {e}\n"
                "Make sure you have Chrome installed. Chromedriver will be downloaded automatically."
            )

    def open_startpage(self):
        """Navigate to the handelsregister homepage"""
        if self.args.debug:
            print("Opening handelsregister.de homepage...")

        self.driver.get("https://www.handelsregister.de")

        if self.args.debug:
            print(f"Page title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")

    def navigate_to_advanced_search(self):
        """Navigate to the advanced search page using JavaScript links"""
        if self.args.debug:
            print("Navigating to advanced search...")

        # Longer timeout for headless mode
        timeout = 15 if not self.args.debug else 10
        wait = WebDriverWait(self.driver, timeout)

        try:
            # Wait for page to fully load first
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional wait for dynamic content

            # Wait for and click the advanced search link
            advanced_search_link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Advanced search"))
            )

            if self.args.debug:
                print("Found 'Advanced search' link, clicking...")

            # Scroll to element to ensure it's visible
            self.driver.execute_script(
                "arguments[0].scrollIntoView();", advanced_search_link)
            time.sleep(1)

            advanced_search_link.click()

            # Wait for the page to load
            time.sleep(3)

            if self.args.debug:
                print(f"Advanced search page loaded: {self.driver.title}")
                print(f"Current URL: {self.driver.current_url}")

            return True

        except TimeoutException:
            # Try German version
            try:
                advanced_search_link = wait.until(
                    EC.element_to_be_clickable(
                        (By.LINK_TEXT, "Erweiterte Suche"))
                )

                if self.args.debug:
                    print("Found 'Erweiterte Suche' link, clicking...")

                # Scroll to element to ensure it's visible
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", advanced_search_link)
                time.sleep(1)

                advanced_search_link.click()
                time.sleep(3)

                if self.args.debug:
                    print(f"Advanced search page loaded: {self.driver.title}")

                return True

            except TimeoutException:
                if self.args.debug:
                    print("Could not find advanced search link")
                    print(f"Page source length: {
                          len(self.driver.page_source)}")
                    print(f"Available links: {
                          [link.text for link in self.driver.find_elements(By.TAG_NAME, 'a')]}")
                return False

    def companyname2cachename(self, companyname):
        """Map a companyname to a cache filename"""
        return self.cachedir / f"{companyname}_selenium"

    def search_company(self):
        """Perform the company search using Selenium"""
        cachename = self.companyname2cachename(self.args.schlagwoerter)

        if not self.args.force and cachename.exists():
            with open(cachename, "r") as f:
                html = f.read()
                print(f"Return cached content for {self.args.schlagwoerter}")
                return get_companies_in_searchresults(html)

        try:
            # Set up the browser
            self.setup_driver()

            # Open homepage
            self.open_startpage()

            # Navigate to advanced search
            if not self.navigate_to_advanced_search():
                raise RuntimeError(
                    "Could not navigate to advanced search page")

            # Find and fill the search form
            search_success = self.fill_search_form()
            if not search_success:
                raise RuntimeError("Could not find or fill search form")

            # Submit the form and get results
            if not self.submit_search_form():
                raise RuntimeError("Could not submit search form")

            # Wait for results page to load
            time.sleep(3)

            if self.args.debug:
                print(f"Results page loaded: {self.driver.title}")
                print(f"Results URL: {self.driver.current_url}")

            # Get the results HTML
            html = self.driver.page_source

            # Cache the results
            with open(cachename, "w") as f:
                f.write(html)

            return get_companies_in_searchresults(html)

        finally:
            if self.driver:
                self.driver.quit()

    def fill_search_form(self):
        """Find and fill the search form"""
        if self.args.debug:
            print("Looking for search form...")

        # Wait a bit for the page to fully load
        time.sleep(2)

        try:
            # Try different possible field names for the search input
            # Prioritize the correct JSF field names we found in the HTML
            search_field_selectors = [
                # The correct company search field
                "textarea[name='form:schlagwoerter']",
                "input[name='form:schlagwoerter']",
                "textarea[name*='schlagwort']",
                "input[name*='schlagwort']",
                "textarea[name*='search']",
                "input[name*='search']",
                "textarea[name*='suche']",
                "input[name*='suche']",
                "textarea[name*='firma']",
                "input[name*='firma']",
                "textarea[name*='company']",
                "input[name*='company']"
            ]

            search_field = None
            for selector in search_field_selectors:
                try:
                    # Wait for element to be present and visible
                    search_field = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if self.args.debug:
                        print(f"Found search field with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not search_field:
                if self.args.debug:
                    print("Could not find search field, trying by ID...")
                # Try some common IDs
                common_ids = ['form:schlagwoerter',
                              'schlagwoerter', 'search', 'suche', 'query']
                for field_id in common_ids:
                    try:
                        search_field = self.wait.until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        if self.args.debug:
                            print(f"Found search field with ID: {field_id}")
                        break
                    except TimeoutException:
                        continue

            if not search_field:
                if self.args.debug:
                    print("Search field not found. Available form elements:")
                    forms = self.driver.find_elements(By.TAG_NAME, "form")
                    for i, form in enumerate(forms):
                        inputs = form.find_elements(By.TAG_NAME, "input")
                        print(f"Form {i}: {len(inputs)} inputs")
                        for inp in inputs:
                            name = inp.get_attribute("name")
                            input_type = inp.get_attribute("type")
                            visible = inp.is_displayed()
                            enabled = inp.is_enabled()
                            print(f"  {input_type}: name='{name}' visible={
                                  visible} enabled={enabled}")
                return False

            # Make sure field is ready and fill it
            if self.args.debug:
                print(f"Search field found: name='{search_field.get_attribute('name')}', visible={
                      search_field.is_displayed()}, enabled={search_field.is_enabled()}")

            # Scroll to element and click to focus
            self.driver.execute_script(
                "arguments[0].scrollIntoView();", search_field)
            time.sleep(0.5)
            search_field.click()

            # Clear and fill the search field
            search_field.clear()
            search_field.send_keys(self.args.schlagwoerter)

            if self.args.debug:
                print(f"Filled search field with: {self.args.schlagwoerter}")
                print(f"Field value after filling: {
                      search_field.get_attribute('value')}")

            # Handle search options if available
            try:
                option_selectors = [
                    "select[name*='option']",
                    "select[name*='schlagwort']",
                    "input[type='radio']"
                ]

                for selector in option_selectors:
                    try:
                        option_element = self.driver.find_element(
                            By.CSS_SELECTOR, selector)
                        if selector.startswith("select"):
                            # Handle dropdown
                            select = Select(option_element)
                            option_value = schlagwortOptionen.get(
                                self.args.schlagwortOptionen, 1)
                            try:
                                select.select_by_value(str(option_value))
                            except:
                                select.select_by_index(option_value - 1)

                            if self.args.debug:
                                print(f"Set search option to: {
                                      self.args.schlagwortOptionen}")
                        break
                    except NoSuchElementException:
                        continue

            except Exception as e:
                if self.args.debug:
                    print(f"Could not set search options: {e}")

            return True

        except Exception as e:
            if self.args.debug:
                print(f"Error filling search form: {e}")
            return False

    def submit_search_form(self):
        """Submit the search form"""
        if self.args.debug:
            print("Submitting search form...")

        try:
            # Try to find and click submit button
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button[name*='search']",
                "input[value*='suchen']",
                "input[value*='search']"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    if self.args.debug:
                        print(f"Found submit button with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not submit_button:
                if self.args.debug:
                    print(
                        "No submit button found, trying form submission via Enter key")
                # Find any form and submit it
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    # Submit the first form
                    self.driver.execute_script(
                        "arguments[0].submit();", forms[0])
                else:
                    return False
            else:
                # Click the submit button
                submit_button.click()

            if self.args.debug:
                print("Search form submitted")

            return True

        except Exception as e:
            if self.args.debug:
                print(f"Error submitting form: {e}")
            return False


def get_companies_in_searchresults(html):
    """Parse companies from search results HTML (same as original)"""
    soup = BeautifulSoup(html, 'html.parser')

    # Try to find results table
    grid = soup.find('table', role='grid')
    if not grid:
        # Try alternative patterns
        grid = soup.find('table', class_='results')
        if not grid:
            grid = soup.find('div', class_='search-results')

    if not grid:
        print("No results table found")
        return []

    results = []
    rows = grid.find_all('tr')

    for result in rows:
        data_ri = result.get('data-ri')
        if data_ri is not None:
            try:
                index = int(data_ri)
                company_info = parse_result(result)
                if company_info:
                    results.append(company_info)
            except (ValueError, TypeError):
                continue

    return results


def parse_result(result):
    """Parse a single result row (adapted from original)"""
    try:
        cells = []
        for cell in result.find_all('td'):
            cells.append(cell.text.strip())

        if len(cells) < 5:
            return None

        company_info = {
            'court': cells[1] if len(cells) > 1 else '',
            'name': cells[2] if len(cells) > 2 else '',
            'state': cells[3] if len(cells) > 3 else '',
            'status': cells[4] if len(cells) > 4 else '',
            'documents': cells[5] if len(cells) > 5 else '',
            'history': []
        }

        # Parse history if available
        hist_start = 8
        if len(cells) > hist_start:
            for i in range(hist_start, len(cells), 3):
                if i + 1 < len(cells):
                    company_info['history'].append((cells[i], cells[i+1]))

        return company_info

    except Exception as e:
        print(f"Error parsing result: {e}")
        return None


def pr_company_info(company):
    """Print company information (same as original)"""
    for tag in ('name', 'court', 'state', 'status'):
        print(f'{tag}: {company.get(tag, "-")}')

    print('history:')
    for name, loc in company.get('history', []):
        print(f'  {name} {loc}')


def parse_args():
    """Parse command line arguments (same as original)"""
    parser = argparse.ArgumentParser(
        description='A handelsregister CLI using Selenium browser automation'
    )
    parser.add_argument(
        "-d", "--debug",
        help="Enable debug mode and activate logging",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--force",
        help="Force a fresh pull and skip the cache",
        action="store_true"
    )
    parser.add_argument(
        "-s", "--schlagwoerter",
        help="Search for the provided keywords",
        required=True,
        default="Gasag AG"
    )
    parser.add_argument(
        "-so", "--schlagwortOptionen",
        help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
        choices=["all", "min", "exact"],
        default="all"
    )

    args = parser.parse_args()

    if args.debug:
        print("Debug mode enabled - browser will run in non-headless mode")

    return args


if __name__ == "__main__":
    if not SELENIUM_AVAILABLE:
        print("Error: Selenium is not installed.")
        print("Install with: pip install selenium")
        print("Also install chromedriver: https://chromedriver.chromium.org/")
        sys.exit(1)

    args = parse_args()

    try:
        h = HandelsRegisterSelenium(args)
        companies = h.search_company()

        if companies:
            print(f"Found {len(companies)} companies:")
            for company in companies:
                pr_company_info(company)
                print("-" * 40)
        else:
            print("No companies found")

    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
