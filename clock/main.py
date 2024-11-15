import calendar
import csv
import os
import pathlib
import typer
from datetime import datetime
from enum import Enum
from .utils import add_clock_entry, create_directories, create_file, validate_month
from rich import print

CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE


class ClockStatus(Enum):
    NONE = 0
    IN = 1
    OUT = 2


app = typer.Typer(name="cloxz-cli")


def main():
    create_directories(CONFIG_DIR, DATA_DIR)
    filename = CSV_FILE_PATH
    if not os.path.exists(filename):
        create_file(CSV_FILE_PATH)
    app()


@app.command(name="in")
def clock_in(customer: str = typer.Argument(None)):
    if customer is None:
        customer = typer.prompt("Customer")
    add_clock_entry(CSV_FILE_PATH, customer, "in")


@app.command(name="out")
def clock_out(customer: str = typer.Argument(None)):
    if customer is None:
        customer = typer.prompt("Customer")
    add_clock_entry(CSV_FILE_PATH, customer, "out")


@app.command(name="show")
def clock_show(month: str = typer.Option("current", prompt=True)):
    month = validate_month(month)
    list_entries(month)


@app.command()
def pwd():
    print(DATA_DIR)


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


def list_entries(month: int, print_line_num: bool = False):
    filename = CSV_FILE_PATH
    if os.path.exists(filename):
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            print(f"Entries for {calendar.month_name[month]}:")
            print("Line | " if print_line_num else "",
                  "Date | Time | Action | Customer")
            for i, row in enumerate(reader, start=1):
                date, time, action, customer = row

                col, col_end = '[grey]', '[/grey]'
                match action:
                    case 'in':
                        col, col_end = '[green]', '[/green]'
                    case 'out':
                        col, col_end = '[red]', '[/red]'

                if datetime.strptime(date, '%Y-%m-%d').month == month:
                    if print_line_num:
                        print(
                            f"{i:>5} | {date:>10} | {time:>8} | {col}{action:>6}{col_end} | {customer}")
                    else:
                        print(
                            f"{date:>10} | {time:>8} | {col}{action:>6}{col_end} | {customer}")


def delete_entry(filename: str):
    """Delete an entry from the CSV file."""
    list_entries(validate_month('current'), True)

    entries = []

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for i, row in enumerate(reader, start=1):
            entries.append(row)

    line_number = typer.prompt(
        '\nEnter the line number of the entry you want to delete', type=int)

    if typer.confirm("Are you sure you want to delete?", default=False):
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
    else:
        print("[yellow]Canceled[/yellow]")


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
