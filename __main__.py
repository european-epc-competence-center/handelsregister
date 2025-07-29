#!/usr/bin/env python3
"""
Main entry point for handelsregister CLI application.
"""

import argparse
import sys

from handelsregister_core import HandelsRegisterSelenium, SELENIUM_AVAILABLE
from html_parser import pr_company_info, output_companies_json


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='A handelsregister CLI using Selenium browser automation'
    )
    parser.add_argument(
        "-d", "--debug",
        help="Enable debug mode and activate logging",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--force",
        help="Force a fresh pull and skip the cache",
        action="store_true"
    )
    parser.add_argument(
        "-s", "--schlagwoerter",
        help="Search for the provided keywords",
        required=True,
        default="European EPC Competence Center"
    )
    parser.add_argument(
        "-so", "--schlagwortOptionen",
        help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
        choices=["all", "min", "exact"],
        default="all"
    )
    parser.add_argument(
        "-pd", "--download-pdfs",
        help="Download and extract information from company PDF documents",
        action="store_true"
    )

    args = parser.parse_args()

    if args.debug:
        print("Debug mode enabled - browser will run in non-headless mode")

    return args


def main():
    """Main application entry point."""
    if not SELENIUM_AVAILABLE:
        print("Error: Selenium is not installed.")
        print("Install with: pip install selenium")
        print("Also install chromedriver: https://chromedriver.chromium.org/")
        sys.exit(1)

    try:
        args = parse_args()

        # Create and run handelsregister search
        h = HandelsRegisterSelenium(args)
        companies = h.search_company()

        if companies:
            print(f"Found {len(companies)} companies:")

            if args.download_pdfs:
                # Output structured JSON with extracted data
                print("\n" + "="*60)
                print("STRUCTURED JSON OUTPUT:")
                print("="*60)
                print(output_companies_json(companies))
            else:
                # Regular output
                for company in companies:
                    pr_company_info(company)
                    print("-" * 40)
        else:
            print("No companies found")

    except Exception as e:
        print(f"Error: {e}")
        if 'args' in locals() and args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
