# Project Notes Index

This directory contains notes about the handelsregister project.

## Files

- `selenium_solution.md` - **WORKING SOLUTION** - Complete Selenium implementation with headless mode support and PDF document processing
- `website_analysis.md` - Analysis of handelsregister.de website structure changes
- `alternative_solutions.md` - Summary of evaluated alternatives (Selenium solution implemented)
- `development_environment.md` - **CRITICAL** - Virtual environment setup and dependency management requirements
- `refactoring.md` - **NEW** - Documentation of the successful project refactoring into modular structure

## Project Structure

### ✅ **REFACTORED MODULAR STRUCTURE** (Current)

- **`__main__.py`** - CLI entry point and main application execution
- **`handelsregister_core.py`** - Main business logic and HandelsRegisterSelenium class
- **`config.py`** - Configuration constants and settings
- **`html_parser.py`** - HTML parsing and output formatting
- **`web_automation.py`** - Selenium WebDriver automation
- **`pdf_processor.py`** - PDF download and content extraction
- **`test_handelsregister.py`** - Test suite (updated for modular structure)
- **`requirements.txt`** - Python dependencies (selenium-focused)
- **`cache/`** - Search result cache directory

### CI/CD & Testing

- **`.github/workflows/runtests.yml`** - GitHub Actions workflow for automated testing
  - Runs on commits to main branch and pull requests
  - Tests against Python 3.8, 3.9, 3.10, 3.11
  - Installs Chrome/Chromium for Selenium tests
  - Uses `pytest -v` to run all tests
- **`test_handelsregister.py`** - ✅ All tests passing (syntax error fixed)
  - Fixed multi-line f-string compatibility issue for older Python versions
  - 3 tests: parse_search_result, get_results, pdf_download_european_epc

### Legacy Files

- `handelsregister_selenium_backup.py` - Backup of original monolithic file (1056 lines)

## Current Status

✅ **FULLY SOLVED WITH PDF PROCESSING** - The handelsregister functionality has been completely restored and enhanced.

**Solution**: `handelsregister_selenium.py` - Selenium-based script that works with the modern JavaScript-based handelsregister.de website.

**Features**:

- ✅ **Debug Mode**: Visible browser for troubleshooting (`-d` flag)
- ✅ **Headless Mode**: Silent automation (default mode)
- ✅ **Force Refresh**: Bypass cache (`-f` flag)
- ✅ **Search Options**: Same CLI as original script
- ✅ **Caching**: File-based result caching
- ✅ **Error Handling**: Robust element waiting and fallbacks
- ✅ **PDF Document Processing**: Download and extract structured data from company documents (`-pd` flag)

**Status**: Production-ready with PDF document extraction fully functional and tested.

**PDF Processing Capabilities**:

- Downloads 'AD' (Aktuelle Daten) documents automatically
- Extracts structured company information including HRB numbers, addresses, capital, management details
- Outputs clean JSON format with both search results and extracted PDF data
- Handles German legal document parsing with comprehensive regex patterns

## Key Technical Solutions

- **JavaScript Navigation**: Uses Selenium WebDriver to handle JSF application
- **Headless Mode**: Proper viewport sizing and element visibility handling
- **Element Waiting**: Robust WebDriverWait with fallback selectors
- **Auto-Driver**: webdriver-manager handles chromedriver automatically

## Alternative Solutions

See `alternative_solutions.md` for other approaches that were evaluated (unternehmensregister.de, APIs, other browser automation tools).
