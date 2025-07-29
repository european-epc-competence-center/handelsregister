# Alternative Solutions for German Company Register Access

## Problem Summary

The handelsregister.de website has moved to a JavaScript-based JSF application that cannot be automated with mechanize. The original script approach is no longer viable.

## Solution Options

### 1. Browser Automation with Selenium (Recommended)

**Approach**: Replace mechanize with Selenium WebDriver to handle JavaScript.

**Pros**:

- Can handle JavaScript navigation
- Full browser functionality
- Most likely to work with current website

**Cons**:

- Heavier resource usage
- Requires browser driver management
- Slower than mechanize

**Implementation**:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def selenium_search(search_term):
    driver = webdriver.Chrome()  # or Firefox()
    try:
        driver.get("https://www.handelsregister.de")

        # Wait for and click advanced search
        advanced_search = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Advanced search"))
        )
        advanced_search.click()

        # Wait for search form and fill it
        search_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "schlagwoerter"))  # or whatever the field name is
        )
        search_field.send_keys(search_term)

        # Submit and get results
        submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        submit_button.click()

        # Parse results
        # ...

    finally:
        driver.quit()
```

### 2. Use Unternehmensregister.de Alternative

**Approach**: Switch to the federal company register at unternehmensregister.de.

**URL**: https://www.unternehmensregister.de/ureg/

**Pros**:

- Different website architecture (might be more automation-friendly)
- Official federal register
- Contains similar data

**Cons**:

- Different data structure
- May require paid access for detailed information
- Uncertain automation compatibility

**Investigation needed**:

- Test if unternehmensregister.de still uses traditional forms
- Check data availability and access restrictions
- Verify field names and search options

### 3. API-Based Solutions

**Approach**: Look for official or third-party APIs.

**Potential Sources**:

- Official government APIs (if they exist)
- Third-party data providers
- OpenCorporates.com (international company data)

**Pros**:

- Stable, programmatic access
- Better performance
- More reliable than web scraping

**Cons**:

- May require API keys or payment
- Limited to available data sources
- Potentially less complete data

### 4. Hybrid Approach: Manual URL Construction

**Approach**: Analyze the JavaScript to understand the underlying API calls and replicate them.

**Investigation steps**:

1. Use browser developer tools to capture network requests
2. Identify the actual search API endpoints
3. Reverse engineer the request format
4. Implement direct API calls

**Pros**:

- Potentially faster than Selenium
- No browser dependency

**Cons**:

- Fragile (may break with website updates)
- Requires deep analysis of JavaScript
- May be blocked by anti-automation measures

### 5. Headless Browser Solutions

**Approach**: Use tools like Playwright or Puppeteer for JavaScript-enabled automation.

**Benefits over Selenium**:

- Often faster and more reliable
- Better handling of modern web applications
- More stable API

**Python Example with Playwright**:

```python
from playwright.sync_api import sync_playwright

def playwright_search(search_term):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://www.handelsregister.de")

        # Click advanced search
        page.click("text=Advanced search")

        # Fill search form
        page.fill("[name='schlagwoerter']", search_term)

        # Submit
        page.click("[type='submit']")

        # Get results
        results = page.query_selector_all(".result-item")  # adjust selector

        browser.close()
```

## Recommended Implementation Strategy

### Phase 1: Quick Assessment

1. Test unternehmensregister.de compatibility with mechanize
2. If that works, adapt the existing script
3. If not, proceed to Phase 2

### Phase 2: Browser Automation

1. Implement Selenium or Playwright solution
2. Use the original script structure but replace mechanize parts
3. Test with the same search functionality

### Phase 3: Enhancement

1. Add error handling and retry logic
2. Implement rate limiting to be respectful
3. Add caching for repeated searches
4. Consider proxy rotation if needed

## Dependencies for Browser Automation

### For Selenium:

```bash
pip install selenium
# Plus browser driver (chromedriver, geckodriver, etc.)
```

### For Playwright:

```bash
pip install playwright
playwright install chromium
```

## Recommended Next Steps

1. **Immediate**: Test unternehmensregister.de with existing mechanize approach
2. **Short-term**: Implement Selenium-based version of the handelsregister search
3. **Long-term**: Investigate API alternatives or optimize the browser automation solution

## Code Migration Notes

To migrate the existing `handelsregister.py`:

- Keep the same CLI argument structure
- Keep the same output format and caching logic
- Replace only the `search_company()` method to use browser automation
- Maintain the same error handling patterns
