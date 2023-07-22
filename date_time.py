"""
It contains methods for manipulating with date and time formats and values.
"""

import datetime


def convert_to_datetime(date_input, time_input):
    '''
    Function takes users data and time input and converts it to datetime format.
    '''
    # Determine the date format based on the delimiter used
    delimiter = '-' if '-' in date_input else '.' if '.' in date_input else None
    if delimiter is None:
        raise ValueError("Invalid date format")
    
    # Parse the date input using the appropriate format
    day, month, year = map(int, date_input.split(delimiter))
    if year < 100:
        year += 2000  # Add 2000 to the two-digit year to get the full year
    date = datetime.datetime(year, month, day)

    # Convert time input
    if '-' in time_input:
        time = datetime.datetime.strptime(time_input.replace("-", ":"), "%H:%M")
    elif ':' in time_input:
        time = datetime.datetime.strptime(time_input, "%H:%M")
    else:
        raise ValueError("Invalid time format")

    datetime_value = datetime.datetime.combine(date.date(), time.time())
    
    return datetime_value

def get_remaining_time(datetime_value):
    time_delta = None
    current_datetime = datetime.datetime.now()

    if datetime_value > current_datetime:
        time_difference = datetime_value - current_datetime
        if time_difference <= datetime.timedelta(hours=24) and time_difference > datetime.timedelta(hours=4):
            time_delta = 24
        elif time_difference <= datetime.timedelta(hours=4) and time_difference > datetime.timedelta(hours=1):
            time_delta = 4
        elif time_difference <= datetime.timedelta(hours=1):
            time_delta = 1
    
    return time_delta
