import os
import textwrap
import threading
import time

import telebot
from dotenv import load_dotenv
from telebot.types import KeyboardButton, Message, ReplyKeyboardMarkup

from history import History
from hunters.hunter import Hunter, Prey
from hunters.gruno import Gruno
from hunters.kamernet import Kamernet
from hunters.pararius import Pararius
from hunters.wonen123 import Wonen123

# --- Constants and Globals ---
ENV_FILE_PATH = 'src/.env'
selected_cities: set[str] = set()
runHunters = True
ALL_HUNTERS: list[Hunter] = [Wonen123(), Gruno(), Kamernet(), Pararius()]

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
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    help_button = KeyboardButton('/help')
    markup.add(help_button)
    return markup

def send_message(chat_id: int | str, text: str):
    bot.send_message(chat_id, text, reply_markup=create_custom_keyboard())

def broadcast_message(text: str):
    for chat_id in chat_ids:
        send_message(chat_id, text)

# --- Command Handlers ---
@bot.message_handler(commands=['subscribe'])
def subscribe_message(message: Message):
    global chat_ids, CHAT_ID
    chat_id = str(message.chat.id)
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        CHAT_ID = ','.join(chat_ids)
        update_env_file()
        print(f'New chat ID subscribed: {chat_id}. Current chat_ids "{CHAT_ID}"')
        send_message(chat_id, 'You have been subscribed to receive the Netherlands housing notifications!')
    else:
        send_message(chat_id, 'You are already subscribed.')

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_message(message: Message):
    global chat_ids, CHAT_ID
    chat_id = str(message.chat.id)
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        CHAT_ID = ','.join(chat_ids)
        update_env_file()
        print(f'Chat ID unsubscribed: {chat_id}. Current chat_ids "{CHAT_ID}"')
        send_message(chat_id, 'You have been unsubscribed from receiving Netherlands housing notifications.')
    else:
        send_message(chat_id, 'You are not subscribed.')

@bot.message_handler(commands=['status'])
def status_message(message: Message):
    if len(selected_cities) > 0:
        pluralized = 'city is' if len(selected_cities) == 1 else 'cities are'
        bot.send_message(message.chat.id, f"The currently selected {pluralized}: {', '.join(selected_cities)}.")
        if MAXIMUM_PRICE is not None:
            bot.send_message(message.chat.id, f"Current maximum price filter is: {MAXIMUM_PRICE}.")
        if MINIMUM_PRICE is not None:
            bot.send_message(message.chat.id, f"Current minimum price filter is: {MINIMUM_PRICE}.")
    else:
        bot.send_message(message.chat.id, "No city has been selected yet. Please use the /start command to select a city.")

@bot.message_handler(commands=['help'])
def help_message(message: Message):
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
def set_min_price(message: Message):
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
    global selected_cities

    # Dynamically fetch supported cities from all hunters
    city_set = set()
    for hunter in ALL_HUNTERS:
        try:
            city_set.update(hunter.supported_cities())
        except NotImplementedError:
            continue

    # Create a numbered list of cities
    city_list = sorted(city_set)
    city_map = {str(i + 1): city for i, city in enumerate(city_list)}

    # Save the city map globally for selection
    global city_map_global
    city_map_global = city_map

    city_options = "\n".join([f"{i}) {city}" for i, city in city_map.items()])
    bot.send_message(
        message.chat.id,
        f"Please select a city by typing the corresponding number:\n{city_options}",
        parse_mode='Markdown'
    )

def parse_city_indices(message: Message):
    # extract comma separated values and convert to set
    return set([part.strip() for part in message.text.split(',')])

@bot.message_handler(func=lambda message: parse_city_indices(message).issubset(city_map_global))
def city_selection_message(message: Message):
    global selected_cities
    selected_cities = set([city_map_global[index] for index in parse_city_indices(message)])
    pluralized = 'city' if len(selected_cities) == 1 else 'cities'
    bot.send_message(message.chat.id, f"Hunters will now target the following {pluralized}: {', '.join(selected_cities)}")

@bot.message_handler(commands=['list'])
def list_message(message: Message):
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
def unrecognized_message(message: Message):
    bot.send_message(message.chat.id, "Unrecognized command. Use /help to see available commands.")

# --- Core Logic: Hunters ---
def run_hunters():
    global selected_cities

    while len(selected_cities) == 0:
        print('Waiting for city selection...')
        time.sleep(5)

    active_hunters: list[Hunter] = []
    for hunter in ALL_HUNTERS:
        unsupported = hunter.set_cities(selected_cities)
        if len(unsupported) < len(selected_cities):
            # There was at least one supported city
            active_hunters.append(hunter)
        else:
            pluralized = 'city' if len(unsupported) == 1 else 'cities'
            print(f"Skipping {hunter.name} as it does not support the selected {pluralized}.")

    print('Starting hunters')
    for hunter in active_hunters:
        hunter.start()

    history = History('history.txt')
    while runHunters:
        preys: set[Prey] = set()
        for hunter in active_hunters:
            try:
                hunter_preys = hunter.hunt()
                print(f'Hunter {hunter.name} found {len(hunter_preys)} preys')
                preys.update(hunter_preys)
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
            message_text = textwrap.dedent(f'''
                📢 *Listing Found:*

                Name: {prey.name}
                {'Agency: ' + prey.agency if prey.agency is not None else ''}
                Price: €{prey.price}
                Link: {prey.link}
            ''')
            broadcast_message(message_text)
        
        time.sleep(4 * 60)

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
