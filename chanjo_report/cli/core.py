# -*- coding: utf-8 -*-
import click

from chanjo_report.server.app import create_app
from chanjo_report.server.config import ProdConfig


@click.command()
@click.option("-s", "--sample", multiple=True, help="Use -s option for each sample")
@click.option("-l", "--language", type=click.Choice(["en", "sv"]))
@click.option("-h", "--host", default="0.0.0.0", help="Server host")
@click.option("-p", "--port", default=5000, help="Server port")
@click.option("-d", "--debug", is_flag=True)
@click.pass_context
def report(context, sample, language, host, port, debug):
    """Generate a coverage report from Chanjo SQL output."""
    # get uri + dialect of Chanjo database
    if context.obj["database"] is None:
        click.echo("database URI not found")
        context.abort()

    config = ProdConfig
    config.SQLALCHEMY_DATABASE_URI = context.obj["database"]
    config.CHANJO_LANGUAGE = language
    config.DEBUG = debug

    app = create_app(config=config)

    base_url = f"http://{host}:{port}"
    if sample:
        url = "/".join([base_url, "/report?"]) + "&".join([f"sample_id={sx}" for sx in sample])
    else:
        url = base_url

    click.echo(click.style(f"open browser to: {url}", fg="yellow"))
    app.run(host=host, port=port)
