# Selenium Solution

**FULLY WORKING** - Selenium-based handelsregister.de automation

## Features

- ✅ **Debug Mode**: Visible browser for troubleshooting (`-d` flag)
- ✅ **Headless Mode**: Silent automation (default mode)
- ✅ **Force Refresh**: Bypass cache (`-f` flag)
- ✅ **Search Options**: Same CLI as original script
- ✅ **Caching**: File-based result caching
- ✅ **Error Handling**: Robust element waiting and fallbacks
- ✅ **PDF Document Download**: Download and extract company information from PDF documents (`-pd` flag)

## PDF Document Processing

The new PDF functionality (`-pd` or `--download-pdfs` flag) adds comprehensive document processing:

### What it does:

1. **Document Link Extraction**: Finds all document download links (AD, CD, HD, etc.) in search results
2. **PDF Download**: Clicks on 'AD' (Aktuelle Daten/Current Data) document links to download PDFs
3. **Text Extraction**: Uses PyPDF2 to extract text content from downloaded PDFs
4. **Structured Parsing**: Parses PDF text into structured JSON format with fields like:
   - Company number (HRB number)
   - Number of entries
   - Company name
   - Location and business address
   - Business purpose
   - Capital information
   - Management details
   - Prokura holders
   - Legal form and founding date
   - Last entry date

### Output Format:

When PDF processing is enabled, the script outputs structured JSON instead of the regular text format:

```json
[
  {
    "basic_info": {
      "name": "Company Name",
      "court": "Court Info",
      "state": "State",
      "status": "Status",
      "documents": "Available Documents",
      "history": []
    },
    "extracted_data": {
      "company_number": "HRB 61026",
      "number_of_entries": 6,
      "company_name": "European EPC Competence Center GmbH",
      "location": "Köln",
      "business_address": "Stolberger Straße 108a, 50933 Köln",
      "business_purpose": "...",
      "capital": "300.000,00 EUR",
      "representation_rules": "...",
      "management": [...],
      "prokura": [...],
      "legal_form": "Gesellschaft mit beschränkter Haftung",
      "founding_date": "16.07.2007",
      "last_entry_date": "24.03.2025"
    },
    "document_links": [...]
  }
]
```

### Dependencies:

- `PyPDF2` - For PDF text extraction
- `requests` - For downloading PDF files

### Usage:

```bash
python handelsregister_selenium.py -s "European EPC Competence Center" -pd
```

### Important Notes:

- Only processes 'AD' (Aktuelle Daten) documents currently
- PDFs are saved to the current working directory with naming pattern: `CompanyName_AD.pdf`
- Cache is bypassed when PDF download is enabled to ensure fresh document access
- Requires active browser session for clicking document links

## Technical Implementation

- **JavaScript Handling**: Executes onclick JavaScript to trigger PDF downloads
- **Session Management**: Transfers browser cookies to requests session for authenticated downloads
- **Error Handling**: Robust error handling for PDF processing failures
- **Text Parsing**: Comprehensive regex patterns for extracting structured data from German legal documents

## Browser Automation Details

### Problem

Initially, the script worked in debug mode (visible browser) but failed in headless mode with "Could not navigate to advanced search page" error.

### Root Causes

1. **Viewport Size**: Headless Chrome uses small default viewport (800x600), causing element positioning issues
2. **Timing Issues**: Headless browsers need more time for JavaScript execution and element visibility
3. **Element Visibility**: Elements not properly rendered without explicit scrolling in headless mode

### Solution Implemented

1. **Proper Viewport**: Added `--window-size=1920,1080` and `--disable-gpu` for headless mode
2. **Increased Timeouts**: Extended timeout from 10s to 15s for headless mode
3. **Better Element Waiting**: Added `scrollIntoView()` before clicking elements
4. **Additional Wait Time**: Added extra 3-second wait for dynamic content loading

### Code Changes

```python
# Better headless configuration
if not self.args.debug:
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

# Improved navigation with better waiting
timeout = 15 if not self.args.debug else 10
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(3)  # Additional wait for dynamic content

# Ensure element visibility
self.driver.execute_script("arguments[0].scrollIntoView();", advanced_search_link)
time.sleep(1)
```

### Status

✅ **FIXED** - Both debug mode and headless mode now work reliably

## Test Results

**Search Query**: "european epc competence center"

**Results**:

- ✅ Successfully navigated to advanced search
- ✅ Found correct search field: `textarea[name='form:schlagwoerter']`
- ✅ Filled company search field (not location field)
- ✅ Submitted form successfully
- ✅ **Found 1 company**: "European EPC Competence Center GmbH"
- ✅ Extracted all details: court, state, status, etc.

## Test Suite Results

**All tests passing with EECC values** ✅

**EECC Company Data**:

- Company name: "European EPC Competence Center GmbH"
- Company number: "HRB 61026"
- Location: "Köln"
- Address: "Stolberger Straße 108a, 50933 Köln"
- Capital: "300.000,00 EUR"
- Legal form: "Gesellschaft mit beschränkter Haftung"
- Founded: "16.07.2007"

**Test Functions**:

- `test_parse_search_result`: HTML parsing (static data) ✅
- `test_get_results`: Search functionality with eecc ✅
- `test_pdf_download_european_epc`: PDF download and data extraction ✅

## Technical Implementation

### Key Improvements

1. **Correct Field Targeting**: Prioritizes `form:schlagwoerter` (company field) over `form:NiederlassungSitz` (location field)
2. **Robust Element Waiting**: Uses WebDriverWait with proper conditions
3. **Multiple Field Types**: Handles both `input` and `textarea` elements
4. **Auto Driver Management**: Uses webdriver-manager for automatic chromedriver setup

### Field Mapping

- **Company Search**: `textarea[name='form:schlagwoerter']` ✅
- **Search Options**: `input[name='form:schlagwortOptionen']` (radio buttons)
- **Submit Button**: `button[type='submit']` ✅

### Dependencies

- `selenium` - Browser automation
- `webdriver-manager` - Automatic chromedriver management
- `beautifulsoup4` - HTML parsing (same as original)

## Usage

### Installation

```bash
pip install selenium webdriver-manager beautifulsoup4
```

### Same CLI Interface

```bash
# Basic search
python3 handelsregister_selenium.py -s "European EPC Competence Center"

# With debug mode (shows browser)
python3 handelsregister_selenium.py -s "European EPC Competence Center" -d

# Force fresh search (bypass cache)
python3 handelsregister_selenium.py -s "European EPC Competence Center" -f

# Search options
python3 handelsregister_selenium.py -s "European EPC Competence Center" -so exact
```

## Migration from Original Script

### What Changed

- **Browser Engine**: mechanize → Selenium WebDriver
- **Navigation**: Direct form access → JavaScript link clicking
- **Field Selection**: Simple name matching → Robust CSS selectors with waiting

### What Stayed the Same

- ✅ **CLI Arguments**: Identical interface (`-s`, `-d`, `-f`, `-so`)
- ✅ **Output Format**: Same company information structure
- ✅ **Caching Logic**: Same file-based caching with `_selenium` suffix
- ✅ **Result Parsing**: Same BeautifulSoup-based parsing

## Performance Notes

- **Startup**: ~2-3 seconds (driver initialization)
- **Navigation**: ~3-4 seconds (page loads)
- **Headless Mode**: ✅ **WORKING** - Default mode (use `-d` for visible browser)
- **Headless Reliability**: Added viewport sizing and better waiting for consistent operation
- **Cache**: Same performance as original when cached

## Browser Requirements

- **Chrome/Chromium**: Required (automatically detected)
- **Chromedriver**: Auto-downloaded by webdriver-manager
- **Display**: Not required in headless mode (default)

## Comparison with Alternatives

| Approach                | Status        | Pros                      | Cons             |
| ----------------------- | ------------- | ------------------------- | ---------------- |
| **Selenium (Current)**  | ✅ Working    | Full JS support, same CLI | Heavier startup  |
| mechanize (Original)    | ❌ Broken     | Lightweight, fast         | No JS support    |
| unternehmensregister.de | ✅ Compatible | mechanize works           | Complex checkout |

## Future Maintenance

### Robustness

- Script adapts to minor HTML changes via CSS selectors
- Multiple fallback field selectors
- Comprehensive error handling and debug output

### Updates Needed If

- Field names change (update selectors in `fill_search_form()`)
- Page structure changes (update navigation in `navigate_to_advanced_search()`)
- Result format changes (update parsing in `get_companies_in_searchresults()`)

## Conclusion

The Selenium-based solution successfully restores functionality to the handelsregister CLI while maintaining the same user interface and output format. This approach is future-proof for modern JavaScript-based websites.
