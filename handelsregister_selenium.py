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
import re
import os
import requests
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

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

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

        if args.download_pdfs and not PDF_AVAILABLE:
            raise ImportError(
                "PyPDF2 is required for PDF processing. Install with: pip install PyPDF2"
            )

        self.args = args
        self.driver = None
        self.wait = None

        self.cachedir = pathlib.Path("cache")
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def setup_driver(self):
        """Set up the Selenium WebDriver"""
        chrome_options = Options()

        # Configure download directory to current working directory
        download_dir = os.path.abspath(".")
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True  # Don't open PDF in browser
        }
        chrome_options.add_experimental_option("prefs", prefs)

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

        if not self.args.force and cachename.exists() and not self.args.download_pdfs:
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

            # Parse companies from results
            companies = get_companies_in_searchresults(html)

            # Download documents if requested
            if self.args.download_pdfs and companies:
                print(f"PDF download enabled, processing {
                      len(companies)} companies...")
                for i, company in enumerate(companies):
                    print(f"Processing company {
                          i+1}/{len(companies)}: {company.get('name', 'Unknown')}")
                    processed_company = self.download_company_documents(
                        company)
                    if processed_company:  # Only update if processing succeeded
                        companies[i] = processed_company

            return companies

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

    def download_company_documents(self, company):
        """Download PDF documents for a company and extract information"""
        if not PDF_AVAILABLE:
            print("Warning: PyPDF2 not available, skipping document processing")
            return company

        if not company.get('document_links'):
            print(f"No document links found for {
                  company.get('name', 'Unknown')}")
            return company

        company['extracted_data'] = {}

        for doc_link in company['document_links']:
            # Only process 'AD' documents (Aktuelle Daten / Current Data)
            if doc_link['type'] == 'AD':
                try:
                    print(f"Processing {doc_link['type']} document for {
                          company.get('name', 'Unknown')}")
                    pdf_path = self.download_pdf_document(doc_link, company)
                    if pdf_path:
                        extracted_data = self.extract_pdf_content(pdf_path)
                        if extracted_data:
                            company['extracted_data'] = extracted_data
                            print(f"Successfully extracted data from {
                                  doc_link['type']} document")
                        break  # Stop after first successful AD document
                except Exception as e:
                    print(f"Error processing document {doc_link['type']}: {e}")
                    continue

                return company

    def download_pdf_document(self, doc_link, company):
        """Download a PDF document by clicking the link"""
        try:
            # Find the document link on the current page
            link_element = self.driver.find_element(By.ID, doc_link['id'])

            # Execute the onclick JavaScript to trigger the download
            if doc_link['onclick']:
                onclick = doc_link['onclick']

                if self.args.debug:
                    print(f"Executing onclick: {onclick[:100]}...")

                # Store current URL to detect navigation
                current_url_before = self.driver.current_url

                # Store page source before to detect changes
                page_source_before = self.driver.page_source[:1000]

                # Execute the onclick JavaScript
                self.driver.execute_script(onclick)

                # Wait for potential navigation or content change
                time.sleep(5)

                # Check if URL changed (form submission likely caused navigation)
                current_url_after = self.driver.current_url
                page_source_after = self.driver.page_source[:1000]

                if self.args.debug:
                    print(f"URL before: {current_url_before}")
                    print(f"URL after: {current_url_after}")
                    print(f"Page title: {self.driver.title}")
                    print(f"Page content changed: {
                          page_source_before != page_source_after}")

                    # Check for PDF-related content in page
                    if 'pdf' in self.driver.page_source.lower():
                        print("Found 'pdf' text in page source")
                    if '%PDF' in self.driver.page_source:
                        print("Found PDF magic bytes in page source!")

                    # Check response headers if possible
                    try:
                        logs = self.driver.get_log('performance')
                        for log in logs[-5:]:  # Check last 5 network events
                            message = json.loads(log['message'])
                            if 'Network.responseReceived' in message.get('method', ''):
                                response = message.get(
                                    'params', {}).get('response', {})
                                headers = response.get('headers', {})
                                content_type = headers.get(
                                    'content-type', headers.get('Content-Type', ''))
                                if 'pdf' in content_type.lower():
                                    print(f"Found PDF response: {
                                          content_type}")
                                    print(f"Response URL: {
                                          response.get('url', '')}")
                    except:
                        pass

                # Check if we're now on a PDF page
                if current_url_after.endswith('.pdf') or 'pdf' in current_url_after.lower():
                    return self.download_pdf_from_url(current_url_after, doc_link['type'], company)

                # Look for PDF content in various ways
                pdf_url = None

                # Method 1: Look for PDF links or iframes
                pdf_elements = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, '.pdf')] | //iframe[contains(@src, '.pdf')] | //embed[contains(@src, '.pdf')]")
                if pdf_elements:
                    pdf_url = pdf_elements[0].get_attribute(
                        'href') or pdf_elements[0].get_attribute('src')
                    if self.args.debug:
                        print(f"Found PDF element with URL: {pdf_url}")

                # Method 2: Check if content-type indicates PDF
                if not pdf_url:
                    try:
                        # Try to detect if the current page is serving PDF content
                        page_source = self.driver.page_source
                        if 'application/pdf' in page_source or '%PDF' in page_source:
                            pdf_url = current_url_after
                            if self.args.debug:
                                print(
                                    "Current page appears to be serving PDF content")
                    except:
                        pass

                # Method 3: Look for download buttons or new windows
                if not pdf_url:
                    try:
                        # Look for elements that might trigger PDF download
                        download_elements = self.driver.find_elements(
                            By.XPATH, "//a[contains(text(), 'Download') or contains(@title, 'PDF') or contains(@class, 'download')]")
                        if download_elements:
                            download_elements[0].click()
                            time.sleep(3)
                            # Check again for PDF
                            current_url_final = self.driver.current_url
                            if current_url_final.endswith('.pdf') or 'pdf' in current_url_final.lower():
                                pdf_url = current_url_final
                    except:
                        pass

                # Method 4: Check for new browser windows/tabs
                if not pdf_url and len(self.driver.window_handles) > 1:
                    try:
                        # Switch to new window
                        original_window = self.driver.current_window_handle
                        for window_handle in self.driver.window_handles:
                            if window_handle != original_window:
                                self.driver.switch_to.window(window_handle)
                                new_url = self.driver.current_url
                                if new_url.endswith('.pdf') or 'pdf' in new_url.lower():
                                    pdf_url = new_url
                                    break
                                self.driver.close()  # Close if not PDF
                        self.driver.switch_to.window(original_window)
                    except:
                        pass

                if pdf_url:
                    return self.download_pdf_from_url(pdf_url, doc_link['type'], company)
                else:
                    # Method 5: Wait for file download in current directory
                    if self.args.debug:
                        print("Checking for downloaded files in current directory...")

                    downloaded_file = self.wait_for_download(company)
                    if downloaded_file:
                        if self.args.debug:
                            print(f"Found downloaded file: {downloaded_file}")
                        return downloaded_file

                    if self.args.debug:
                        print("Could not find PDF download after clicking link")
                        print("Page source snippet:",
                              self.driver.page_source[:500])
                    return None

        except Exception as e:
            print(f"Error downloading document: {e}")
            if self.args.debug:
                import traceback
                traceback.print_exc()
            return None

    def download_pdf_from_url(self, pdf_url, doc_type, company):
        """Download PDF from a direct URL"""
        try:
            # Create filename
            company_name = company.get('name', 'Unknown').replace(
                ' ', '_').replace('/', '_')
            filename = f"{company_name}_{doc_type}.pdf"

            # Get cookies from selenium driver for the request
            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])

            # Download the PDF
            response = session.get(pdf_url)
            response.raise_for_status()

            # Save to current directory
            with open(filename, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded PDF: {filename}")
            return filename

        except Exception as e:
            print(f"Error downloading PDF from URL: {e}")
            return None

    def wait_for_download(self, company, timeout=15):
        """Wait for a file to be downloaded and return the filename"""
        import glob
        company_name = company.get('name', 'Unknown').replace(
            ' ', '_').replace('/', '_')

        # Get list of PDF files before (to detect new downloads)
        pdf_files_before = set(
            [f for f in os.listdir('.') if f.endswith('.pdf')])

        # Wait for new files to appear
        for i in range(timeout):
            time.sleep(1)
            pdf_files_after = set(
                [f for f in os.listdir('.') if f.endswith('.pdf')])
            new_pdf_files = pdf_files_after - pdf_files_before

            # Look for new PDF files
            if new_pdf_files:
                downloaded_file = list(new_pdf_files)[0]  # Get first new PDF
                if self.args.debug:
                    print(f"Detected new PDF file: {downloaded_file}")

                # Optionally rename to our naming convention
                target_name = f"{company_name}_AD.pdf"
                try:
                    if downloaded_file != target_name and not os.path.exists(target_name):
                        os.rename(downloaded_file, target_name)
                        return target_name
                except:
                    pass
                return downloaded_file

            # Also check for .crdownload files (Chrome partial downloads)
            all_files = set(os.listdir('.'))
            partial_files = [f for f in all_files if f.endswith('.crdownload')]
            if partial_files and i < timeout - 2:  # Still waiting for download to complete
                if self.args.debug and i % 5 == 0:  # Print every 5 seconds
                    print(
                        f"Waiting for download to complete... ({i+1}/{timeout})")
                continue

        # Final check for any PDF files that might match the company
        all_pdfs = [f for f in os.listdir('.') if f.endswith('.pdf')]
        for pdf_file in all_pdfs:
            # Check if this might be our company's PDF (contains HRB number or similar pattern)
            if 'HRB' in pdf_file and 'AD' in pdf_file:
                file_time = os.path.getmtime(pdf_file)
                current_time = time.time()
                # If file was created in the last 30 seconds, likely our download
                if current_time - file_time < 30:
                    if self.args.debug:
                        print(
                            f"Found recent PDF file that might be ours: {pdf_file}")
                    return pdf_file

        return None

    def extract_pdf_content(self, pdf_path):
        """Extract text content from PDF and parse company information"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from all pages
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()

                # Parse the extracted text into structured data
                return self.parse_company_data(text)

        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return None

    def parse_company_data(self, text):
        """Parse extracted PDF text into structured JSON data"""
        data = {}

        try:
            # Extract company number (HRB number)
            hrb_match = re.search(r'HRB\s*(\d+)', text)
            if hrb_match:
                data['company_number'] = f"HRB {hrb_match.group(1)}"

            # Extract number of entries
            entries_match = re.search(
                r'Anzahl der bisherigen Eintragungen:\s*(\d+)', text)
            if entries_match:
                data['number_of_entries'] = int(entries_match.group(1))

            # Extract company name (look for the actual company name, not just after "Firma:")
            firma_match = re.search(r'2\.\s*a\)\s*Firma:\s*([^\n]+)', text)
            if firma_match:
                data['company_name'] = firma_match.group(1).strip()

            # Extract location and address
            sitz_match = re.search(r'Sitz[^:]*:\s*([^\n]+)', text)
            if sitz_match:
                data['location'] = sitz_match.group(1).strip()

            # Extract business address
            address_match = re.search(r'Geschäftsanschrift:\s*([^\n]+)', text)
            if address_match:
                data['business_address'] = address_match.group(1).strip()

            # Extract business purpose
            purpose_match = re.search(
                r'Gegenstand des Unternehmens:\s*([^0-9]+?)(?=\n\d+\.|\n[A-Z]|\Z)', text, re.DOTALL)
            if purpose_match:
                data['business_purpose'] = re.sub(
                    r'\s+', ' ', purpose_match.group(1).strip())

            # Extract capital
            capital_match = re.search(
                r'Grund- oder Stammkapital:\s*([^\n]+)', text)
            if capital_match:
                data['capital'] = capital_match.group(1).strip()

            # Extract representation rules
            vertretung_match = re.search(
                r'Allgemeine Vertretungsregelung:\s*([^b\)]+)', text, re.DOTALL)
            if vertretung_match:
                data['representation_rules'] = re.sub(
                    r'\s+', ' ', vertretung_match.group(1).strip())

            # Extract management
            management_section = re.search(
                r'Geschäftsführer:([^0-9]+?)(?=\n\d+\.|\n[A-Z]|\Z)', text, re.DOTALL)
            if management_section:
                management_text = management_section.group(1)
                # Extract individual managers
                managers = re.findall(
                    r'([^,\n]+),\s*([^,\n]+),\s*\*(\d{2}\.\d{2}\.\d{4})', management_text)
                if managers:
                    data['management'] = []
                    for manager in managers:
                        data['management'].append({
                            'name': manager[0].strip(),
                            'location': manager[1].strip(),
                            'birth_date': manager[2].strip()
                        })

            # Extract prokura
            prokura_match = re.search(
                r'Prokura:\s*([^0-9]+?)(?=\n\d+\.|\n[A-Z]|\Z)', text, re.DOTALL)
            if prokura_match:
                prokura_text = prokura_match.group(1)
                # Look for individual prokura holders
                prokura_holders = re.findall(
                    r'([^,\n]+),\s*([^,\n]+),\s*\*(\d{2}\.\d{2}\.\d{4})', prokura_text)
                if prokura_holders:
                    data['prokura'] = []
                    for holder in prokura_holders:
                        data['prokura'].append({
                            'name': holder[0].strip(),
                            'location': holder[1].strip(),
                            'birth_date': holder[2].strip()
                        })

            # Extract legal form and founding date
            legal_form_match = re.search(
                r'Gesellschaft mit beschränkter Haftung\s*Gesellschaftsvertrag vom\s*(\d{2}\.\d{2}\.\d{4})', text)
            if legal_form_match:
                data['legal_form'] = 'Gesellschaft mit beschränkter Haftung'
                data['founding_date'] = legal_form_match.group(1)

            # Extract last entry date
            last_entry_match = re.search(
                r'Tag der letzten Eintragung:\s*(\d{2}\.\d{2}\.\d{4})', text)
            if last_entry_match:
                data['last_entry_date'] = last_entry_match.group(1)

            return data

        except Exception as e:
            print(f"Error parsing company data: {e}")
            return {}


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
            'history': [],
            'document_links': []
        }

        # Extract document download links
        document_links = result.find_all('a', class_='dokumentList')
        for link in document_links:
            if link.get('id'):
                # Extract document type from the span text
                span = link.find('span')
                doc_type = span.text.strip() if span else 'Unknown'
                onclick_value = link.get('onclick', '')

                company_info['document_links'].append({
                    'id': link.get('id'),
                    'type': doc_type,
                    'onclick': onclick_value
                })

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

    # Print extracted PDF data if available
    if company.get('extracted_data'):
        print('extracted_data:')
        print(json.dumps(company['extracted_data'],
              indent=2, ensure_ascii=False))


def output_companies_json(companies):
    """Output companies with extracted data as JSON"""
    output_data = []
    for company in companies:
        if company is None:  # Skip None companies
            continue

        company_data = {
            'basic_info': {
                'name': company.get('name', ''),
                'court': company.get('court', ''),
                'state': company.get('state', ''),
                'status': company.get('status', ''),
                'documents': company.get('documents', ''),
                'history': company.get('history', [])
            }
        }

        # Add extracted data if available
        if company.get('extracted_data'):
            company_data['extracted_data'] = company['extracted_data']

        # Add document links if available
        if company.get('document_links'):
            company_data['document_links'] = company['document_links']

        output_data.append(company_data)

    return json.dumps(output_data, indent=2, ensure_ascii=False)


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
        default="European EPC Competence Center"
    )
    parser.add_argument(
        "-so", "--schlagwortOptionen",
        help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
        choices=["all", "min", "exact"],
        default="all"
    )
    parser.add_argument(
        "-pd", "--download-pdfs",
        help="Download and extract information from company PDF documents",
        action="store_true"
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

            if args.download_pdfs:
                # Output structured JSON with extracted data
                print("\n" + "="*60)
                print("STRUCTURED JSON OUTPUT:")
                print("="*60)
                print(output_companies_json(companies))
            else:
                # Regular output
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
