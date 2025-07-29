# Project Notes Index

This directory contains notes about the handelsregister project.

## Files

- `website_analysis.md` - Analysis of handelsregister.de website structure changes and investigation results
- `alternative_solutions.md` - Alternative approaches for accessing German company register data
- `selenium_solution.md` - **SUCCESSFUL SOLUTION** - Working Selenium-based implementation

## Project Structure

- `handelsregister.py` - Main CLI script for searching the German company register
- `test_handelsregister.py` - Test script
- `investigate_website.py` - Diagnostic script for investigating website structure
- `analyze_search_pages.py` - Script to analyze specific search page URLs
- `navigate_to_search.py` - Script to test navigation to search pages
- `find_form_endpoints.py` - Script to find form submission endpoints
- `examine_javascript_interface.py` - Script to examine JavaScript interface (not run)

## Current Status

✅ **SOLVED** - The original handelsregister.py script was broken due to major changes in the handelsregister.de website structure.

**Solution**: `handelsregister_selenium.py` - A drop-in replacement using Selenium browser automation that successfully works with the modern JavaScript-based website.

**Status**: Fully functional and tested with original search queries.

## Key Findings

- handelsregister.de now uses JSF (JavaServer Faces) with JavaScript navigation
- Search links point to `#` and require client-side JavaScript execution
- Direct access to search URLs returns HTTP 400 errors
- The site requires complex session management and ViewState handling

## Alternative Solutions

See `alternative_solutions.md` for potential workarounds and alternative data sources.
