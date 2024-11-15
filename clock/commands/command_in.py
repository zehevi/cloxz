import click
from utils import add_clock_entry


@click.command()
@click.argument('text', required=False)
def clock_in(filename: str, text: str, action: str) -> None:
    if text in (None, ""):
        text = click.prompt('Enter text for the clock entry', type=str)
    add_clock_entry(filename, text, action)
