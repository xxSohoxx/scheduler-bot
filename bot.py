import logging
import os
import time
import datetime
from functools import wraps
import telebot
import threading
import gspread
from flask import Flask, jsonify
import schedule

from date_time import convert_to_datetime, get_remaining_time, convert_date, convert_time
from weather_check import weather_one_time_forecast


TOKEN = os.environ.get('TOKEN')
MY_CHAT_ID = int(os.environ.get('CHAT_ID'))

# Google Sheets credentials
GOOGLE_SHEETS_CREDS = os.environ.get('GOOGLE_SHEETS_CREDS')
GOOGLE_SPREADSHEET_ID = os.environ.get('GOOGLE_SPREADSHEET_ID')
GOOGLE_SHEET_NAME = os.environ.get('GOOGLE_SHEET_NAME')
GOOGLE_BIRTHDAY_SHEET_NAME = "Birthdays"

scope = ['https://www.googleapis.com/auth/spreadsheets']

help_message = '''You can run the following commands:
    /help - get help and support
    /w    - get weather forecast (currently for Novi-Sad only)
    /list - get all future events
    /event EVENT_NAME DATE TIME - add a new event 
       example: "/event Doctor_appointment 01-11-2023 12:20"
    '''

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create an instance of the bot
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Connect to Google Sheets
def connect_to_google_sheet(sheet_name):
    try:
        gc = gspread.service_account(GOOGLE_SHEETS_CREDS)
        spreadsheet = gc.open_by_key(GOOGLE_SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet
    except Exception as e:
        logger.error(f"An error occurred while connecting : {str(e)}")

event_worksheet = connect_to_google_sheet(GOOGLE_SHEET_NAME)
birthday_worksheet = connect_to_google_sheet(GOOGLE_BIRTHDAY_SHEET_NAME)

def restrict_chat_access(func):
    """
    Allows access only for users from group with MY_CHAT_ID
    """
    @wraps(func)
    def wrapper(message):
        chat_id = message.chat.id
        if chat_id == MY_CHAT_ID:
            return func(message)
    return wrapper

def update_spreadsheet(new_event, worksheet):
    """
    Writing new event details to the Google spreadsheet
    """
    rows = worksheet.get_all_records()
    next_row = len(rows) + 1
    worksheet.append_row(new_event, value_input_option='USER_ENTERED', table_range=f'A{next_row}:C{next_row}')

# Handler for the /start command
@bot.message_handler(commands=['start'])
@restrict_chat_access
def start(message):
    user = message.from_user
    logger.info(f"Received /start command from user: {user.username}")
    bot.reply_to(message, f"Hi {user.first_name}!")

@bot.message_handler(func=lambda message: message.new_chat_members is not None)
@restrict_chat_access
def handle_new_chat_members(message):
    new_members = message.new_chat_members
    chat_id = message.chat.id

    for member in new_members:
        #user_id = member.id
        username = member.username

        # Send welcome message
        welcome_message = f"Welcome, {username}! Feel free to explore and use the available commands."
        bot.send_message(chat.id, welcome_message)
        bot.send_message(chat.id, help_message)

def send_notification_to_group(group_chat_id, event_name, remaining_time):
    notification=f"Reminder: less than {remaining_time} until {event_name}"
    bot.send_message(chat_id=group_chat_id, text=notification)

def get_future_events():
    current_datetime = datetime.datetime.now()

    events = event_worksheet.get_all_records()
    future_events = []

    for event in events:
        event_datetime = convert_to_datetime(event['Date'], event['Time'])
        if event_datetime > current_datetime:
            future_events.append(event)

    return future_events

@bot.message_handler(commands=['list'])
@restrict_chat_access
def handle_list_command(message):
    user = message.from_user
    logger.info(f"Received /list command from user: {user.username}")

    future_events = get_future_events()

    if future_events:
        response = "Future Events:\n\n"
        for event in future_events:
            response += f"Event Name: {event['Name']}\nDate: {event['Date']}\nTime: {event['Time']}\n\n"
    else:
        response = "No future events found."

    bot.reply_to(message, response)

# Handler for the /help command
@bot.message_handler(commands=['help'])
@restrict_chat_access
def help_command(message):
    user = message.from_user
    logger.info(f"Received /help command from user: {user.username}")
    response = help_message
    bot.reply_to(message, response)

# Handler for the /event command
@bot.message_handler(commands=['event'])
@restrict_chat_access
def handle_event_command(message):
    """
    Takes event from users message and writes it to the Google Spreadsheet with update_spreadsheet method
    """
    user = message.from_user
    logger.info(f"Received /event command from user: {user.username}")

    command_text = message.text.split("/event", 1)[-1].strip()
    event_details = command_text.split()
    #converting date and time before writing in to event worksheet
    if len(event_details) == 3:
        event_details[1] = convert_date(event_details[1])
        event_details[2] = convert_time(event_details[2])
        event_name, date, time = event_details
        try:
            update_spreadsheet(event_details, event_worksheet)
            logger.info(f"New event {event_name} has been added to spreadsheet.")
            response = f"Event has been added: Event Name - {event_name}, Date - {date}, Time - {time}"
        except Exception as e:
            logger.error(f"An error occurred while updating the spreadsheet: {str(e)}")
            response = f"FAILED to write new event. Error: {str(e)}"
    else:
        response = "Please provide event details in the format: event_name date time"
    bot.reply_to(message, response)

# Handler for the /w (weather) command to check weather
@bot.message_handler(commands=['w'])
@restrict_chat_access
def weather_check_command(message):
    user = message.from_user
    logger.info(f"Received /w command from user: {user.username}")
    response = weather_one_time_forecast()
    bot.reply_to(message, response)

# Handler for the /b (birthdays) command to check weather
@bot.message_handler(commands=['b'])
@restrict_chat_access
def birthday_check_command(message):
    user = message.from_user
    logger.info(f"Received /b command from user: {user.username}")
    response = check_birthdays()
    if response:
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "No birthdays for today")

def check_events_and_notify():    
    """
    Description of check_events

    Function checks current events in the spreadsheet and set Notification_status flag in Google Spreadsheet column D:
    Notified_24hours - notification for 24h till the event has been sent 
    Notified_4hours - notification for 4h  has been sent
    Notified_1hour - notification for 1h has been sent

    Returns:
       notification_is_required (boolean): If True that means that notification needs to be sent
    """
    connection_failures = 0
    
    while True:
        try:
            # Check if the header row is present, if not, add it
            header_row_values = ["Name", "Date", "Time", "Notification_status"]
            header_row = event_worksheet.row_values(1)
            if header_row != header_row_values:
                event_worksheet.insert_row(header_row_values, 1)
                logger.info("Added header row to the Google Sheet.")
            notification_is_required = False
            rows = event_worksheet.get_all_records()

            # Get the values of date and time and notification
            row_number = 2
            for row in rows:
                date_value = row['Date']
                time_value = row['Time']
                event_name = row['Name']
                notification_status = row['Notification_status']     
                datetime_value = convert_to_datetime(date_value, time_value) # Generate date and time value from the Google sheet
                remaining_time = get_remaining_time(datetime_value) # Get remaining time until the event
                if remaining_time != None:
                    if 4 < remaining_time <= 24 and notification_status != "Notified_24hours":
                        send_notification_to_group(MY_CHAT_ID, event_name, "24 hours")
                        event_worksheet.update(f'D{row_number}', 'Notified_24hours')
                    elif 1 < remaining_time <=4 and notification_status != "Notified_4hours":
                        send_notification_to_group(MY_CHAT_ID, event_name, "4 hours")
                        event_worksheet.update(f'D{row_number}', 'Notified_4hours')
                    elif remaining_time <= 1 and notification_status != "Notified_1hour":
                        send_notification_to_group(MY_CHAT_ID, event_name, "1 hour")
                        event_worksheet.update(f'D{row_number}', 'Notified_1hour')
                row_number += 1
            time.sleep(10)
        except Exception as e:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"An error occurred in the check_events_and_notify function at {current_time}: {str(e)}")
            connection_failures += 1
            time.sleep(20)
        if connection_failures == 3:
            bot.send_message(chat_id=MY_CHAT_ID, text="Failed to connect to Google Sheet 3 times.")
            connection_failures += 1
        if connection_failures == 15:
            bot.send_message(chat_id=MY_CHAT_ID, text="Failed to connect to Google Sheet 15 times. Bot stopped checking the schedule!")
            break

def check_birthdays():
    '''
    Method returns list of birthdays in "Birthdays" worksheet for today
    '''
    try:
        # Check if the header row is present, if not, add it
        header_row_values = ["Person", "Date"]
        header_row = birthday_worksheet.row_values(1)
        if header_row != header_row_values:
            birthday_worksheet.insert_row(header_row_values, 1)
            logger.info("Added header row to the Birthdays Google Sheet.")

        now = datetime.datetime.now()
        today_birthdays = []
        rows = birthday_worksheet.get_all_records()
        for row in rows:
            date = datetime.datetime.strptime(row['Date'], '%d.%m.%Y')
            if date.day == now.day and date.month == now.month:
                today_birthdays.append(row)

        if len(today_birthdays) > 0:
            response = "Here is the list of birthdays for today:\n"
            for person in today_birthdays:
                birth_date = datetime.datetime.strptime(person['Date'], '%d.%m.%Y').date()
                age = int(now.year) - int(birth_date.year)
                response += f"{person['Person']} - {birth_date.strftime('%d %B, %Y')} (Age: {age})\n"
            return response

    except Exception as e:
        logger.error(f"An error occurred in the check_birthdays function: {str(e)}")

def daily_checks():
    '''
    Schedule 2 sub methods that check and send notifications about weather and birthdays for today
    '''
    def send_weather_forecast():
        bot.send_message(chat_id=MY_CHAT_ID, text=weather_one_time_forecast())
        logger.info("Weather forecast has been sent.")
    schedule.every().day.at("07:00").do(send_weather_forecast)

    def send_birthday_notification():
        today_birthdays = check_birthdays()
        if len(today_birthdays) > 0:
            bot.send_message(chat_id=MY_CHAT_ID, text=today_birthdays)
            logger.info("Birthday notifications with ages have been sent.")
    schedule.every().day.at("07:01").do(send_birthday_notification)
    while True:
        schedule.run_pending()
        time.sleep(50)

def check_thread_liveness(threads):
    """Check the liveness of a list of threads.

    This function checks the liveness of a list of threads and returns a status
    based on their liveness. The liveness of a thread is determined by whether it
    is currently running (alive) or not.

    Parameters:
        threads (list): A list of threading.Thread objects to be checked.
    Returns:
        tuple: A tuple containing the JSON response data and HTTP status code.
    """
    dead_threads = []
    for thread in threads:
        if not thread.is_alive():
            dead_threads.append(thread.name)

    if len(dead_threads) == 0:
        return jsonify(status='OK', message='All threads are alive'), 200
    elif len(dead_threads) == len(threads):
        return jsonify(status='ERROR', message='All threads are not alive'), 500
    else:
        return jsonify(status='ERROR', message=f'Threads not alive: {", ".join(dead_threads)}'), 500

@app.route('/health')
def health_check():
    threads = [check_events_thread, check_birthdays_thread, bot_thread, weather_check_daily_thread]
    return check_thread_liveness(threads)

if __name__ == "__main__":
    check_events_thread = threading.Thread(target=check_events_and_notify, name="Check events thread")
    check_events_thread.start()

    bot_thread = threading.Thread(target=bot.infinity_polling, name="Telegram Bot thread")
    bot_thread.start()

    daily_checks_thread = threading.Thread(target=daily_checks, name="Weather and birthdays check thread")
    daily_checks_thread.start()

    # Run the Flask application
    app.run()

    check_events_thread.join()
    bot_thread.join()
    daily_checks_thread.join()