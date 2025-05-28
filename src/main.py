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

# --- Constants and Globals ---
ENV_FILE_PATH = 'src/.env'
selected_city = None
runHunters = True

# --- Load environment variables ---
load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
MAXIMUM_PRICE = os.environ.get('MAXIMUM_PRICE')
MINIMUM_PRICE = os.environ.get('MINIMUM_PRICE')

# --- Validate environment variables ---
if BOT_TOKEN is None:
    print('BOT_TOKEN was not set! Make sure your .bashrc is well configured')

chat_ids = [chat_id.strip() for chat_id in CHAT_ID.split(',') if chat_id.strip()] if CHAT_ID and CHAT_ID.strip() else []
print(f'Messages will be sent to: {chat_ids}')

if MAXIMUM_PRICE is None:
    print('MAXIMUM_PRICE was not set! No filter will be applied')
else:
    print(f'MAXIMUM_PRICE is set to {MAXIMUM_PRICE}')

if MINIMUM_PRICE is None:
    print('MINIMUM_PRICE was not set! No filter will be applied')
else:
    print(f'MINIMUM_PRICE is set to {MINIMUM_PRICE}')

# --- Utility functions ---
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

# --- Telegram bot setup ---
bot = telebot.TeleBot(BOT_TOKEN)

def create_custom_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    help_button = types.KeyboardButton('/help')
    markup.add(help_button)
    return markup

def send_message(chat_id, message):
    bot.send_message(chat_id, message, reply_markup=create_custom_keyboard())

def broadcast_message(message):
    for chat_id in chat_ids:
        send_message(chat_id, message)

# --- Command Handlers ---
@bot.message_handler(commands=['subscribe'])
def subscribe_message(message):
    global chat_ids, CHAT_ID
    chat_id = str(message.chat.id)
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        CHAT_ID = ','.join(chat_ids)
        update_env_file()
        print(f'New chat ID subscribed: {chat_id}. Current chat_ids "{CHAT_ID}"')
        send_message(chat_id, 'You have been subscribed to receive the Groningen apartment notifications!')
    else:
        send_message(chat_id, 'You are already subscribed.')

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_message(message):
    global chat_ids, CHAT_ID
    chat_id = str(message.chat.id)
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        CHAT_ID = ','.join(chat_ids)
        update_env_file()
        print(f'Chat ID unsubscribed: {chat_id}. Current chat_ids "{CHAT_ID}"')
        send_message(chat_id, 'You have been unsubscribed from receiving Groningen apartment notifications.')
    else:
        send_message(chat_id, 'You are not subscribed.')

@bot.message_handler(commands=['status'])
def status_message(message):
    if selected_city:
        bot.send_message(message.chat.id, f"The currently selected city is: {selected_city}.")
        if MAXIMUM_PRICE is not None:
            bot.send_message(message.chat.id, f"Current maximum price filter is: {MAXIMUM_PRICE}.")
        if MINIMUM_PRICE is not None:
            bot.send_message(message.chat.id, f"Current minimum price filter is: {MINIMUM_PRICE}.")
    else:
        bot.send_message(message.chat.id, "No city has been selected yet. Please use the /start command to select a city.")

@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = textwrap.dedent('''
        🌟 *Available Commands* 🌟

        📩 *Subscription:*
        /subscribe - Subscribe to apartment notifications.
        /unsubscribe - Unsubscribe from apartment notifications.

        🔍 *Status:*
        /status - Check the currently selected city and price filters.
        /list - Display all apartment listings found so far.

        💰 *Price Filters:*
        /set\_min\_price <amount> - Set the minimum price filter.
        /set\_max\_price <amount> - Set the maximum price filter.

        ❓ *Help:*
        /help - Display this help message.

        ⚠️ *Note:*
        Once a city is selected, you must restart the bot to change the city.
    ''')
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['set_min_price'])
def set_min_price(message):
    global MINIMUM_PRICE
    try:
        price = int(message.text.split()[1])
        MINIMUM_PRICE = price
        update_env_file()
        bot.send_message(message.chat.id, f"Minimum price filter set to {MINIMUM_PRICE}.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Invalid input. Use /set_min_price <amount>.")
        if MINIMUM_PRICE is not None:
            bot.send_message(message.chat.id, f"Current minimum price filter is {MINIMUM_PRICE}.")


@bot.message_handler(commands=['set_max_price'])
def set_max_price(message):
    global MAXIMUM_PRICE
    try:
        price = int(message.text.split()[1])
        MAXIMUM_PRICE = price
        update_env_file()
        bot.send_message(message.chat.id, f"Maximum price filter set to {MAXIMUM_PRICE}.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Invalid input. Use /set_max_price <amount>.")
        if not MAXIMUM_PRICE is None:
            bot.send_message(message.chat.id, f"Current maximum price filter is {MAXIMUM_PRICE}.")

@bot.message_handler(commands=['start'])
def start_message(message):
    global selected_city
    bot.send_message(
        message.chat.id,
        "Please select a city by typing the corresponding number:\n1) Groningen\n2) The Hague",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text in ['1', '2'])
def city_selection_message(message):
    global selected_city
    city_map = {'1': 'Groningen', '2': 'The Hague'}
    selected_city = city_map[message.text]
    bot.send_message(message.chat.id, f"You have selected {selected_city}. Hunters will now target this city.")

    # Update hunters with the selected city
    for hunter in [Wonen123(), Gruno(), Kamernet(), Pararius()]:
        try:
            hunter.set_city(selected_city)
        except ValueError as e:
            bot.send_message(message.chat.id, str(e))

@bot.message_handler(commands=['list'])
def list_message(message):
    history = History('history.txt')
    all_preys = history.get_all()

    if not all_preys:
        bot.send_message(message.chat.id, "No listings have been found yet.")
        return

    for prey in all_preys:
        response = textwrap.dedent(f'''
            \U0001F4E2 *Listing Found:*

            Name: {prey['name']}
            Agency: {prey['agency']}
            Price: €{prey['price']}
            Link: {prey['link']}
        ''')
        bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def unrecognized_message(message):
    bot.send_message(message.chat.id, "Unrecognized command. Use /help to see available commands.")

# --- Core Logic: Hunters ---
def run_hunters():
    global selected_city
    all_hunters = [Wonen123(), Gruno(), Kamernet(), Pararius()]

    while selected_city is None:
        print('Waiting for city selection...')
        time.sleep(5)

    active_hunters = []
    for hunter in all_hunters:
        try:
            hunter.set_city(selected_city)
            active_hunters.append(hunter)
        except ValueError:
            print(f"Skipping {hunter.name} as it does not support the selected city.")

    print('Start hunters')
    for hunter in active_hunters:
        hunter.start()

    history = History('history.txt')
    while runHunters:
        preys = []
        for hunter in active_hunters:
            try:
                hunter_preys = hunter.hunt()
                print(f'Hunter {hunter.name} found {len(hunter_preys)} preys')
                preys += hunter_preys
            except Exception as e:
                print(f'Error with hunter {hunter.name}: {e}')

        filtered_preys = history.filter(preys)
        if len(filtered_preys) > 0:
            print(f'Found {len(filtered_preys)} new preys')

        if MAXIMUM_PRICE is not None:
            filtered_preys = [prey for prey in filtered_preys if int(prey.price) <= int(MAXIMUM_PRICE)]

        if MINIMUM_PRICE is not None:
            filtered_preys = [prey for prey in filtered_preys if int(prey.price) >= int(MINIMUM_PRICE)]

        for prey in filtered_preys:
            message = textwrap.dedent(f'''
                \U0001F4E2 *Listing Found:*

                Name: {prey.name}
                {'Agency: ' + prey.agency if prey.agency is not None else ''}
                Price: €{prey.price}
                Link: {prey.link}
            ''')
            broadcast_message(message)
        time.sleep(10 * 60)

    print('Stop hunters')
    for hunter in active_hunters:
        hunter.stop()

# --- Main Entrypoint ---
if __name__ == "__main__":
    t = threading.Thread(target=run_hunters)
    t.start()
    bot.infinity_polling(timeout=1200)  # Timeout after 20 minutes (1200 seconds)
    runHunters = False
    t.join()
