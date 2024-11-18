import os
import pathlib
import tempfile
import typer
import typer.completion
from datetime import datetime
from enum import Enum
from rich import print
from rich.table import Table
from typing import Annotated
from .local_db import LocalDatabase
from .utils import create_directories, create_file, validate_month


CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE
DEFAULT_TABLE_NAME = f'data_{datetime.now().strftime("%Y")}_{datetime.now().strftime("%m")}'


class ClockStatus(Enum):
    NONE = 0
    IN = 1
    OUT = 2


app = typer.Typer(name="cxz")
config_app = typer.Typer(name="config", help="Configuration reletad commands.")
app.add_typer(config_app)

# typer.completion.completion_init()


def main():
    create_directories(CONFIG_DIR, DATA_DIR)
    if not os.path.exists(CSV_FILE_PATH):
        create_file(CSV_FILE_PATH)
    create_db()
    create_db_table()
    app()


# TODO: Support time and date input / picker
@app.command(name='in')
def clock_in(customer: str = typer.Argument(None)):
    """Clock in for the day."""
    add_entry(customer, 'in')


# TODO: Support time and date input / picker
@app.command(name='out')
def clock_out(customer: str = typer.Argument(None)):
    """Clock out for the day."""
    add_entry(customer, 'out')


@app.command(name="show")
def clock_show(
    month: str = typer.Option(str(datetime.now().strftime('%m'))),
    year: str = typer.Option(str(datetime.now().strftime('%Y')))
):
    """Display clock-in/clock-out records."""
    month = validate_month(month)
    get_rows()


@config_app.command('dir')
def config_dir_command():
    """
    Print the DATA directory path.
    """
    print(DATA_DIR)


@config_app.command("show-tables")
def show_tables():
    """
    List all tables in the database.
    """
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        table = Table()
        table.add_column('Table')
        for row in db.get_all_tables():
            table.add_row(row[0])
        print(table)


@config_app.command("create-db")
def create_db():
    """Create the local database file."""
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        db.create_database()


@config_app.command('create-table')
def create_db_table(
    month: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%m")),
    year: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%Y"))
):
    """Create a new database table."""
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        if not db.create_table(
            table_name=f"data_{year}_{month}",
            columns=["date TEXT", "time TEXT", "action TEXT", "customer TEXT"]
        ):
            print('[red]Database table failed to create[/red]')


@config_app.command()
def drop_table(month: str, year: str):
    """Erase all months' records."""
    table_name = f"data_{year}_{month}"
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        typer.confirm(
            f"You sure you want to delete all entries for the month {month}.{year}?", abort=True)
        if db.delete_table(table_name):
            print(f'[green]Table {table_name} dropped[/green]')
        else:
            print(f'[red]Could not drop table [{table_name}][/red]')


def add_entry(customer: str, action: str):
    if customer is None:
        customer = typer.prompt("Customer")
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        db.insert_row(DEFAULT_TABLE_NAME, (
            str(datetime.now().strftime("%Y-%m-%d")),
            str(datetime.now().strftime('%H:%M')),
            action,
            customer
        ))


def get_rows(print_line_num: bool = False):
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        table = Table()
        if print_line_num:
            table.add_column('')
        table.add_column('Date')
        table.add_column('Time')
        table.add_column('Action')
        table.add_column('Customer')
        for i, row in enumerate(db.read_all_rows(DEFAULT_TABLE_NAME), start=1):
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
        print(table)


@app.command()
def delete():
    """Delete a specific clock-in/clock-out record."""
    get_rows(True)

    entries = []
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        reader = db.read_all_rows(DEFAULT_TABLE_NAME)
        for i, row in enumerate(reader, start=1):
            entries.append((i,)+row)

        line_number = typer.prompt(
            '\nEnter the line number of the entry you want to delete', type=int)

        for entry in entries:
            if entry[0] == line_number:
                _, date, time, action, customer = entry

        typer.confirm("Are you sure you want to delete?", abort=True)

        db.delete_row(DEFAULT_TABLE_NAME,
                      f"date = '{date}' AND time = '{time}' AND action = '{action}' AND customer = '{customer}'")


@app.command()
def status():
    """Display the clock-in/out status for today."""
    date = datetime.now().strftime("%Y-%m-%d")
    match find_status_by_date(date):
        case ClockStatus.NONE:
            print("No clocking entry found for today")
        case ClockStatus.IN:
            print("Found a clock-in entry for today")
        case ClockStatus.OUT:
            print("found clock-out entry for today")


def find_status_by_date(date: str) -> ClockStatus:
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        entries = db.read_all_rows(DEFAULT_TABLE_NAME)

    status = ClockStatus.NONE

    for row in entries:
        if row[0] == date:
            if row[2] == 'out':
                status = ClockStatus.OUT
            elif row[2] == 'in' and status != ClockStatus.OUT:
                status = ClockStatus.IN
    return status


@app.command('edit')
def edit_table(
    month: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%m")),
    year: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%Y"))
):
    """Edit a database's table."""
    table_name = f"data_{year}_{month}"

    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            reader = db.read_all_rows(table_name)
            for row in reader:
                temp_file.write("\t".join(row) + "\n")

        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} {temp_file.name}")

        with open(temp_file.name, "r") as updated_file:
            updated_rows = [line.strip().split("\t")
                            for line in updated_file.readlines()]

        db.delete_table(table_name)
        db.create_table(
            table_name, ["date TEXT", "time TEXT", "action TEXT", "customer TEXT"])
        for row in updated_rows:
            db.insert_row(table_name, row)

        print(f"[green]Table {table_name} updated[/green]")


if __name__ == "__main__":
    app()
