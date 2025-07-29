"""Web automation utilities for handelsregister selenium operations."""

import os
import time

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

from config import (
    HANDELSREGISTER_URL,
    CHROME_AUTOMATION_OPTIONS,
    CHROME_EXPERIMENTAL_OPTIONS,
    USER_AGENT,
    DOWNLOAD_PREFS,
    DEFAULT_WAIT_TIMEOUT,
    EXTENDED_WAIT_TIMEOUT,
    SEARCH_FIELD_SELECTORS,
    SEARCH_OPTION_SELECTORS,
    SUBMIT_BUTTON_SELECTORS,
    COMMON_FIELD_IDS,
    ADVANCED_SEARCH_LINK_TEXT,
    SCHLAGWORT_OPTIONEN
)


class WebAutomation:
    """Handles web automation tasks for handelsregister website."""

    def __init__(self, debug=False):
        if not SELENIUM_AVAILABLE:
            raise ImportError(
                "Selenium is required for web automation. Install with: pip install selenium"
            )
        self.debug = debug
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Set up the Selenium WebDriver with optimal configuration."""
        chrome_options = Options()

        # Configure download directory to current working directory
        download_dir = os.path.abspath(".")
        prefs = DOWNLOAD_PREFS.copy()
        prefs["download.default_directory"] = download_dir
        chrome_options.add_experimental_option("prefs", prefs)

        # Add automation options
        for option in CHROME_AUTOMATION_OPTIONS:
            chrome_options.add_argument(option)

        # Add experimental options
        for key, value in CHROME_EXPERIMENTAL_OPTIONS.items():
            chrome_options.add_experimental_option(key, value)

        # Run headless if not in debug mode
        if not self.debug:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")

        # Add user agent
        chrome_options.add_argument(f"--user-agent={USER_AGENT}")

        try:
            # Use webdriver-manager to automatically handle chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, DEFAULT_WAIT_TIMEOUT)

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
        """Navigate to the handelsregister homepage."""
        self._debug_print("Opening handelsregister.de homepage...")

        self.driver.get(HANDELSREGISTER_URL)

        self._debug_print(f"Page title: {self.driver.title}")
        self._debug_print(f"Current URL: {self.driver.current_url}")

    def navigate_to_advanced_search(self):
        """Navigate to the advanced search page using JavaScript links."""
        self._debug_print("Navigating to advanced search...")

        # Longer timeout for headless mode
        timeout = EXTENDED_WAIT_TIMEOUT if not self.debug else DEFAULT_WAIT_TIMEOUT
        wait = WebDriverWait(self.driver, timeout)

        try:
            # Wait for page to fully load first
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional wait for dynamic content

            # Try each advanced search link text
            for link_text in ADVANCED_SEARCH_LINK_TEXT:
                try:
                    advanced_search_link = wait.until(
                        EC.element_to_be_clickable((By.LINK_TEXT, link_text))
                    )

                    self._debug_print(f"Found '{link_text}' link, clicking...")

                    # Scroll to element to ensure it's visible
                    self._scroll_to_element(advanced_search_link)
                    time.sleep(1)

                    advanced_search_link.click()
                    time.sleep(3)

                    page_title = self.driver.title
                    self._debug_print(
                        f"Advanced search page loaded: {page_title}")
                    self._debug_print(
                        f"Current URL: {self.driver.current_url}")

                    return True

                except TimeoutException:
                    continue

            # If we get here, none of the link texts worked
            self._debug_print("Could not find advanced search link")
            if self.debug:
                self._debug_available_links()
            return False

        except TimeoutException:
            self._debug_print("Timeout waiting for page to load")
            return False

    def find_and_fill_search_field(self, search_term, search_option):
        """Find and fill the search form field."""
        self._debug_print("Looking for search form...")
        time.sleep(2)  # Wait for page to fully load

        # Try to find search field using various selectors
        search_field = self._find_search_field()
        if not search_field:
            return False

        # Fill the search field
        return self._fill_search_field(search_field, search_term, search_option)

    def submit_search_form(self):
        """Submit the search form."""
        self._debug_print("Submitting search form...")

        # Try to find and click submit button
        submit_button = self._find_submit_button()

        if submit_button:
            submit_button.click()
            self._debug_print("Search form submitted")
            return True
        else:
            # Try submitting the first form directly
            return self._submit_form_directly()

    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

    def _find_search_field(self):
        """Find the search field using various selectors."""
        # Try CSS selectors first
        for selector in SEARCH_FIELD_SELECTORS:
            try:
                search_field = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self._debug_print(
                    f"Found search field with selector: {selector}")
                return search_field
            except TimeoutException:
                continue

        # Try by ID if CSS selectors fail
        for field_id in COMMON_FIELD_IDS:
            try:
                search_field = self.wait.until(
                    EC.element_to_be_clickable((By.ID, field_id))
                )
                self._debug_print(f"Found search field with ID: {field_id}")
                return search_field
            except TimeoutException:
                continue

        # Debug available form elements if nothing found
        if self.debug:
            self._debug_available_form_elements()

        return None

    def _fill_search_field(self, search_field, search_term, search_option):
        """Fill the search field with the given term and options."""
        try:
            self._debug_print(f"Search field found: name='{search_field.get_attribute('name')}', "
                              f"visible={search_field.is_displayed()}, enabled={search_field.is_enabled()}")

            # Scroll to element and focus
            self._scroll_to_element(search_field)
            time.sleep(0.5)
            search_field.click()

            # Clear and fill the search field
            search_field.clear()
            search_field.send_keys(search_term)

            self._debug_print(f"Filled search field with: {search_term}")
            field_value = search_field.get_attribute('value')
            self._debug_print(f"Field value after filling: {field_value}")

            # Handle search options if available
            self._set_search_options(search_option)

            return True

        except Exception as e:
            self._debug_print(f"Error filling search form: {e}")
            return False

    def _set_search_options(self, search_option):
        """Set search options (dropdown or radio buttons)."""
        try:
            for selector in SEARCH_OPTION_SELECTORS:
                try:
                    option_element = self.driver.find_element(
                        By.CSS_SELECTOR, selector)
                    if selector.startswith("select"):
                        # Handle dropdown
                        select = Select(option_element)
                        option_value = SCHLAGWORT_OPTIONEN.get(
                            search_option, 1)
                        try:
                            select.select_by_value(str(option_value))
                        except:
                            select.select_by_index(option_value - 1)

                        self._debug_print(
                            f"Set search option to: {search_option}")
                    break
                except NoSuchElementException:
                    continue

        except Exception as e:
            self._debug_print(f"Could not set search options: {e}")

    def _find_submit_button(self):
        """Find the submit button using various selectors."""
        for selector in SUBMIT_BUTTON_SELECTORS:
            try:
                submit_button = self.driver.find_element(
                    By.CSS_SELECTOR, selector)
                self._debug_print(
                    f"Found submit button with selector: {selector}")
                return submit_button
            except NoSuchElementException:
                continue
        return None

    def _submit_form_directly(self):
        """Submit the first form directly if no submit button found."""
        try:
            self._debug_print(
                "No submit button found, trying form submission via JavaScript")
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                self.driver.execute_script("arguments[0].submit();", forms[0])
                return True
            else:
                return False
        except Exception as e:
            self._debug_print(f"Error submitting form: {e}")
            return False

    def _scroll_to_element(self, element):
        """Scroll to ensure element is visible."""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)

    def _debug_print(self, message):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            print(message)

    def _debug_available_links(self):
        """Debug helper to print available links."""
        print(f"Page source length: {len(self.driver.page_source)}")
        links = [link.text for link in self.driver.find_elements(
            By.TAG_NAME, 'a')]
        print(f"Available links: {links}")

    def _debug_available_form_elements(self):
        """Debug helper to print available form elements."""
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
                print(f"  {input_type}: name='{name}' visible={visible} enabled={enabled}")
