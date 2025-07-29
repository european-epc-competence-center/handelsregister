"""Configuration module for handelsregister project."""

# URL constants
HANDELSREGISTER_URL = "https://www.handelsregister.de"

# Search option mappings
SCHLAGWORT_OPTIONEN = {
    "all": 1,
    "min": 2,
    "exact": 3
}

# Chrome WebDriver options for better automation
CHROME_AUTOMATION_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled"
]

CHROME_EXPERIMENTAL_OPTIONS = {
    "excludeSwitches": ["enable-automation"],
    "useAutomationExtension": False
}

# User agent for web requests
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"
)

# Download preferences for Chrome
DOWNLOAD_PREFS = {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False,
    "plugins.always_open_pdf_externally": True
}

# Timeout constants
DEFAULT_WAIT_TIMEOUT = 10
EXTENDED_WAIT_TIMEOUT = 15
DOWNLOAD_WAIT_TIMEOUT = 15

# Cache directory name
CACHE_DIR_NAME = "cache"

# CSS selectors for form elements
SEARCH_FIELD_SELECTORS = [
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

SEARCH_OPTION_SELECTORS = [
    "select[name*='option']",
    "select[name*='schlagwort']",
    "input[type='radio']"
]

SUBMIT_BUTTON_SELECTORS = [
    "input[type='submit']",
    "button[type='submit']",
    "button[name*='search']",
    "input[value*='suchen']",
    "input[value*='search']"
]

# Common field IDs to try
COMMON_FIELD_IDS = [
    'form:schlagwoerter',
    'schlagwoerter',
    'search',
    'suche',
    'query'
]

# Link text variations for navigation
ADVANCED_SEARCH_LINK_TEXT = ["Advanced search", "Erweiterte Suche"]

# PDF processing regex patterns
REGEX_PATTERNS = {
    'hrb_number': r'HRB\s*(\d+)',
    'entries_count': r'Anzahl der bisherigen Eintragungen:\s*(\d+)',
    'company_name': r'2\.\s*a\)\s*Firma:\s*([^\n]+)',
    'location': r'Sitz[^:]*:\s*([^\n]+)',
    'business_address': r'Geschäftsanschrift:\s*([^\n]+)',
    'business_purpose': r'Gegenstand des Unternehmens:\s*([^0-9]+?)(?=\n\d+\.|\n[A-Z]|\Z)',
    'capital': r'Grund- oder Stammkapital:\s*([^\n]+)',
    'representation_rules': r'Allgemeine Vertretungsregelung:\s*([^b\)]+)',
    'management_section': r'Geschäftsführer:([^0-9]+?)(?=\n\d+\.|\n[A-Z]|\Z)',
    'managers': r'([^,\n]+),\s*([^,\n]+),\s*\*(\d{2}\.\d{2}\.\d{4})',
    'prokura_section': r'Prokura:\s*([^0-9]+?)(?=\n\d+\.|\n[A-Z]|\Z)',
    'prokura_holders': r'([^,\n]+),\s*([^,\n]+),\s*\*(\d{2}\.\d{2}\.\d{4})',
    'legal_form': r'Gesellschaft mit beschränkter Haftung\s*Gesellschaftsvertrag vom\s*(\d{2}\.\d{2}\.\d{4})',
    'last_entry_date': r'Tag der letzten Eintragung:\s*(\d{2}\.\d{2}\.\d{4})'
}
