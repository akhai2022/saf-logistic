"""Invoice & Credit Note PDF generation with WeasyPrint + Factur-X."""
from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def generate_invoice_pdf(invoice, lines, customer, tenant) -> bytes:
    template = env.get_template("invoice.html")
    html = template.render(
        invoice=invoice,
        lines=lines,
        customer=customer,
        tenant=tenant,
    )
    from weasyprint import HTML
    return HTML(string=html).write_pdf()


def generate_credit_note_pdf(credit_note, lines, customer, tenant) -> bytes:
    """Generate a credit note PDF using the credit_note.html template."""
    template = env.get_template("credit_note.html")
    html = template.render(
        credit_note=credit_note,
        lines=lines,
        customer=customer,
        tenant=tenant,
    )
    from weasyprint import HTML
    return HTML(string=html).write_pdf()


def generate_facturx_pdf(invoice, lines, customer, tenant) -> bytes:
    """Generate a Factur-X (EN 16931 BASIC) PDF/A-3 using the facturx library."""
    # First generate a regular PDF
    pdf_bytes = generate_invoice_pdf(invoice, lines, customer, tenant)

    # Build minimal EN 16931 XML
    xml_content = _build_facturx_xml(invoice, lines, customer, tenant)

    from facturx import generate_from_binary
    facturx_pdf = generate_from_binary(
        pdf_bytes,
        xml_content.encode("utf-8"),
        flavor="factur-x",
        level="basic",
    )
    return facturx_pdf


def _build_facturx_xml(invoice, lines, customer, tenant) -> str:
    """Build minimal Factur-X BASIC XML conforming to EN 16931."""
    inv_number = getattr(invoice, "invoice_number", "") or ""
    issue_date = str(getattr(invoice, "issue_date", "")) or ""
    due_date = str(getattr(invoice, "due_date", "")) or ""
    total_ht = f"{float(getattr(invoice, 'total_ht', 0)):.2f}"
    total_tva = f"{float(getattr(invoice, 'total_tva', 0)):.2f}"
    total_ttc = f"{float(getattr(invoice, 'total_ttc', 0)):.2f}"
    tva_rate = f"{float(getattr(invoice, 'tva_rate', 20)):.2f}"

    seller_name = getattr(tenant, "name", "SAF Transport") if tenant else "SAF Transport"
    seller_siren = getattr(tenant, "siren", "") if tenant else ""
    buyer_name = getattr(customer, "name", "") if customer else ""
    buyer_siren = getattr(customer, "siren", "") if customer else ""

    # Format date as YYYYMMDD
    formatted_issue = issue_date.replace("-", "")[:8] if issue_date else ""
    formatted_due = due_date.replace("-", "")[:8] if due_date else ""

    lines_xml = ""
    for idx, line in enumerate(lines, 1):
        desc = getattr(line, "description", "") or ""
        qty = f"{float(getattr(line, 'quantity', 1)):.2f}"
        up = f"{float(getattr(line, 'unit_price', 0)):.2f}"
        amt = f"{float(getattr(line, 'amount_ht', 0)):.2f}"
        lines_xml += f"""
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument><ram:LineID>{idx}</ram:LineID></ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct><ram:Name>{desc}</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice><ram:ChargeAmount>{up}</ram:ChargeAmount></ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="C62">{qty}</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:TypeCode>VAT</ram:TypeCode><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>{tva_rate}</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>{amt}</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
  xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:factur-x.eu:1p0:basic</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
  <rsm:ExchangedDocument>
    <ram:ID>{inv_number}</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">{formatted_issue}</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>{lines_xml}
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty>
        <ram:Name>{seller_name}</ram:Name>
        <ram:SpecifiedLegalOrganization><ram:ID schemeID="0002">{seller_siren}</ram:ID></ram:SpecifiedLegalOrganization>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>{buyer_name}</ram:Name>
        <ram:SpecifiedLegalOrganization><ram:ID schemeID="0002">{buyer_siren}</ram:ID></ram:SpecifiedLegalOrganization>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeDelivery/>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:ApplicableTradeTax>
        <ram:CalculatedAmount>{total_tva}</ram:CalculatedAmount>
        <ram:TypeCode>VAT</ram:TypeCode>
        <ram:BasisAmount>{total_ht}</ram:BasisAmount>
        <ram:CategoryCode>S</ram:CategoryCode>
        <ram:RateApplicablePercent>{tva_rate}</ram:RateApplicablePercent>
      </ram:ApplicableTradeTax>
      <ram:SpecifiedTradePaymentTerms>
        <ram:DueDateDateTime><udt:DateTimeString format="102">{formatted_due}</udt:DateTimeString></ram:DueDateDateTime>
      </ram:SpecifiedTradePaymentTerms>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:LineTotalAmount>{total_ht}</ram:LineTotalAmount>
        <ram:TaxBasisTotalAmount>{total_ht}</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">{total_tva}</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>{total_ttc}</ram:GrandTotalAmount>
        <ram:DuePayableAmount>{total_ttc}</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>"""
