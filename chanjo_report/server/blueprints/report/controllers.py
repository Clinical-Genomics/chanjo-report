import pdfkit
from chanjo.store.models import Sample
from flask import session

from io import BytesIO
from chanjo_report.server.constants import LEVELS

from .utils import keymetrics_rows, samplesex_rows, transcripts_rows

def report_contents(request):
    """Check args or form provided by user request and prepare contents for report or pdf endpoints
    Args:
        request(flask.Request)

    Returns:
        data(dict)
    """

    sample_ids = request.form.getlist("sample_id") or request.args.getlist("sample_id")
    raw_gene_ids = request.form.get("gene_ids") or request.args.get("gene_ids")
    gene_ids = []
    if raw_gene_ids:
        gene_ids = [gene_id.strip() for gene_id in raw_gene_ids.split(",")]

    int_gene_ids = set()
    gene_id_errors = set()
    for gene_id in gene_ids:
        try:
            int_gene_ids.add(int(gene_id))
        except ValueError:
            gene_id_errors.add(gene_id)

    int_gene_ids = list(int_gene_ids)

    level = int(request.args.get("level") or request.form.get("level") or 10)
    extras = {
        "panel_name": (request.args.get("panel_name") or request.form.get("panel_name")),
        "level": level,
        "gene_ids": int_gene_ids,
        "show_genes": any([request.args.get("show_genes"), request.form.get("show_genes")]),
    }
    samples = Sample.query.filter(Sample.id.in_(sample_ids))
    case_name = request.form.get("case_name") or request.args.get("case_name")
    sex_rows = samplesex_rows(sample_ids)
    metrics_rows = keymetrics_rows(sample_ids, genes=int_gene_ids)
    tx_rows = transcripts_rows(sample_ids, genes=int_gene_ids, level=level)

    data = dict(
        sample_ids=sample_ids,
        samples=samples,
        case_name=case_name,
        sex_rows=sex_rows,
        levels=LEVELS,
        extras=extras,
        metrics_rows=metrics_rows,
        tx_rows=tx_rows,
        gene_id_errors=gene_id_errors,
    )
    return data

def html_to_pdf_file(
    html_string, orientation, dpi=96, margins=["1.5cm", "1cm", "1cm", "1cm"], zoom=1
) -> BytesIO:
    """Creates a pdf file from the content of an HTML file
    Args:
        html_string(string): an HTML string to be rendered as PDF
        orientation(string): landscape, portrait
        dpi(int): dot density of the page to be printed
        margins(list): [ margin-top, margin-right, margin-bottom, margin-left], in cm
        zoom(float): change the size of the content on the pages

    Returns:
        bytes_file(BytesIO): a BytesIO file
    """
    options = {
        "page-size": "A4",
        "zoom": zoom,
        "orientation": orientation,
        "encoding": "UTF-8",
        "dpi": dpi,
        "margin-top": margins[0],
        "margin-right": margins[1],
        "margin-bottom": margins[2],
        "margin-left": margins[3],
        "enable-local-file-access": None,
    }
    pdf = pdfkit.from_string(html_string, False, options=options, verbose=True)
    bytes_file = BytesIO(pdf)
    return bytes_file
