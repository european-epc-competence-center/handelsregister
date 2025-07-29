[![Run Python 🐍 tests](https://github.com/european-epc-competence-center/handelsregister/actions/workflows/runtests.yml/badge.svg)](https://github.com/european-epc-competence-center/handelsregister/actions/workflows/runtests.yml)

# Handelsregister CLI

## Background

This project is based on the original [bundesAPI/handelsregister](https://github.com/bundesAPI/handelsregister) repository. However, the German company register website has undergone significant changes that made the original script non-functional. We have completely rewritten the tool using Selenium WebDriver to handle the modern JavaScript-based website architecture.

**Credit**: This project builds upon the excellent work by [@LilithWittmann](https://github.com/LilithWittmann) and contributors at [bundesAPI/handelsregister](https://github.com/bundesAPI/handelsregister). The original API structure and CLI design inspired this implementation.

**Technical Change**: The original implementation used HTTP requests and form parsing, but the new handelsregister.de website requires JavaScript and complex form interactions that necessitated a complete rewrite using Selenium browser automation.

## Features

- ✅ **Full Company Search**: Search German company register with various filter options
- ✅ **PDF Document Processing**: Download and extract structured data from official company documents
- ✅ **Headless Mode**: Silent automation (default) or visible browser for debugging
- ✅ **Caching**: File-based result caching to improve performance and reduce server load
- ✅ **Multiple Search Options**: Exact match, partial match, or contain all keywords
- ✅ **JSON Output**: Structured data output for programmatic use
- ✅ **Rate Limiting Compliance**: Respects the 60 requests/hour limit

## Installation

### Prerequisites

- Python 3.7+
- Chrome/Chromium browser
- Internet connection

### Quick Install

```bash
# Clone this repository
git clone https://github.com/european-epc-competence-center/handelsregister.git
cd handelsregister

pyhton -m venv .venv
source .venv/bin/activate
# Install dependencies
pip install -r requirements.txt

# Selenium will automatically download the correct ChromeDriver
```

### Dependencies

All required packages are listed in `requirements.txt`:

- `selenium` - Browser automation
- `webdriver-manager` - Automatic ChromeDriver management
- `beautifulsoup4` - HTML parsing
- `PyPDF2` - PDF document processing
- `requests` - HTTP requests for PDF downloads

## Quick Start

### Company Search

```bash
# Search for a company (basic)
python handelsregister_selenium.py -s "European EPC Competence Center"

# Enable PDF document processing (downloads and extracts company data)
python3 handelsregister_selenium.py -s "European EPC Competence Center" -pd

# Debug mode (shows browser window for troubleshooting)
python3 handelsregister_selenium.py -s "European EPC Competence Center" -d

# Force fresh data (bypass cache)
python3 handelsregister_selenium.py -s "European EPC Competence Center" -f

# Combine multiple options
python3 handelsregister_selenium.py -s "European EPC Competence Center" -so exact -pd -f
```

### PDF Processing Feature

The `-pd` (or `--download-pdfs`) option enables automatic downloading and parsing of official company documents:

- **Downloads**: Automatically fetches 'AD' (Aktuelle Daten/Current Data) documents
- **Extracts**: Structured information including:
  - Company registration numbers (HRB)
  - Official addresses and postal codes
  - Share capital and currency
  - Management board details
  - Registration dates
- **Output**: Clean JSON format combining search results with extracted PDF data

```bash
# Example with PDF processing
python3 handelsregister_selenium.py -s "European EPC Competence Center" -pd
```

**Sample Output with PDF Processing**:

## Command Line Options

| Option                 | Short | Description                                            |
| ---------------------- | ----- | ------------------------------------------------------ |
| `--schlagwoerter`      | `-s`  | **Required.** Search keywords (company name)           |
| `--schlagwortOptionen` | `-so` | Search mode: `all`, `min`, or `exact` (default: `all`) |
| `--download-pdfs`      | `-pd` | Download and process PDF documents                     |
| `--debug`              | `-d`  | Show browser window (for debugging)                    |
| `--force`              | `-f`  | Bypass cache and fetch fresh data                      |
| `--help`               | `-h`  | Show help message                                      |

### Search Options Explained

- **`all`** (default): Company name must contain ALL search keywords
- **`min`**: Company name must contain AT LEAST ONE search keyword
- **`exact`**: Search for exact company name match

## Testing

```bash
# Run tests
python -m pytest test_handelsregister.py -v

# Run with coverage
python -m pytest test_handelsregister.py --cov=handelsregister_selenium
```

## Legal Information

The German Commercial Register (Handelsregister) is a public directory that maintains records of registered merchants within a specific geographical area under commercial law. Entries are mandatory for facts or legal relationships conclusively listed in the HGB (German Commercial Code), AktG (Stock Corporation Act), and GmbHG (Limited Liability Company Act).

Access to the commercial register and submitted documents is permitted for informational purposes according to § 9 Para. 1 HGB, with a limit of no more than 60 queries per hour (see [Terms of Use](https://www.handelsregister.de/rp_web/information.xhtml)). Individual company searches, access to company data, and use of commercial register announcements are free of charge.

**Warning**: The register portal is regularly targeted by automated mass queries. According to the [FAQs](https://www.handelsregister.de/rp_web/information.xhtml), the frequency of these queries often reaches levels that constitute criminal offenses under §§303a, b StGB. More than 60 queries per hour violate the terms of use.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

![AGPL Logo](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)

Copyright (C) 2025 European EPC Competence Center GmbH

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Acknowledgments

- Original implementation by [@LilithWittmann](https://github.com/LilithWittmann) and the [bundesAPI](https://github.com/bundesAPI) team
- German Federal API initiative for making government data accessible
- All contributors to the original project

---

**Note**: This is an independent implementation created due to website changes that broke the original tool. For the historical HTTP-based approach, see the original [bundesAPI/handelsregister](https://github.com/bundesAPI/handelsregister) repository.
