"""
It contains methods for manipulating with date and time formats and values.
"""

import datetime

def convert_date(date_input):
    '''
    Converts date_input and returns it to format day.month.year
    '''
    current_year = datetime.datetime.now().year  # Get the current year

    # Determine the date format based on the delimiter used
    delimiter = '-' if '-' in date_input else '.' if '.' in date_input else None
    if delimiter is None:
        raise ValueError("Invalid date format")
    
    # Parse the date input using the appropriate format
    date_parts = date_input.split(delimiter)
    if len(date_parts) == 2:  # If the user input does not include the year
        day, month = map(int, date_parts)
        year = current_year
    elif len(date_parts) == 3:  # If the user input includes day, month, and year
        day, month, year = map(int, date_parts)
    else:
        raise ValueError("Invalid date format")
    
    if year < 100:
        year += 2000  # Add 2000 to the two-digit year to get the full year
    return datetime.datetime(year, month, day).strftime("%d.%m.%Y")

def convert_time(time_input):
    # Convert time input
    if '-' in time_input:
        time_input = time_input.replace("-", ":")

    time_obj = datetime.datetime.strptime(time_input, "%H:%M").time()
    return time_obj.strftime("%H:%M")

def convert_to_datetime(date_input, time_input):
    formatted_date = convert_date(date_input)
    formatted_time = convert_time(time_input)
    datetime_obj = datetime.datetime.strptime(f"{formatted_date} {formatted_time}", "%d.%m.%Y %H:%M")
    return datetime_obj

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
