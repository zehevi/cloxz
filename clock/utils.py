import calendar
import os
import typer
from datetime import datetime


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
