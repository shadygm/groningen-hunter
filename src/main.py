import os
import telebot
from telebot import types
import threading
import time
import textwrap
from hunters.pararius import Pararius
from hunters.kamernet import Kamernet
from hunters.gruno import Gruno
from hunters.wonen123 import Wonen123
from history import History
from dotenv import load_dotenv

load_dotenv()
ENV_FILE_PATH = 'src/.env'  # Path to the .env file
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
MAXIMUM_PRICE = os.environ.get('MAXIMUM_PRICE')
MINIMUM_PRICE = os.environ.get('MINIMUM_PRICE')

if BOT_TOKEN is None:
    print('BOT_TOKEN was not set! Make sure your .bashrc is well configured')

if CHAT_ID and CHAT_ID.strip():
    chat_ids = [chat_id.strip() for chat_id in CHAT_ID.split(',') if chat_id.strip()]
else:
    chat_ids = []
print(f'Messages will be sent to: {chat_ids}')

if MAXIMUM_PRICE is None:
    print('MAXIMUM_PRICE was not set! No filter will be applied')
else:
    print(f'MAXIMUM_PRICE is set to {MAXIMUM_PRICE}')

if MINIMUM_PRICE is None:
    print('MINIMUM_PRICE was not set! No filter will be applied')
else:
    print(f'MINIMUM_PRICE is set to {MINIMUM_PRICE}')

# Update the .env file
def update_env_file():
    with open(ENV_FILE_PATH, 'w') as f:
        if BOT_TOKEN is not None:
            f.write(f'BOT_TOKEN="{BOT_TOKEN}"\n')
        if CHAT_ID is not None:
            f.write(f'CHAT_ID="{CHAT_ID}"\n')
        if MAXIMUM_PRICE is not None:
            f.write(f'MAXIMUM_PRICE={MAXIMUM_PRICE}\n')
        if MINIMUM_PRICE is not None:
            f.write(f'MINIMUM_PRICE={MINIMUM_PRICE}\n')

bot = telebot.TeleBot(BOT_TOKEN)

# Create a custom keyboard
def create_custom_keyboard():
    # Create the markup object
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

    # Create buttons that show one text but trigger another action
    subscribe_button = types.KeyboardButton('/subscribe')
    unsubscribe_button = types.KeyboardButton('/unsubscribe')
    status_button = types.KeyboardButton('/status')

    # Add buttons to the markup
    markup.add(subscribe_button, unsubscribe_button, status_button)

    return markup

def send_message(chat_id, message):
    bot.send_message(chat_id, message, reply_markup=create_custom_keyboard())

def broadcast_message(message):
    for chat_id in chat_ids:
        send_message(chat_id, message)

@bot.message_handler(commands=['subscribe'])
def subscribe_message(message):
    global chat_ids
    global CHAT_ID
    chat_id = str(message.chat.id)
    if chat_id not in chat_ids:
        chat_ids.append(chat_id) # Add chat ID to the list
        CHAT_ID = ','.join(chat_ids) # Update CHAT_ID to be comma-separated

        # Update the .env file with the new chat IDs
        update_env_file()

        print(f'New chat ID subscribed: {chat_id}. Current chat_ids "{CHAT_ID}"')
        send_message(chat_id, f'You have been subscribed to receive the groningen apartment notifications!')
    else:
        send_message(chat_id, f'You are already subscribed.')

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_message(message):
    global chat_ids
    global CHAT_ID
    chat_id = str(message.chat.id)
    if chat_id in chat_ids:
        chat_ids.remove(chat_id) # Remove chat ID from the list
        CHAT_ID = ','.join(chat_ids) # Update CHAT_ID to be comma-separated

        # Update the .env file with the new chat IDs
        update_env_file()

        print(f'Chat ID unsubscribed: {chat_id}. Current chat_ids "{CHAT_ID}"')
        send_message(chat_id, f'You have been unsubscribed from receiving groningen apartment notifications.')
    else:
        send_message(chat_id, f'You are not subscribed.')

# This handler captures any messages that are not handled by other commands
@bot.message_handler(func=lambda message: True)
def status_message(message):
    chat_id = str(message.chat.id)
    if chat_id in chat_ids:
        send_message(chat_id, 'I\'m hunting some apartments right now!')
    else:
        send_message(chat_id, 'You are not subscribed to notifications, send the message /subscribe if you want them :)')

runHunters = True
def run_hunters():
    hunters = [Wonen123(), Gruno(), Kamernet(), Pararius()]

    print('Start hunters')
    for hunter in hunters:
        hunter.start()
    history = History('history.txt')
    while runHunters:
        preys = []
        # Get preys
        for hunter in hunters:
            try:
                hunter_preys = hunter.hunt()
                print(f'Hunter {hunter.name} found {len(hunter_preys)} preys')
                preys += hunter_preys
            except Exception as e:
                message = f'Found error when running hunter "{hunter.name}": {str(e)}'
                print(message)
                # Optional: Send message on error
                # broadcast_message(message)

        # Filter already seen preys
        filtered_preys = history.filter(preys)
        if len(filtered_preys) > 0:
            print(f'Found {len(filtered_preys)} new preys')

        # Filter maximum price
        if MAXIMUM_PRICE is not None:
            filtered_preys = [prey for prey in filtered_preys if int(prey.price) <= int(MAXIMUM_PRICE)]

        # Filter minimum price
        if MINIMUM_PRICE is not None:
            filtered_preys = [prey for prey in filtered_preys if int(prey.price) >= int(MINIMUM_PRICE)]

        # Send telegram message
        for prey in filtered_preys:
            message = textwrap.dedent(f'''
                Name: {prey.name}
                {'Agency: ' + prey.agency if prey.agency is not None else ''}
                Price: {prey.price}
                Link: {prey.link}
            ''')
            broadcast_message(message)
        time.sleep(5*60)
    print('Stop hunters')
    for hunter in hunters:
        hunter.stop()

t = threading.Thread(target=run_hunters)
t.start()
bot.infinity_polling()
runHunters = False
t.join()
