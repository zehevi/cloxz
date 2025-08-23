from datetime import datetime, timedelta
import calendar
import os
import typer
from enum import Enum
from rich.table import Table
from rich import box
from statistics import median
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
            with open(filename, "w+"):
                pass
        except:
            print("Failed to create clock file")
            return
        print(f"Created {filename}")
    else:
        print(f"{filename} already exists.")


def validate_month(month: str) -> int:
    if month.lower() == "current":
        return datetime.now().month
    try:
        if month.startswith("-"):
            month = datetime.now().month - int(month[1:])

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


def add_entry(
    note: str,
    action: str,
    config_dir: str,
    table_name: str,
    date: str | None = None,
    time: str | None = None,
):
    entry_date = date or datetime.now().strftime("%Y-%m-%d")
    entry_time = time or datetime.now().strftime("%H:%M")

    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        db.insert_row(
            table_name,
            (entry_date, entry_time, action, note),
        )


def get_rows(
    config_dir: str, table_name: str, print_line_num: bool = False, title: str = None
):
    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        rows = db.read_all_rows(table_name)
        if rows is None:
            return None

        table = Table(title=title, box=box.ROUNDED)
        if print_line_num:
            table.add_column("")
        table.add_column("Date")
        table.add_column("Time")
        table.add_column("Action")
        table.add_column("Note")
        for i, row in enumerate(rows, start=1):
            date, time, action, note = row
            match action:
                case "in":
                    action = "[green]in[/green]"
                case "out":
                    action = "[red]out[/red]"
                case "task":
                    action = "[blue]task[/blue]"
            if print_line_num:
                table.add_row(str(i), date, time, action, note)
            else:
                table.add_row(date, time, action, note)
        return table


def find_status_by_date(date: str, config_dir: str, table_name: str) -> ClockStatus:
    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        entries = db.read_all_rows(table_name)
    if not entries:
        return ClockStatus.NONE

    # Filter for the given date and get the last action, since entries are now sorted by date and time
    day_entries = [
        row for row in entries if row[0] == date and row[2] in ("in", "out")
    ]

    if not day_entries:
        return ClockStatus.NONE

    last_action = day_entries[-1][2]
    return ClockStatus.IN if last_action == "in" else ClockStatus.OUT


def get_sum(note: str, config_dir: str, table_name: str) -> str:
    with LocalDatabase.Database(database_file=f"{config_dir}/database.db") as db:
        # Check if the number of clock-ins and clock-outs are equal
        check_query = f"""
            SELECT
                COUNT(CASE WHEN "action" = 'in' THEN 1 END) AS total_in,
                COUNT(CASE WHEN "action" = 'out' THEN 1 END) AS total_out
            FROM
                "{table_name}"
            WHERE
                "note" = ?;
        """
        check_result = db.execute_query(check_query, (note,))
        if check_result:
            total_in = check_result[0][0]
            total_out = check_result[0][1]
            if total_in != total_out:
                return "Error: Unequal number of clock-ins and clock-outs"

        # Calculate the total time
        # FIXME: Needs refactoring, does not calculate time over 24 hours well
        query = f"""
            SELECT
                "note",
                SUM(CASE WHEN "action" = 'in' THEN CAST(SUBSTR("time", 1, 2) AS INTEGER) * 60 + CAST(SUBSTR("time", 4, 2) AS INTEGER) ELSE 0 END) AS total_in_minutes,
                SUM(CASE WHEN "action" = 'out' THEN CAST(SUBSTR("time", 1, 2) AS INTEGER) * 60 + CAST(SUBSTR("time", 4, 2) AS INTEGER) ELSE 0 END) AS total_out_minutes
            FROM
                "{table_name}"
            WHERE
                "note" = ?
            GROUP BY
                "note";
        """
        result = db.execute_query(query, (note,))
        if result:
            total_in_minutes = result[0][1]
            total_out_minutes = result[0][2]
            total_time_minutes = total_out_minutes - total_in_minutes
            hours = int(total_time_minutes // 60)
            minutes = int(total_time_minutes % 60)
            return f"{hours}:{minutes:02d}"
        else:
            return "0:00"


def get_table_name(month: str | int, year: str | int) -> str:
    # validate_month expects a string
    valid_month = validate_month(str(month))
    _month = f"{valid_month:02d}"
    _year = year if year not in (None, "") else datetime.now().strftime("%Y")
    return f"data_{_year}_{_month}"
