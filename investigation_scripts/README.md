# Investigation Scripts

This directory contains scripts created to investigate the handelsregister.de website structure changes that broke the original `handelsregister.py` script.

## Scripts

- `investigate_website.py` - Initial comprehensive website structure analysis
- `analyze_search_pages.py` - Attempted analysis of specific search page URLs
- `navigate_to_search.py` - Tested navigation approaches with session context
- `find_form_endpoints.py` - Searched for alternative endpoints and form actions
- `examine_javascript_interface.py` - Script to examine JavaScript interface (not executed)

## Results

- `website_investigation_results.json` - Initial investigation results
- `search_pages_analysis.json` - Search page analysis results
- `navigation_analysis.json` - Navigation testing results
- `form_endpoints_analysis.json` - Form endpoint investigation results

## Conclusion

All investigations confirmed that handelsregister.de has moved to a JavaScript-based JSF application that cannot be automated with mechanize. The website requires browser automation tools like Selenium or Playwright.

## Key Findings

1. Search links point to `#` and require JavaScript execution
2. Direct access to search URLs returns HTTP 400 errors
3. The site uses JSF ViewState management
4. No traditional HTML forms are available for search functionality

See `../.cursor/notes/` for detailed analysis and alternative solutions.
