import logging
import os
import time
import datetime
from functools import wraps
import telebot
import threading
import gspread

import date_time


TOKEN = os.environ.get('TOKEN')
MY_CHAT_ID = int(os.environ.get('CHAT_ID'))

# Google Sheets credentials
GOOGLE_SHEETS_CREDS = os.environ.get('GOOGLE_SHEETS_CREDS')
GOOGLE_SPREADSHEET_ID = os.environ.get('GOOGLE_SPREADSHEET_ID')
GOOGLE_SHEET_NAME = os.environ.get('GOOGLE_SHEET_NAME')

scope = ['https://www.googleapis.com/auth/spreadsheets']

help_message = '''You can run the following commands:
    /help - get help and support
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

gc = gspread.service_account(GOOGLE_SHEETS_CREDS)
spreadsheet = gc.open_by_key(GOOGLE_SPREADSHEET_ID)
worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)


# Connect to Google Sheets
def connect_to_google_sheet():
    try:
        gc = gspread.service_account(GOOGLE_SHEETS_CREDS)
        spreadsheet = gc.open_by_key(GOOGLE_SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)
        return worksheet
    except Exception as e:
        logger.error(f"An error occurred while connecting : {str(e)}")

def restrict_chat_access(func):
    '''
    Allows access only for users from group with MY_CHAT_ID
    '''
    @wraps(func)
    def wrapper(message):
        chat_id = message.chat.id
        if chat_id == MY_CHAT_ID:
            return func(message)
    return wrapper

def update_spreadsheet(new_event):
    '''
    Writing new event details to the Google spreadsheet
    '''
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

    events = worksheet.get_all_records()
    future_events = []

    for event in events:
        event_datetime = date_time.convert_to_datetime(event['Date'], event['Time'])
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
        response = "Future Events:\n"
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
    user = message.from_user
    logger.info(f"Received /event command from user: {user.username}")

    command_text = message.text.split("/event", 1)[-1].strip()
    event_details = command_text.split()
    if len(event_details) == 3:
        event_name, date, time = event_details
        try:
            update_spreadsheet(event_details)
            logger.info(f"New event {event_name} has been added to spreadsheet.")
            response = f"Event has been added: Event Name - {event_name}, Date - {date}, Time - {time}"
        except Exception as e:
            logger.error(f"An error occurred while updating the spreadsheet: {str(e)}")
            response = f"FAILED to write new event. Error: {str(e)}"
    else:
        response = "Please provide event details in the format: event_name date time"
    bot.reply_to(message, response)

def check_events_and_notify():    
    '''
    Description of check_events

    Function checks current events in the spreadsheet and set Notification_status flag:
    Notified_24hours - notification for 24h till the event has been sent 
    Notified_4hours - notification for 4h  has been sent
    Notified_1hour - notification for 1h has been sent

    Returns:
       notification_is_required (boolean): If True that means that notification needs to be sent
    '''
    connection_failures = 0
    running = True
    while running:
        try:
            notification_is_required = False
            rows = worksheet.get_all_records()

            # Get the values of date and time and notification
            row_number = 2
            for row in rows:
                date_value = row['Date']
                time_value = row['Time']
                event_name = row['Name']
                notification_status = row['Notification_status']     
                datetime_value = date_time.convert_to_datetime(date_value, time_value) # Generate date and time value from the Google sheet
                remaining_time = date_time.get_remaining_time(datetime_value) # Get remaining time until the event
                if remaining_time != None:
                    if 4 < remaining_time <= 24 and notification_status != "Notified_24hours":
                        send_notification_to_group(MY_CHAT_ID, event_name, "24 hours")
                        worksheet.update(f'D{row_number}', 'Notified_24hours')
                    elif 1 < remaining_time <=4 and notification_status != "Notified_4hours":
                        send_notification_to_group(MY_CHAT_ID, event_name, "4 hours")
                        worksheet.update(f'D{row_number}', 'Notified_4hours')
                    elif remaining_time <= 1 and notification_status != "Notified_1hour":
                        send_notification_to_group(MY_CHAT_ID, event_name, "1 hour")
                        worksheet.update(f'D{row_number}', 'Notified_1hour')
                row_number += 1
            time.sleep(5)
        except Exception as e:
            logger.error(f"An error occurred in the check_events_and_notify function: {str(e)}")
            connection_failures += 1
            time.sleep(5)
        if connection_failures > 5:
            bot.send_message(chat_id=MY_CHAT_ID, text="Failed to connect to Google Sheet 5 times. Bot stopped checking the schedule!")
            running = False

def main():
    check_events_thread = threading.Thread(target=check_events_and_notify)
    check_events_thread.start()

    bot_thread = threading.Thread(target=bot.infinity_polling)
    bot_thread.start()

    check_events_thread.join()
    bot_thread.join()

if __name__ == "__main__":
    main()
