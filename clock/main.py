import calendar
import click
import csv
import os
from datetime import datetime
import pathlib

CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE

ACTIONS = {
    'in': 'Add a clock-in item',
    'out': 'Add a clock-out item',
    'modify': 'Modify an existing entry',
    'list': 'List all items',
    'delete': 'Delete an item',
    'pwd': 'Prints the data directory path'
}


def create_directories():
    """Create the necessary directories if they don't exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def print_csv_directory():
    """Print the CSV file directory path."""
    click.echo(DATA_DIR)


@click.command()
@click.argument('action', type=click.Choice(list(ACTIONS.keys())), required=False)
@click.argument('text', type=str, required=False)
@click.pass_context
def main(ctx, action: str, text: str):
    create_directories()
    filename = CSV_FILE_PATH

    if not os.path.exists(filename):
        create_file()

    if not action:
        action = click.prompt('Choose an action',
                              type=click.Choice(list(ACTIONS.keys())))
        if action in ['in', 'out']:
            text = click.prompt('Enter text for the clock entry', type=str)
        elif action == 'delete':
            delete_entry(filename)
            return
        ctx.invoke(main, action=action, text=text)
        return

    match action:
        case "pwd":
            print_csv_directory()
        case "in" | "out":
            add_clock_entry(filename, text, action)
        case "modify":
            modify_entry(filename)
        case "list":
            month = click.prompt(
                'Enter the month (name, number)', type=validate_month, default="current")
            list_entries(month)
        case "delete":
            delete_entry(filename)


def create_file():
    filename = CSV_FILE_PATH
    if not os.path.exists(filename):
        try:
            with open(filename, 'w+'):
                pass
        except:
            click.echo("Failed to create clock file")
            return
        click.echo(f"Created {filename}")
    else:
        click.echo(f"{filename} already exists.")


def add_clock_entry(filename: str, customer: str, action: str):
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([date, time, action, customer])


def list_entries(month: int):
    filename = CSV_FILE_PATH
    if os.path.exists(filename):
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            click.echo(click.style(
                f"Entries for {calendar.month_name[month]}:", fg='blue', bold=True))
            click.echo(click.style(
                "Date | Time | Action | Customer", fg='green', bold=True))
            for row in reader:
                date, time, action, customer = row
                if datetime.strptime(date, '%Y-%m-%d').month == month:
                    click.echo(click.style(
                        f"{date:>10} | {time:>8} | {action:>6} | {customer}", fg='white'))


def validate_month(month: str) -> int:
    if month.lower() == 'current':
        return datetime.now().month
    try:
        month_num = int(month)
        if 1 <= month_num <= 12:
            return month_num
        else:
            raise click.BadParameter(f"Invalid month number: {month}")
    except ValueError:
        month_num = list(calendar.month_name).index(month.capitalize())
        if month_num > 0:
            return month_num
        else:
            raise click.BadParameter(f"Invalid month name: {month}")


def delete_entry(filename: str):
    """Delete an entry from the CSV file."""
    entries = []

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        click.echo(click.style(
            "Entries:", fg='blue', bold=True))
        click.echo(click.style(
            "Line | Date | Time | Action | Customer", fg='green', bold=True))
        for i, row in enumerate(reader, start=1):
            date, time, action, customer = row
            click.echo(click.style(
                f"{i:>5} | {date:>10} | {time:>8} | {action:>6} | {customer}", fg='white'))
            entries.append(row)

    line_number = click.prompt(
        '\nEnter the line number of the entry you want to delete', type=int)

    if 1 <= line_number <= len(entries):
        del entries[line_number - 1]
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(entries)
            click.echo(f"Deleted entry at line {line_number}")
        except:
            click.echo("Failed to delete entry")
    else:
        click.echo(f"Invalid line number: {line_number}")


def modify_entry(filename: str):
    """Modify an entry in the CSV file."""
    entries = []

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        click.echo(click.style(
            "Entries:", fg='blue', bold=True))
        click.echo(click.style(
            "Line | Date | Time | Action | Customer", fg='green', bold=True))
        for i, row in enumerate(reader, start=1):
            date, time, action, customer = row
            click.echo(click.style(
                f"{i:>5} | {date:>10} | {time:>8} | {action:>6} | {customer}", fg='white'))
            entries.append(row)

    line_number = click.prompt(
        '\nEnter the line number of the entry you want to modify', type=int)

    if 1 <= line_number <= len(entries):
        click.echo(f"Current entry: {entries[line_number - 1]}")
        new_date = click.prompt(
            'Enter the new date (YYYY-MM-DD)', type=str, default=entries[line_number - 1][0])
        new_time = click.prompt(
            'Enter the new time (HH:MM:SS)', type=str, default=entries[line_number - 1][1])
        new_action = click.prompt(
            'Enter the new action', type=str, default=entries[line_number - 1][2])
        new_customer = click.prompt(
            'Enter the new customer', type=str, default=entries[line_number - 1][3])

        entries[line_number - 1] = [new_date,
                                    new_time, new_action, new_customer]

        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(entries)
            click.echo(f"Modified entry at line {line_number}")
        except:
            click.echo("Failed to modify entry")
    else:
        click.echo(f"Invalid line number: {line_number}")
