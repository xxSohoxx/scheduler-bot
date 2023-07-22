# scheduler-bot
Telegram bot for scheduling events/meetings/etc.

Prerequisites
==============

Enable API Access for a Google Project
-------------------------------

1. Head to [Google Developers Console](https://console.developers.google.com/) and create a new project (or select the one you already have).

2. In the box labeled "Search for APIs and Services", search for "Google Drive API" and enable it.

3. In the box labeled "Search for APIs and Services", search for "Google Sheets API" and enable it.


Configuring Google Service Account
-------------------------------

A service account is a special type of Google account intended to represent a non-human user that needs to authenticate and be authorized to access data in Google APIs.

Since it's a separate account, by default it does not have access to any spreadsheet until you share it with this account. Just like any other Google account.

Here's how to get one:

1. Open [Google Cloud console](https://console.cloud.google.com/apis/) and go to "APIs & Services > Credentials" and choose "Create credentials > Service account key".

2. Fill out the form

3. Click "Create" and "Done".

4. Press "Manage service accounts" above Service Accounts.

5. Press on **⋮** near recently created service account and select "Manage keys" and then click on "ADD KEY > Create new key".

6. Select JSON key type and press "Create".

You will automatically download a JSON file with credentials. It may look like this:

    {
        "type": "service_account",
        "project_id": "api-project-XXX",
        "private_key_id": "2cd … ba4",
        "private_key": "-----BEGIN PRIVATE KEY-----\nNrDyLw … jINQh/9\n-----END PRIVATE KEY-----\n",
        "client_email": "473000000000-yoursisdifferent@developer.gserviceaccount.com",
        "client_id": "473 … hd.apps.googleusercontent.com",
        ...
    }

Remember the path to the downloaded credentials file. Also, in the next step you'll need the value of *client_email* from this file.

6. Very important! Go to your spreadsheet and share it with a *client_email* from the step above. Just like you do with any other Google account. If you don't do this, you'll get a ``gspread.exceptions.SpreadsheetNotFound`` exception when trying to access this spreadsheet from your application or a script.

Telegram Bot
------------

Creating a bot is streamlined by Telegram’s Bot API, which gives the tools and framework required to integrate your code. To get started, message [@BotFather](https://t.me/botfather) on Telegram to register your bot and receive its authentication token.  
[Here](https://core.telegram.org/bots/#3-how-do-i-create-a-bot) you can find more details 

Other requirements
------------------
You need to install libraries from requirements.txt:  
`pip install -r requirements.txt`

Also you need to set env viriables below:

GOOGLE_SHEETS_CREDS - path to your credentials.json file from the Configuring Google Service Account step  
GOOGLE_SPREADSHEET_ID - spreadsheet ID can be taken from the URL of the document - https://docs.google.com/spreadsheets/d/%GOOGLE_SPREADSHEET_ID%  
GOOGLE_SHEET_NAME - title of the sheet with your schedule  
TOKEN - Telegram bot access token  
CHAT_ID - ID of Telegram group where you are going to work with the bot  

How does it work
================
Here is the list of available commands:

/help - get help and support  
/list - get all future events  
/event EVENT_NAME DATE TIME - add a new event (example: "/event Doctor_appointment 01-11-2023 12:20")  

Bot processes commands only from the group with CHAT_ID. It takes events and writes them to your Google Spreadsheet.
Additionally, it checks the event list every 5 seconds and sends reminders 24 hours, 4 hours, and 1 hour prior to each event.

