import pytest
import os
import json
from html_parser import get_companies_in_searchresults
from handelsregister_core import HandelsRegisterSelenium
import argparse


def test_parse_search_result():
    # simplified html from a real search
    html = '<html><body>%s</body></html>' % """<table role="grid"><thead></thead><tbody id="ergebnissForm:selectedSuchErgebnisFormTable_data" class="ui-datatable-data ui-widget-content"><tr data-ri="0" class="ui-widget-content ui-datatable-even" role="row"><td role="gridcell" colspan="9" class="borderBottom3"><table id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt147" class="ui-panelgrid ui-widget" role="grid"><tbody><tr class="ui-widget-content ui-panelgrid-even borderBottom1" role="row"><td role="gridcell" class="ui-panelgrid-cell fontTableNameSize" colspan="5">Berlin  <span class="fontWeightBold"> District court Berlin (Charlottenburg) HRB 44343  </span></td></tr><tr class="ui-widget-content ui-panelgrid-odd" role="row"><td role="gridcell" class="ui-panelgrid-cell paddingBottom20Px" colspan="5"><span class="marginLeft20">GASAG AG</span></td><td role="gridcell" class="ui-panelgrid-cell sitzSuchErgebnisse"><span class="verticalText ">Berlin</span></td><td role="gridcell" class="ui-panelgrid-cell" style="text-align: center;padding-bottom: 20px;"><span class="verticalText">currently registered</span></td><td role="gridcell" class="ui-panelgrid-cell textAlignLeft paddingBottom20Px" colspan="2"><div id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt160" class="ui-outputpanel ui-widget linksPanel"><script type="text/javascript" src="/rp_web/javax.faces.resource/jsf.js.xhtml?ln=javax.faces"></script><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:popupLink" class="underlinedText">AD</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:popupLink" class="underlinedText">CD</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:popupLink" class="underlinedText">HD</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:popupLink" class="underlinedText">DK</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:popupLink" class="underlinedText">UT</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:popupLink" class="underlinedText">VÖ</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:popupLink" class="underlinedText">SI</span></a></div></td></tr><tr class="ui-widget-content ui-panelgrid-even" role="row"><td role="gridcell" class="ui-panelgrid-cell" colspan="7"><table id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt172" class="ui-panelgrid ui-widget marginLeft20" role="grid"><tbody><tr class="ui-widget-content ui-panelgrid-even borderBottom1 RegPortErg_Klein" role="row"><td role="gridcell" class="ui-panelgrid-cell padding0Px">History</td></tr></tbody></table><table id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt176" class="ui-panelgrid ui-widget" role="grid"><tbody><tr class="ui-widget-content" role="row"><td role="gridcell" class="ui-panelgrid-cell RegPortErg_HistorieZn marginLeft20 padding0Px" colspan="5"><span class="marginLeft20 fontSize85">1.) Gasag Berliner Gaswerke Aktiengesellschaft</span></td><td role="gridcell" class="ui-panelgrid-cell RegPortErg_SitzStatus "><span class="fontSize85">1.) Berlin</span></td><td role="gridcell" class="ui-panelgrid-cell textAlignCenter"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table>"""
    res = get_companies_in_searchresults(html)
    assert res == [{
        'court': 'Berlin   District court Berlin (Charlottenburg) HRB 44343',
        'name': 'GASAG AG',
        'state': 'Berlin',
        'status': 'currently registered',
        'documents': 'ADCDHDDKUTVÖSI',
        'history': [('1.) Gasag Berliner Gaswerke Aktiengesellschaft', '1.) Berlin')],
        'document_links': [
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:fade',
                'type': 'AD', 'onclick': ''},
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:fade',
                'type': 'CD', 'onclick': ''},
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:fade',
                'type': 'HD', 'onclick': ''},
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:fade',
                'type': 'DK', 'onclick': ''},
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:fade',
                'type': 'UT', 'onclick': ''},
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:fade',
                'type': 'VÖ', 'onclick': ''},
            {'id': 'ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:fade',
                'type': 'SI', 'onclick': ''}
        ]
    },]


def test_get_results():
    args = argparse.Namespace(
        debug=False, force=True, schlagwoerter='european epc competence center', schlagwortOptionen='all', download_pdfs=False)
    h = HandelsRegisterSelenium(args)
    companies = h.search_company()
    assert len(companies) > 0


def test_pdf_download_european_epc():
    """Test PDF download functionality with European EPC Competence Center"""
    # Clean up any existing PDF files before test
    pdf_files_before = [f for f in os.listdir(
        '.') if f.endswith('.pdf') and 'European_EPC' in f]
    for pdf_file in pdf_files_before:
        try:
            os.remove(pdf_file)
        except:
            pass

    # Create args with PDF download enabled
    args = argparse.Namespace(
        debug=False,
        force=True,
        schlagwoerter='european epc competence center',
        schlagwortOptionen='all',
        download_pdfs=True
    )

    # Execute search with PDF download
    h = HandelsRegisterSelenium(args)
    companies = h.search_company()

    # Verify we found companies
    assert len(companies) > 0, "No companies found for European EPC search"

    # Check if any company has extracted data
    companies_with_data = [c for c in companies if c.get('extracted_data')]

    if companies_with_data:
        company = companies_with_data[0]
        extracted_data = company['extracted_data']

        # Verify the extracted data structure contains expected fields
        expected_fields = ['company_number', 'company_name', 'location']
        for field in expected_fields:
            assert field in extracted_data, f"Missing expected field: {field}"

        # Print the extracted data for verification
        print("\n" + "="*50)
        print("EXTRACTED COMPANY DATA:")
        print("="*50)
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        print("="*50)

        # Verify specific expected values for European EPC if found
        if 'European EPC' in extracted_data.get('company_name', ''):
            assert 'HRB' in extracted_data.get(
                'company_number', ''), "Company number should contain HRB"
            assert 'Köln' in extracted_data.get(
                'location', ''), "Location should be Köln"

    # Check that at least one PDF file was downloaded
    pdf_files_after = [f for f in os.listdir('.') if f.endswith('.pdf')]
    assert len(pdf_files_after) > len(
        pdf_files_before), "No PDF files were downloaded"

    downloaded_files = [
        f for f in pdf_files_after if f not in pdf_files_before]
    print(f"\nPDF files downloaded: {downloaded_files}")

    # Clean up downloaded PDF files after test
    for pdf_file in pdf_files_after:
        if pdf_file not in pdf_files_before:
            try:
                os.remove(pdf_file)
                print(f"Cleaned up: {pdf_file}")
            except:
                pass
