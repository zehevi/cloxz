import os
import pathlib
from importlib import metadata
import subprocess
import tempfile
import calendar
import typer
import typer.completion
from datetime import datetime
from rich import print
from rich.table import Table
from rich import box
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
    get_table_name,
)
from statistics import median

CONFIG_DIR = pathlib.Path.home() / ".config/clockz"
DATA_DIR = CONFIG_DIR / "data"
CSV_FILE = f"{datetime.now().strftime('%B')}.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILE


app = typer.Typer(name="cxz")
config_app = typer.Typer(name="config", help="Configuration reletad commands.")
app.add_typer(config_app)

def get_default_table_name() -> str:
    """Returns the table name for the current month and year."""
    return f'data_{datetime.now().strftime("%Y")}_{datetime.now().strftime("%m")}'


def _get_table_for_date(date: str | None) -> str:
    """Get table name for a given date string, creating it if necessary."""
    if not date:
        return get_default_table_name()

    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        month, year = str(parsed_date.month), str(parsed_date.year)
        # This creates the table if it doesn't exist, as it's called non-interactively.
        create_db_table(month=month, year=year)
        return get_table_name(month, year)
    except ValueError:
        print("[red]Error: Date must be in YYYY-MM-DD format.[/red]")
        raise typer.Exit(1)


def _get_clock_entry_details(
    note: str | None, date: str | None, time: str | None
) -> tuple[str, str | None, str | None]:
    """If note is not provided, prompt for note, and any missing date/time."""
    if note is None:
        # Interactive mode
        note = typer.prompt("Note")
        date = date or typer.prompt(
            "Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d")
        )
        time = time or typer.prompt(
            "Time (HH:MM)", default=datetime.now().strftime("%H:%M")
        )
    return note, date, time


@app.command(name="in")
def clock_in(
    note: str = typer.Argument(None, help="A note about the clock-in event."),
    date: Annotated[
        str,
        typer.Option(
            "--date",
            "-d",
            help="Date of the entry in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = None,
    time: Annotated[
        str,
        typer.Option(
            "--time",
            "-t",
            help="Time of the entry in HH:MM format. Defaults to now.",
        ),
    ] = None,
):
    """Clock in for the day."""
    note, date, time = _get_clock_entry_details(note, date, time)
    table_name = _get_table_for_date(date)
    add_entry(note, "in", CONFIG_DIR, table_name, date, time)


@app.command(name="out")
def clock_out(
    note: str = typer.Argument(None, help="A note about the clock-out event."),
    date: Annotated[
        str,
        typer.Option(
            "--date",
            "-d",
            help="Date of the entry in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = None,
    time: Annotated[
        str,
        typer.Option(
            "--time",
            "-t",
            help="Time of the entry in HH:MM format. Defaults to now.",
        ),
    ] = None,
):
    """Clock out for the day."""
    note, date, time = _get_clock_entry_details(note, date, time)
    table_name = _get_table_for_date(date)
    add_entry(note, "out", CONFIG_DIR, table_name, date, time)


@app.command(name="task")
def clock_task(
    note: str = typer.Argument(None, help="A note about the task."),
    date: Annotated[
        str,
        typer.Option(
            "--date",
            "-d",
            help="Date of the entry in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = None,
    time: Annotated[
        str,
        typer.Option(
            "--time",
            "-t",
            help="Time of the entry in HH:MM format. Defaults to now.",
        ),
    ] = None,
):
    """Mark a task in the timetable."""
    note, date, time = _get_clock_entry_details(note, date, time)
    table_name = _get_table_for_date(date)
    add_entry(note, "task", CONFIG_DIR, table_name, date, time)


@app.command(name="show")
def clock_show(
    month: str = typer.Option(str(datetime.now().strftime("%m"))),
    year: str = typer.Option(str(datetime.now().strftime("%Y"))),
):
    """Display clock-in/clock-out records."""
    table_name = get_table_name(month, year)
    _year, _month = table_name.lstrip("data_").split("_")
    month_name = calendar.month_name[int(_month)]
    title = f"Clock Records for {month_name} {_year}"

    table = get_rows(CONFIG_DIR, table_name, title=title)
    if table is None:
        print(f"Failed to retrieve data for {month_name} {_year}. The table might not exist.")
    else:
        print(table)

@app.command(name="sum")
def clock_sum(
    note: str = None,
    month: str = typer.Option(str(datetime.now().strftime("%m"))),
    year: str = typer.Option(str(datetime.now().strftime("%Y"))),
):
    """Summarize clocked time for a specific note."""
    print(
        get_sum(
            note=note or typer.prompt("Note"),
            config_dir=CONFIG_DIR,
            table_name=get_table_name(month, year),
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
        table = Table(title="Database Tables", box=box.ROUNDED)
        table.add_column("Table Name")
        all_tables = db.get_all_tables()
        if all_tables:
            for row in all_tables:
                table.add_row(row[0])
        else:
            table.add_row("[italic]No tables found.[/italic]")
        print(table)


@config_app.command("create-db")
def create_db():
    """Create the local database file."""
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        db.create_database()


@config_app.command("create-table")
def create_db_table(
    month: Annotated[str, typer.Option(..., prompt=True)],
    year: Annotated[str, typer.Option(..., prompt=True)],
):
    """Create a new database table."""
    valid_month = validate_month(month)
    padded_month = f"{valid_month:02d}"
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        if not db.create_table(
            table_name=f"data_{year}_{padded_month}",
            columns=["date TEXT", "time TEXT", "action TEXT", "note TEXT"],
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
    table_name = get_default_table_name()
    _year, _month = table_name.lstrip("data_").split("_")
    month_name = calendar.month_name[int(_month)]
    title = f"Clock Records for {month_name} {_year}"

    table = get_rows(CONFIG_DIR, table_name, print_line_num=True, title=title)

    if table is None or table.row_count == 0:
        print(f"No records found for {month_name} {_year} to delete.")
        raise typer.Exit()

    print(table)

    entries = []
    with LocalDatabase.Database(database_file=f"{CONFIG_DIR}/database.db") as db:
        reader = db.read_all_rows(table_name)
        for i, row in enumerate(reader, start=1):
            entries.append((i,) + row)

        line_number = typer.prompt(
            "\nEnter the line number of the entry you want to delete", type=int
        )

        entry_to_delete = None
        for entry in entries:
            if entry[0] == line_number:
                entry_to_delete = entry
                break

        if not entry_to_delete:
            print(f"[red]Error: Invalid line number {line_number}.[/red]")
            raise typer.Exit(1)

        _, date, time, action, note = entry_to_delete

        typer.confirm(f"Are you sure you want to delete entry {line_number}?", abort=True)

        db.delete_row(
            table_name,
            "date = ? AND time = ? AND action = ? AND note = ?",
            (date, time, action, note),
        )
        print(f"[green]Entry {line_number} deleted successfully.[/green]")

@app.command()
def status():
    """Display the clock-in/out status for today."""
    date = datetime.now().strftime("%Y-%m-%d")
    match find_status_by_date(date, CONFIG_DIR, get_default_table_name()):
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
            table_name, ["date TEXT", "time TEXT", "action TEXT", "note TEXT"]
        )
        for row in updated_rows:
            db.insert_row(table_name, row)

        print(f"[green]Table {table_name} updated[/green]")


def _version_callback(value: bool) -> None:
    if value:
        try:
            print(metadata.version("cloxz"))
        except metadata.PackageNotFoundError:
            print("Version for 'cloxz' not found. Is it installed?")
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
    # The create_db() call is redundant.
    # Always ensure the table for the current month exists on startup.
    create_db_table(month=datetime.now().strftime('%m'),
                    year=datetime.now().strftime('%Y'))
