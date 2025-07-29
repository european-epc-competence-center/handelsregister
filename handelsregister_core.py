#!/usr/bin/env python3
"""
Refactored handelsregister core module using extracted components.
This module contains the main HandelsRegisterSelenium class.
"""

import pathlib
import time

from config import CACHE_DIR_NAME
from html_parser import get_companies_in_searchresults

try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Import web automation and PDF processor only if needed
if SELENIUM_AVAILABLE:
    from web_automation import WebAutomation
    from pdf_processor import PDFProcessor

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class HandelsRegisterSelenium:
    """Main class for handelsregister search functionality."""

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
        self.web_automation = WebAutomation(
            debug=args.debug) if SELENIUM_AVAILABLE else None
        self.pdf_processor = None

        # Set up cache directory
        self.cachedir = pathlib.Path(CACHE_DIR_NAME)
        self.cachedir.mkdir(parents=True, exist_ok=True)

    def search_company(self):
        """Perform the company search using Selenium."""
        cachename = self._get_cache_filename(self.args.schlagwoerter)

        # Check cache first (unless force refresh or PDF download requested)
        if not self.args.force and cachename.exists() and not self.args.download_pdfs:
            return self._load_cached_results(cachename)

        try:
            # Perform web search
            companies = self._perform_web_search(cachename)

            # Download PDFs if requested
            if self.args.download_pdfs and companies:
                companies = self._process_pdf_documents(companies)

            return companies

        finally:
            # Always clean up
            self.web_automation.close_driver()

    def _get_cache_filename(self, search_term):
        """Generate cache filename for search term."""
        return self.cachedir / f"{search_term}_selenium"

    def _load_cached_results(self, cachename):
        """Load results from cache."""
        with open(cachename, "r") as f:
            html = f.read()
            print(f"Return cached content for {self.args.schlagwoerter}")
            return get_companies_in_searchresults(html)

    def _perform_web_search(self, cachename):
        """Perform the actual web search and return results."""
        # Set up the browser
        self.web_automation.setup_driver()

        # Navigate to homepage
        self.web_automation.open_startpage()

        # Navigate to advanced search
        if not self.web_automation.navigate_to_advanced_search():
            raise RuntimeError("Could not navigate to advanced search page")

        # Fill and submit search form
        if not self._execute_search():
            raise RuntimeError("Could not complete search")

        # Wait for results page to load
        time.sleep(3)

        if self.args.debug:
            print(f"Results page loaded: {self.web_automation.driver.title}")
            print(f"Results URL: {self.web_automation.driver.current_url}")

        # Get and cache results
        html = self.web_automation.driver.page_source
        with open(cachename, "w") as f:
            f.write(html)

        # Parse companies from results
        return get_companies_in_searchresults(html)

    def _execute_search(self):
        """Execute the search form filling and submission."""
        # Find and fill the search form
        if not self.web_automation.find_and_fill_search_field(
            self.args.schlagwoerter,
            self.args.schlagwortOptionen
        ):
            return False

        # Submit the form
        return self.web_automation.submit_search_form()

    def _process_pdf_documents(self, companies):
        """Process PDF documents for companies if requested."""
        company_count = len(companies)
        print(f"PDF download enabled, processing {company_count} companies...")

        # Initialize PDF processor
        self.pdf_processor = PDFProcessor(
            self.web_automation.driver,
            debug=self.args.debug
        )

        # Process each company
        for i, company in enumerate(companies):
            company_name = company.get('name', 'Unknown')
            print(f"Processing company {i+1}/{len(companies)}: {company_name}")
            processed_company = self.pdf_processor.download_company_documents(
                company)
            if processed_company:  # Only update if processing succeeded
                companies[i] = processed_company

        return companies
