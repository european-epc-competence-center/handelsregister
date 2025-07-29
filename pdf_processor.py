"""PDF processing functionality for handelsregister documents."""

import os
import time
import re
import json
import requests
from config import REGEX_PATTERNS, DOWNLOAD_WAIT_TIMEOUT

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFProcessor:
    """Handles PDF document downloading and content extraction."""

    def __init__(self, driver, debug=False):
        self.driver = driver
        self.debug = debug

        if not PDF_AVAILABLE:
            raise ImportError(
                "PyPDF2 is required for PDF processing. Install with: pip install PyPDF2"
            )

    def download_company_documents(self, company):
        """Download PDF documents for a company and extract information."""
        if not company.get('document_links'):
            if self.debug:
                company_name = company.get('name', 'Unknown')
                print(f"No document links found for {company_name}")
            return company

        company['extracted_data'] = {}

        for doc_link in company['document_links']:
            # Only process 'AD' documents (Aktuelle Daten / Current Data)
            if doc_link['type'] == 'AD':
                try:
                    if self.debug:
                        company_name = company.get('name', 'Unknown')
                        print(f"Processing {doc_link['type']} document for {company_name}")

                    pdf_path = self._download_pdf_document(doc_link, company)
                    if pdf_path:
                        extracted_data = self._extract_pdf_content(pdf_path)
                        if extracted_data:
                            company['extracted_data'] = extracted_data
                            if self.debug:
                                doc_type = doc_link['type']
                                print(f"Successfully extracted data from {doc_type} document")
                        break  # Stop after first successful AD document
                except Exception as e:
                    print(f"Error processing document {doc_link['type']}: {e}")
                    continue

        return company

    def _download_pdf_document(self, doc_link, company):
        """Download a PDF document by clicking the link."""
        try:
            # Find the document link on the current page
            from selenium.webdriver.common.by import By
            link_element = self.driver.find_element(By.ID, doc_link['id'])

            # Execute the onclick JavaScript to trigger the download
            if doc_link['onclick']:
                onclick = doc_link['onclick']

                if self.debug:
                    print(f"Executing onclick: {onclick[:100]}...")

                # Store current state before action
                current_url_before = self.driver.current_url
                page_source_before = self.driver.page_source[:1000]

                # Execute the onclick JavaScript
                self.driver.execute_script(onclick)

                # Wait for potential navigation or content change
                time.sleep(5)

                # Check if URL changed (form submission likely caused navigation)
                current_url_after = self.driver.current_url
                page_source_after = self.driver.page_source[:1000]

                if self.debug:
                    self._debug_pdf_download_state(
                        current_url_before, current_url_after,
                        page_source_before, page_source_after
                    )

                # Try different methods to get the PDF
                pdf_url = self._find_pdf_url(current_url_after)

                if pdf_url:
                    return self._download_pdf_from_url(pdf_url, doc_link['type'], company)
                else:
                    # Wait for file download in current directory
                    return self._wait_for_download(company)

        except Exception as e:
            print(f"Error downloading document: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def _debug_pdf_download_state(self, url_before, url_after, page_before, page_after):
        """Debug helper to print download state information."""
        print(f"URL before: {url_before}")
        print(f"URL after: {url_after}")
        print(f"Page title: {self.driver.title}")
        print(f"Page content changed: {page_before != page_after}")

        # Check for PDF-related content in page
        page_source = self.driver.page_source.lower()
        if 'pdf' in page_source:
            print("Found 'pdf' text in page source")
        if '%PDF' in self.driver.page_source:
            print("Found PDF magic bytes in page source!")

        # Check response headers if possible
        try:
            logs = self.driver.get_log('performance')
            for log in logs[-5:]:  # Check last 5 network events
                message = json.loads(log['message'])
                if 'Network.responseReceived' in message.get('method', ''):
                    response = message.get('params', {}).get('response', {})
                    headers = response.get('headers', {})
                    content_type = headers.get(
                        'content-type', headers.get('Content-Type', ''))
                    if 'pdf' in content_type.lower():
                        print(f"Found PDF response: {content_type}")
                        print(f"Response URL: {response.get('url', '')}")
        except:
            pass

    def _find_pdf_url(self, current_url):
        """Try different methods to find PDF URL."""
        # Method 1: Check if we're now on a PDF page
        if current_url.endswith('.pdf') or 'pdf' in current_url.lower():
            return current_url

        # Method 2: Look for PDF links or iframes
        try:
            from selenium.webdriver.common.by import By
            pdf_elements = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, '.pdf')] | //iframe[contains(@src, '.pdf')] | //embed[contains(@src, '.pdf')]"
            )
            if pdf_elements:
                pdf_url = pdf_elements[0].get_attribute(
                    'href') or pdf_elements[0].get_attribute('src')
                if self.debug:
                    print(f"Found PDF element with URL: {pdf_url}")
                return pdf_url
        except:
            pass

        # Method 3: Check if content-type indicates PDF
        try:
            page_source = self.driver.page_source
            if 'application/pdf' in page_source or '%PDF' in page_source:
                if self.debug:
                    print("Current page appears to be serving PDF content")
                return current_url
        except:
            pass

        # Method 4: Look for download buttons or new windows
        try:
            from selenium.webdriver.common.by import By
            download_elements = self.driver.find_elements(
                By.XPATH, "//a[contains(text(), 'Download') or contains(@title, 'PDF') or contains(@class, 'download')]"
            )
            if download_elements:
                download_elements[0].click()
                time.sleep(3)
                # Check again for PDF
                current_url_final = self.driver.current_url
                if current_url_final.endswith('.pdf') or 'pdf' in current_url_final.lower():
                    return current_url_final
        except:
            pass

        # Method 5: Check for new browser windows/tabs
        if len(self.driver.window_handles) > 1:
            try:
                original_window = self.driver.current_window_handle
                for window_handle in self.driver.window_handles:
                    if window_handle != original_window:
                        self.driver.switch_to.window(window_handle)
                        new_url = self.driver.current_url
                        if new_url.endswith('.pdf') or 'pdf' in new_url.lower():
                            return new_url
                        self.driver.close()  # Close if not PDF
                self.driver.switch_to.window(original_window)
            except:
                pass

        return None

    def _download_pdf_from_url(self, pdf_url, doc_type, company):
        """Download PDF from a direct URL."""
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

    def _wait_for_download(self, company, timeout=DOWNLOAD_WAIT_TIMEOUT):
        """Wait for a file to be downloaded and return the filename."""
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
                if self.debug:
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
                if self.debug and i % 5 == 0:  # Print every 5 seconds
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
                    if self.debug:
                        print(
                            f"Found recent PDF file that might be ours: {pdf_file}")
                    return pdf_file

        return None

    def _extract_pdf_content(self, pdf_path):
        """Extract text content from PDF and parse company information."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from all pages
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()

                # Parse the extracted text into structured data
                return self._parse_company_data(text)

        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return None

    def _parse_company_data(self, text):
        """Parse extracted PDF text into structured JSON data."""
        data = {}

        try:
            # Extract company number (HRB number)
            hrb_match = re.search(REGEX_PATTERNS['hrb_number'], text)
            if hrb_match:
                data['company_number'] = f"HRB {hrb_match.group(1)}"

            # Extract number of entries
            entries_match = re.search(REGEX_PATTERNS['entries_count'], text)
            if entries_match:
                data['number_of_entries'] = int(entries_match.group(1))

            # Extract company name
            firma_match = re.search(REGEX_PATTERNS['company_name'], text)
            if firma_match:
                data['company_name'] = firma_match.group(1).strip()

            # Extract location and address
            sitz_match = re.search(REGEX_PATTERNS['location'], text)
            if sitz_match:
                data['location'] = sitz_match.group(1).strip()

            # Extract business address
            address_match = re.search(REGEX_PATTERNS['business_address'], text)
            if address_match:
                data['business_address'] = address_match.group(1).strip()

            # Extract business purpose
            purpose_match = re.search(
                REGEX_PATTERNS['business_purpose'], text, re.DOTALL)
            if purpose_match:
                # Clean up multiline text by normalizing whitespace but preserving line breaks where meaningful
                business_purpose = purpose_match.group(1).strip()
                # Replace multiple spaces/newlines with single spaces, but keep intentional line breaks
                business_purpose = re.sub(r'\n\s*', '\n', business_purpose)
                business_purpose = re.sub(r' +', ' ', business_purpose)
                data['business_purpose'] = business_purpose

            # Extract capital
            capital_match = re.search(REGEX_PATTERNS['capital'], text)
            if capital_match:
                data['capital'] = capital_match.group(1).strip()

            # Extract representation rules
            vertretung_match = re.search(
                REGEX_PATTERNS['representation_rules'], text, re.DOTALL)
            if vertretung_match:
                representation_rules = vertretung_match.group(1).strip()
                # Clean up multiline text
                representation_rules = re.sub(
                    r'\n\s*', ' ', representation_rules)
                representation_rules = re.sub(r' +', ' ', representation_rules)
                data['representation_rules'] = representation_rules

            # Extract management
            management_section = re.search(
                REGEX_PATTERNS['management_section'], text, re.DOTALL)
            if management_section:
                management_text = management_section.group(1)
                # Clean up management text
                management_text = re.sub(r'\n\s*', ' ', management_text)

                # Extract individual managers
                managers = re.findall(
                    REGEX_PATTERNS['managers'], management_text)
                if managers:
                    data['management'] = []
                    for manager in managers:
                        # Combine last name and first name
                        last_name = manager[0].strip()
                        first_name = manager[1].strip()
                        full_name = f"{last_name}, {first_name}"
                        data['management'].append({
                            'name': full_name,
                            'location': manager[2].strip(),
                            'birth_date': manager[3].strip()
                        })
                else:
                    # If regex doesn't find managers, try to extract manually
                    # Look for pattern: "Name, Location, *Birth"
                    management_lines = [
                        line.strip() for line in management_text.split('\n') if line.strip()]
                    for line in management_lines:
                        if '*' in line and ',' in line:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 4:
                                # Handle 4-part format: LastName, FirstName, Location, *Birth
                                full_name = f"{parts[0]}, {parts[1]}"
                                location = parts[2]
                                birth_info = parts[3]
                                if '*' in birth_info:
                                    birth_date = birth_info.split(
                                        '*')[1].strip()
                                    if not data.get('management'):
                                        data['management'] = []
                                    data['management'].append({
                                        'name': full_name,
                                        'location': location,
                                        'birth_date': birth_date
                                    })
                            elif len(parts) >= 3:
                                # Fallback to 3-part format for compatibility
                                name = parts[0]
                                location = parts[1]
                                birth_info = parts[2]
                                if '*' in birth_info:
                                    birth_date = birth_info.split(
                                        '*')[1].strip()
                                    if not data.get('management'):
                                        data['management'] = []
                                    data['management'].append({
                                        'name': name,
                                        'location': location,
                                        'birth_date': birth_date
                                    })

            # Extract prokura
            prokura_match = re.search(
                REGEX_PATTERNS['prokura_section'], text, re.DOTALL)
            if prokura_match:
                prokura_text = prokura_match.group(1)
                # Clean up prokura text and handle "Einzelprokura:" prefix
                prokura_text = re.sub(r'\n\s*', '\n', prokura_text)
                prokura_text = re.sub(r'Einzelprokura:\s*', '', prokura_text)
                prokura_text = re.sub(r'Gesamtprokura:\s*', '', prokura_text)

                # Look for individual prokura holders
                prokura_holders = re.findall(
                    REGEX_PATTERNS['prokura_holders'], prokura_text)
                if prokura_holders:
                    data['prokura'] = []
                    for holder in prokura_holders:
                        # Combine title/last name and first name
                        full_name = f"{holder[0].strip()}, {holder[1].strip()}"
                        data['prokura'].append({
                            'name': full_name,
                            'location': holder[2].strip(),
                            'birth_date': holder[3].strip()
                        })
                else:
                    # If regex doesn't find holders, try to extract the full prokura text as single entry
                    prokura_lines = [
                        line.strip() for line in prokura_text.split('\n') if line.strip()]
                    if prokura_lines:
                        # Try to parse manually: "Name, Location, *Birth"
                        for line in prokura_lines:
                            if '*' in line and ',' in line:
                                parts = [p.strip() for p in line.split(',')]
                                if len(parts) >= 4:
                                    # Handle 4-part format: TitleLastName, FirstName, Location, *Birth
                                    full_name = f"{parts[0]}, {parts[1]}"
                                    location = parts[2]
                                    birth_info = parts[3]
                                    if '*' in birth_info:
                                        birth_date = birth_info.split(
                                            '*')[1].strip()
                                        if not data.get('prokura'):
                                            data['prokura'] = []
                                        data['prokura'].append({
                                            'name': full_name,
                                            'location': location,
                                            'birth_date': birth_date
                                        })
                                elif len(parts) >= 3:
                                    # Fallback to 3-part format for compatibility
                                    name = parts[0]
                                    location = parts[1]
                                    birth_info = parts[2]
                                    if '*' in birth_info:
                                        birth_date = birth_info.split(
                                            '*')[1].strip()
                                        if not data.get('prokura'):
                                            data['prokura'] = []
                                        data['prokura'].append({
                                            'name': name,
                                            'location': location,
                                            'birth_date': birth_date
                                        })

            # Extract legal form and founding date
            legal_form_match = re.search(REGEX_PATTERNS['legal_form'], text)
            if legal_form_match:
                data['legal_form'] = 'Gesellschaft mit beschränkter Haftung'
                data['founding_date'] = legal_form_match.group(1)

            # Extract last entry date
            last_entry_match = re.search(
                REGEX_PATTERNS['last_entry_date'], text)
            if last_entry_match:
                data['last_entry_date'] = last_entry_match.group(1)

            return data

        except Exception as e:
            print(f"Error parsing company data: {e}")
            return {}
