import os
import pathlib
import pkg_resources
import subprocess
import tempfile
import typer
import typer.completion
from datetime import datetime
from rich import print
from rich.table import Table
from typing import Annotated, Optional
from .local_db import LocalDatabase
from .utils import (
    add_entry,
    ClockStatus,
    create_directories,
    create_file,
    find_status_by_date,
    get_rows,
    get_sum,
    validate_month,
)
from statistics import median

CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE
DEFAULT_TABLE_NAME = (
    f'data_{datetime.now().strftime("%Y")}_{datetime.now().strftime("%m")}'
)


app = typer.Typer(name="cxz")
config_app = typer.Typer(name="config", help="Configuration reletad commands.")
app.add_typer(config_app)


# TODO: Support time and date input / picker
@app.command(name="in")
def clock_in(customer: str = typer.Argument(None)):
    """Clock in for the day."""
    add_entry(customer, "in", CONFIG_DIR, DEFAULT_TABLE_NAME)


# TODO: Support time and date input / picker
@app.command(name="out")
def clock_out(customer: str = typer.Argument(None)):
    """Clock out for the day."""
    add_entry(customer, "out", CONFIG_DIR, DEFAULT_TABLE_NAME)


@app.command(name="task")
def clock_task(customer: str = typer.Argument(None)):
    """Mark a task in the timetable."""
    add_entry(customer, "task", CONFIG_DIR, DEFAULT_TABLE_NAME)


@app.command(name="show")
def clock_show(
    month: str = typer.Option(str(datetime.now().strftime("%m"))),
    year: str = typer.Option(str(datetime.now().strftime("%Y"))),
):
    """Display clock-in/clock-out records."""
    valid_month = validate_month(month)
    _month = (
        valid_month
        if valid_month == median([1, 12, valid_month])
        else datetime.now().strftime("%m")
    )
    _year = year if year not in (None, "") else datetime.now().strftime("%Y")
    table_name = f"data_{_year}_{_month}"
    try:
        print(get_rows(CONFIG_DIR, table_name))
    except Exception:
        print(f"Failed to retrieve data for {_month}.{_year}")


@app.command(name="sum")
def clock_sum(
    customer: str = None,
    month: str = typer.Option(str(datetime.now().strftime("%m"))),
    year: str = typer.Option(str(datetime.now().strftime("%Y"))),
):
    """Summerize clocked time for a customer"""
    print(
        get_sum(
            customer=customer or typer.prompt("Customer"),
            config_dir=CONFIG_DIR,
            table_name=DEFAULT_TABLE_NAME,
        )
    )


@config_app.command("dir")
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
        table.add_column("Table")
        for row in db.get_all_tables():
            table.add_row(row[0])
        print(table)


@config_app.command("create-db")
def create_db():
    """Create the local database file."""
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        db.create_database()


@config_app.command("create-table")
def create_db_table(
    month: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%m")
    ),
    year: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%Y")
    ),
):
    """Create a new database table."""
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        if not db.create_table(
            table_name=f"data_{year}_{month}",
            columns=["date TEXT", "time TEXT", "action TEXT", "customer TEXT"],
        ):
            print("[red]Database table failed to create[/red]")


@config_app.command()
def drop_table(month: str, year: str):
    """Erase all months' records."""
    table_name = f"data_{year}_{month}"
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        typer.confirm(
            f"You sure you want to delete all entries for the month {month}.{year}?",
            abort=True,
        )
        if db.delete_table(table_name):
            print(f"[green]Table {table_name} dropped[/green]")
        else:
            print(f"[red]Could not drop table [{table_name}][/red]")


@app.command()
def delete():
    """Delete a specific clock-in/clock-out record."""
    print(get_rows(CONFIG_DIR, DEFAULT_TABLE_NAME, True))

    entries = []
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        reader = db.read_all_rows(DEFAULT_TABLE_NAME)
        for i, row in enumerate(reader, start=1):
            entries.append((i,) + row)

        line_number = typer.prompt(
            "\nEnter the line number of the entry you want to delete", type=int
        )

        for entry in entries:
            if entry[0] == line_number:
                _, date, time, action, customer = entry

        typer.confirm("Are you sure you want to delete?", abort=True)

        db.delete_row(
            DEFAULT_TABLE_NAME,
            f"date = '{date}' AND time = '{time}' AND action = '{action}' AND customer = '{customer}'",
        )


@app.command()
def status():
    """Display the clock-in/out status for today."""
    date = datetime.now().strftime("%Y-%m-%d")
    match find_status_by_date(date, CONFIG_DIR, DEFAULT_TABLE_NAME):
        case ClockStatus.NONE:
            print("No clocking entry found for today")
        case ClockStatus.IN:
            print("Found a clock-in entry for today")
        case ClockStatus.OUT:
            print("found clock-out entry for today")


@app.command("edit")
def edit_table(
    month: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%m")
    ),
    year: Annotated[str, typer.Option(..., prompt=True)] = str(
        datetime.now().strftime("%Y")
    ),
    editor: Annotated[str, typer.Option(..., prompt=True)] = None,
):
    """Edit a database's table."""
    table_name = f"data_{year}_{month}"

    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            reader = db.read_all_rows(table_name)
            for row in reader:
                temp_file.write("\t".join(row) + "\n")

        if editor == None:
            editor = os.environ.get("CXZ_EDITOR", "nano")

        match editor:
            case "code":
                subprocess.Popen([editor, temp_file.name])
                subprocess.call([editor, "--wait", temp_file.name])
            case _:
                os.system(f"{editor} {temp_file.name}")

        with open(temp_file.name, "r") as updated_file:
            updated_rows = [
                line.strip().split("\t") for line in updated_file.readlines()
            ]

        db.delete_table(table_name)
        db.create_table(
            table_name, ["date TEXT", "time TEXT", "action TEXT", "customer TEXT"]
        )
        for row in updated_rows:
            db.insert_row(table_name, row)

        print(f"[green]Table {table_name} updated[/green]")


def _version_callback(value: bool) -> None:
    if value:
        print(pkg_resources.get_distribution("cloxz").version)
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the app's version.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    create_directories(CONFIG_DIR, DATA_DIR)
    if not os.path.exists(CSV_FILE_PATH):
        create_file(CSV_FILE_PATH)
    create_db()
    create_db_table()


if __name__ == "__main__":
    app()
