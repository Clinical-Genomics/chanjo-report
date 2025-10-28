# -*- coding: utf-8 -*-
from flask import url_for
from chanjo_report.server.app import create_app
from chanjo_report.server.config import DefaultConfig
from chanjo_report.server.utils import html_to_pdf_file


def render_pdf(options):
    """Generate a PDF report for a given group of samples and return as bytes file."""
    group_id = options['report']['group']
    report_options = options['report']

    config = DefaultConfig
    config.CHANJO_URI = options.get('database')
    config.CHANJO_LANGUAGE = report_options.get('language')
    config.CHANJO_PANEL = report_options.get('panel')
    panel_name = report_options.get('panel_name')

    app = create_app(config=config)

    # Generate the URL for the report page
    with app.test_request_context(base_url='http://localhost/'):
        report_url = url_for('report.group', group_id=group_id, panel_name=panel_name)

    # Use your HTML-to-PDF function to fetch and render the page
    bytes_file = html_to_pdf_file(
        html_string=None,
        url=report_url,
        orientation="portrait",
        dpi=300,
        zoom=0.6
    )

    return bytes_file
