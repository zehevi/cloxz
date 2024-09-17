import calendar
import click
import csv
import os
from datetime import datetime

CSV_FILE = f"{datetime.now().strftime('%B')}.csv"

ACTIONS = {
    'add-in': 'Add a clock-in item',
    'add-out': 'Add a clock-out item',
    'list': 'List all items',
    'delete': 'Delete an item'
}


@click.command()
@click.argument('action', type=click.Choice(list(ACTIONS.keys())), required=False)
@click.pass_context
def main(ctx, action: str):
    filename = CSV_FILE

    if not os.path.exists(filename):
        create_file()

    if not action:
        action = click.prompt('Choose an action',
                              type=click.Choice(list(ACTIONS.keys())))
        ctx.invoke(main, action=action)
        return

    match action:
        case "add-in" | "add-out":
            text = click.prompt('Enter text for the clock entry', type=str)
            add_clock_entry(filename, text, action)
        case "list":
            month = click.prompt(
                'Enter the month (name, number)', type=validate_month, default="current")
            list_entries(month)


def create_file():
    filename = CSV_FILE
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
    clock_action = "in" if action == "add-in" else "out"

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([date, time, clock_action, customer])


def list_entries(month: int):
    filename = CSV_FILE
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
    else:
        pass


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


if __name__ == "__main__":
    main()
