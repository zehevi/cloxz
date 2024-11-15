import csv
import os
import pathlib
import typer
import typer.completion
from datetime import datetime
from enum import Enum
from rich import print
from rich.table import Table
from typing import Annotated, Optional
from .utils import add_clock_entry, create_directories, create_file, validate_month


CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE


class ClockStatus(Enum):
    NONE = 0
    IN = 1
    OUT = 2


app = typer.Typer(name="cxz")
config_app = typer.Typer(name="config")
app.add_typer(config_app)

# typer.completion.completion_init()


def main():
    create_directories(CONFIG_DIR, DATA_DIR)
    filename = CSV_FILE_PATH
    if not os.path.exists(filename):
        create_file(CSV_FILE_PATH)
    app()


# TODO: Support time and date input / picker
@app.command(name="in")
def clock_in(customer: str = typer.Argument(None)):
    if customer is None:
        customer = typer.prompt("Customer")
    add_clock_entry(CSV_FILE_PATH, customer, "in")


# TODO: Support time and date input / picker
@app.command(name="out")
def clock_out(customer: str = typer.Argument(None)):
    if customer is None:
        customer = typer.prompt("Customer")
    add_clock_entry(CSV_FILE_PATH, customer, "out")


# FIXME: Supplying a month doesn't do anything
@app.command(name="show")
def clock_show(month: str = typer.Option("current", prompt=True)):
    month = validate_month(month)
    list_entries()


@config_app.command('dir')
def config_dir_command():
    """
    Print the DATA directory path.
    """
    print(DATA_DIR)


@config_app.command('file')
def config_file_command():
    """
    Print the path to the CSV file currently active.
    """
    print(CSV_FILE_PATH)


@app.command()
def delete():
    delete_entry(CSV_FILE_PATH)


@app.command()
def status():
    date = datetime.now().strftime("%Y-%m-%d")
    match find_status_by_date(date, CSV_FILE_PATH):
        case ClockStatus.NONE:
            print("No clocking entry found for today")
        case ClockStatus.IN:
            print("Found a clock-in entry for today")
        case ClockStatus.OUT:
            print("found clock-out entry for today")


def list_entries(print_line_num: bool = False):
    filename = CSV_FILE_PATH
    if os.path.exists(filename):
        headers = (['Line'] if print_line_num else [])
        headers += ['Date', 'Time', 'Action', 'Customer']
        table = Table()
        # prev_date = None
        for c in headers:
            table.add_column(c)
        for row in _read_csv_to_list(filename):
            date, time, action, customer = row
            # FIXME: requires newer version of rich
            # if prev_date != None and date != prev_date:
            #     table.add_section()
            prev_date = date
            match action:
                case 'in':
                    col, col_end = '[green]', '[/green]'
                case 'out':
                    col, col_end = '[red]', '[/red]'
            table.add_row(date, time, f"{col}{action}{col_end}", customer)
        print(table)


def delete_entry(filename: str):
    """Delete an entry from the CSV file."""
    list_entries(True)

    entries = []

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for i, row in enumerate(reader, start=1):
            entries.append(row)

    line_number = typer.prompt(
        '\nEnter the line number of the entry you want to delete', type=int)

    typer.confirm("Are you sure you want to delete?", abort=True)
    if 1 <= line_number <= len(entries):
        del entries[line_number - 1]
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(entries)
            print(f"Deleted entry at line {line_number}")
        except:
            print("Failed to delete entry")
    else:
        print(f"Invalid line number: {line_number}")


def find_status_by_date(date: str, filename: str) -> ClockStatus:
    entries = _read_csv_to_list(filename)
    status = ClockStatus.NONE

    for row in entries:
        if row[0] == date:
            if row[2] == 'out':
                status = ClockStatus.OUT
            elif row[2] == 'in' and status != ClockStatus.OUT:
                status = ClockStatus.IN
    return status


def _read_csv_to_list(filename: str) -> list:
    entries = []
    if os.path.exists(filename):
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                entries.append(row)  # Append each row as a list
    else:
        print(f"File {filename} does not exist.")
    return entries


@config_app.command()
def completion(shell: Annotated[str, typer.Option(help="BASH ZSH FISH POWERSHELL", default="zsh")] = "zsh", install: bool = False):
    """
    Generate the completion script for the specified shell.
    """
    if install:
        typer.echo(f"Installing completion script for {shell}")
        typer.completion.install(
            shell=shell, prog_name=app.info.name, complete_var='_TYPER_COMPLETE')
    else:
        print(typer.completion.get_completion_script(
            prog_name=app.info.name, shell=shell, complete_var='_TYPER_COMPLETE'))


if __name__ == "__main__":
    app()
