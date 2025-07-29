# Selenium-Based Handelsregister Solution

## Problem Solved ✅

The original `handelsregister.py` script broke due to handelsregister.de moving to a JavaScript-based JSF application. The new `handelsregister_selenium.py` script successfully replaces mechanize with Selenium browser automation.

## Solution Overview

**File**: `handelsregister_selenium.py`
**Approach**: Browser automation using Selenium WebDriver
**Status**: ✅ **WORKING** - Successfully tested with original search query

## Test Results

**Search Query**: "european epc competence center"

**Results**:

- ✅ Successfully navigated to advanced search
- ✅ Found correct search field: `textarea[name='form:schlagwoerter']`
- ✅ Filled company search field (not location field)
- ✅ Submitted form successfully
- ✅ **Found 1 company**: "European EPC Competence Center GmbH"
- ✅ Extracted all details: court, state, status, etc.

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
python3 handelsregister_selenium.py -s "company name"

# With debug mode (shows browser)
python3 handelsregister_selenium.py -s "company name" -d

# Force fresh search (bypass cache)
python3 handelsregister_selenium.py -s "company name" -f

# Search options
python3 handelsregister_selenium.py -s "company name" -so exact
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
- **Headless Mode**: Default (use `-d` for visible browser)
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
