import calendar
import csv
import os
import pathlib
import typer
from datetime import datetime
from enum import Enum
from .utils import add_clock_entry
from rich import print

CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE

ACTIONS = {
    'in': 'Record a clock-in entry',
    'out': 'Record a clock-out entry',
    'modify': 'Update an existing entry',
    'list': 'Display all recorded entries',
    'delete': 'Remove a specified entry',
    'pwd': 'Display the path to the data directory',
    'status': 'Verify the clocking status for the current day'
}


class ClockStatus(Enum):
    NONE = 0
    IN = 1
    OUT = 2


app = typer.Typer(name="cloxz-cli")


def create_directories():
    """Create the necessary directories if they don't exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def print_csv_directory():
    """Print the CSV file directory path."""
    print(DATA_DIR)


def main():
    create_directories()
    filename = CSV_FILE_PATH
    if not os.path.exists(filename):
        create_file()
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


@app.command(name="list")
def clock_list(month: str = typer.Option("current", prompt=True)):
    month = validate_month(month)
    list_entries(month)


@app.command()
def pwd():
    print_csv_directory()


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


def create_file():
    filename = CSV_FILE_PATH
    if not os.path.exists(filename):
        try:
            with open(filename, 'w+'):
                pass
        except:
            print("Failed to create clock file")
            return
        print(f"Created {filename}")
    else:
        print(f"{filename} already exists.")


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


def validate_month(month: str) -> int:
    if month.lower() == 'current':
        return datetime.now().month
    try:
        month_num = int(month)
        if 1 <= month_num <= 12:
            return month_num
        else:
            print(f"Invalid month number: {month}")
            raise typer.Exit(code=1)
    except ValueError:
        month_num = list(calendar.month_name).index(month.capitalize())
        if month_num > 0:
            return month_num
        else:
            print(f"Invalid month name: {month}")
            raise typer.Exit(code=1)


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


# def on_press(key, options):
#     global selected_index, selected_char_index

#     if key == keyboard.Key.up:
#         selected_index = (selected_index - 1) % len(options)
#         selected_char_index = min(
#             selected_char_index, len(options[selected_index]) - 1)
#     elif key == keyboard.Key.down:
#         selected_index = (selected_index + 1) % len(options)
#         selected_char_index = min(
#             selected_char_index, len(options[selected_index]) - 1)
#     elif key == keyboard.Key.left:
#         selected_char_index = max(selected_char_index - 1, 0)
#     elif key == keyboard.Key.right:
#         selected_char_index = min(
#             selected_char_index + 1, len(options[selected_index]) - 1)
#     elif key == keyboard.Key.enter:
#         return False
#     elif key == keyboard.Key.backspace:
#         if selected_char_index > 0:
#             options[selected_index] = options[selected_index][:selected_char_index-1] + \
#                 options[selected_index][selected_char_index:]
#             selected_char_index -= 1
#     elif key == keyboard.Key.delete:
#         if selected_char_index < len(options[selected_index]):
#             options[selected_index] = options[selected_index][:selected_char_index] + \
#                 options[selected_index][selected_char_index+1:]
#     elif hasattr(key, 'char') and key.char is not None:
#         # Handle regular character input
#         # Limit the maximum length of the option
#         if len(options[selected_index]) < 50:
#             options[selected_index] = options[selected_index][:selected_char_index] + \
#                 key.char + \
#                 options[selected_index][selected_char_index:]
#             selected_char_index += 1

#     return True  # Return True to continue the listener


# def display_options(entries: list):
#     global selected_index, selected_char_index, options

#     options = entries  # Assign the entries variable to the options variable
#     options.append("\nUse arrow keys to nevigate through text")

#     screen = curses.initscr()
#     curses.curs_set(2)  # Set cursor visibility to 2 (visible)
#     height, width = screen.getmaxyx()

#     selected_index = 0
#     selected_char_index = 0

#     with keyboard.Listener(on_press=lambda key: on_press(key, options)) as listener:
#         while True:
#             screen.clear()
#             for i, option in enumerate(options):
#                 if i == selected_index:
#                     # Convert the list to a string
#                     screen.addstr(i, 0, ''.join(option))
#                     screen.chgat(i, selected_char_index, 1, curses.A_REVERSE)
#                     screen.move(i, selected_char_index)
#                 else:
#                     # Convert the list to a string
#                     screen.addstr(i, 0, ''.join(option))
#             screen.refresh()

#             key = screen.getch()
#             if key == curses.KEY_ENTER or key in [10, 13]:
#                 break

#     # Clean up the curses screen
#     curses.endwin()
#     listener.stop()
#     return options[:len(options)-1]


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


# def read_csv_entries(filename: str) -> list:
#     entries = []
#     if os.path.exists(filename):
#         with open(filename, 'r', newline='') as csvfile:
#             reader = csv.reader(csvfile)
#             entries = [','.join(row) for row in reader]
#     return entries


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
