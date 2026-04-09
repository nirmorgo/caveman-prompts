"""CLI entrypoint for caveman-prompts."""

import sys
import click
from caveman import CavemanCompressor


@click.command()
@click.argument("prompt", required=False)
@click.option("--level", "-l", default=2, show_default=True,
              help="Compression level (1-3).")
@click.option("--report", "-r", "show_report", is_flag=True,
              help="Show token-savings breakdown.")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True),
              help="Read prompt from file instead of argument.")
def cli(prompt: str, level: int, show_report: bool, input_file: str) -> None:
    """Compress LLM prompts to their caveman essence."""
    if input_file:
        with open(input_file, "r") as fh:
            text = fh.read()
    elif prompt:
        text = prompt
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
        if not text.strip():
            raise click.UsageError("Provide a PROMPT argument, --file, or pipe input.")
    else:
        raise click.UsageError("Provide a PROMPT argument, --file, or pipe input.")

    c = CavemanCompressor(level=level)

    if show_report:
        c.report(text)
    else:
        click.echo(c.compress(text))
