import calendar
import os
import typer
from datetime import datetime
from enum import Enum
from rich.table import Table
from .local_db import LocalDatabase


class ClockStatus(Enum):
    NONE = 0
    IN = 1
    OUT = 2


def create_directories(config_dir: str, data_dir: str):
    """Create the necessary directories if they don't exist."""
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


def create_file(filename: str):
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


def add_entry(customer: str, action: str, config_dir: str, table_name: str):
    if customer is None:
        customer = typer.prompt("Customer")
    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        db.insert_row(table_name, (
            str(datetime.now().strftime("%Y-%m-%d")),
            str(datetime.now().strftime('%H:%M')),
            action,
            customer
        ))


def get_rows(config_dir: str, table_name: str, print_line_num: bool = False):
    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        table = Table()
        if print_line_num:
            table.add_column('')
        table.add_column('Date')
        table.add_column('Time')
        table.add_column('Action')
        table.add_column('Customer')
        for i, row in enumerate(db.read_all_rows(table_name), start=1):
            id_, timestamp, action, customer = row
            match action:
                case 'in':
                    action = '[green]in[/green]'
                case 'out':
                    action = '[red]out[/red]'
            if print_line_num:
                table.add_row(str(i), str(id_), timestamp, action, customer)
            else:
                table.add_row(str(id_), timestamp, action, customer)
        return (table)


def find_status_by_date(date: str, config_dir: str, table_name: str) -> ClockStatus:
    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        entries = db.read_all_rows(table_name)

    status = ClockStatus.NONE

    for row in entries:
        if row[0] == date:
            if row[2] == 'out':
                status = ClockStatus.OUT
            elif row[2] == 'in' and status != ClockStatus.OUT:
                status = ClockStatus.IN
    return status
