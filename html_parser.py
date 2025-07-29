"""HTML parsing functionality for handelsregister search results."""

import json
from bs4 import BeautifulSoup


def get_companies_in_searchresults(html):
    """Parse companies from search results HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Try to find results table
    grid = soup.find('table', role='grid')
    if not grid:
        # Try alternative patterns
        grid = soup.find('table', class_='results')
        if not grid:
            grid = soup.find('div', class_='search-results')

    if not grid:
        print("No results table found")
        return []

    results = []
    rows = grid.find_all('tr')

    for result in rows:
        data_ri = result.get('data-ri')
        if data_ri is not None:
            try:
                index = int(data_ri)
                company_info = parse_result(result)
                if company_info:
                    results.append(company_info)
            except (ValueError, TypeError):
                continue

    return results


def parse_result(result):
    """Parse a single result row."""
    try:
        cells = []
        for cell in result.find_all('td'):
            cells.append(cell.text.strip())

        if len(cells) < 5:
            return None

        company_info = {
            'court': cells[1] if len(cells) > 1 else '',
            'name': cells[2] if len(cells) > 2 else '',
            'state': cells[3] if len(cells) > 3 else '',
            'status': cells[4] if len(cells) > 4 else '',
            'documents': cells[5] if len(cells) > 5 else '',
            'history': [],
            'document_links': []
        }

        # Extract document download links
        document_links = result.find_all('a', class_='dokumentList')
        for link in document_links:
            if link.get('id'):
                # Extract document type from the span text
                span = link.find('span')
                doc_type = span.text.strip() if span else 'Unknown'
                onclick_value = link.get('onclick', '')

                company_info['document_links'].append({
                    'id': link.get('id'),
                    'type': doc_type,
                    'onclick': onclick_value
                })

        # Parse history if available
        hist_start = 8
        if len(cells) > hist_start:
            for i in range(hist_start, len(cells), 3):
                if i + 1 < len(cells):
                    company_info['history'].append((cells[i], cells[i+1]))

        return company_info

    except Exception as e:
        print(f"Error parsing result: {e}")
        return None


def pr_company_info(company):
    """Print company information."""
    for tag in ('name', 'court', 'state', 'status'):
        print(f'{tag}: {company.get(tag, "-")}')

    print('history:')
    for name, loc in company.get('history', []):
        print(f'  {name} {loc}')

    # Print extracted PDF data if available
    if company.get('extracted_data'):
        print('extracted_data:')
        print(json.dumps(company['extracted_data'],
              indent=2, ensure_ascii=False))


def output_companies_json(companies):
    """Output companies with extracted data as JSON."""
    output_data = []
    for company in companies:
        if company is None:  # Skip None companies
            continue

        company_data = {
            'basic_info': {
                'name': company.get('name', ''),
                'court': company.get('court', ''),
                'state': company.get('state', ''),
                'status': company.get('status', ''),
                'documents': company.get('documents', ''),
                'history': company.get('history', [])
            }
        }

        # Add extracted data if available
        if company.get('extracted_data'):
            company_data['extracted_data'] = company['extracted_data']

        output_data.append(company_data)

    return json.dumps(output_data, indent=2, ensure_ascii=False)
