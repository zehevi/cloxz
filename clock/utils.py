import csv
from datetime import datetime


def add_clock_entry(filename: str, customer: str, action: str):
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([date, time, action, customer])
