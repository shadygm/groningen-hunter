import os
import textwrap
import threading
import time

import telebot
from dotenv import load_dotenv
from telebot.types import KeyboardButton, Message, ReplyKeyboardMarkup

from history import History, read_listings
from hunters.hunter import Hunter, Prey, SharedBrowser
from hunters.gruno import Gruno
from hunters.kamernet import Kamernet
from hunters.pararius import Pararius
from hunters.wonen123 import Wonen123
from users import UserStore

# --- Constants and Globals ---
runHunters = True
ALL_HUNTERS: list[Hunter] = [Wonen123(), Gruno(), Kamernet(), Pararius()]

# --- Load environment variables ---
load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# --- Validate environment variables ---
if BOT_TOKEN is None:
    print('BOT_TOKEN was not set! Make sure your .env is well configured')

# --- Per-user settings ---
users = UserStore('users.json')
# One-time import of subscribers from the old global .env configuration
users.migrate_legacy(
    os.environ.get('CHAT_ID'),
    os.environ.get('MINIMUM_PRICE'),
    os.environ.get('MAXIMUM_PRICE'),
)

# --- City selection map (static: built once from all hunters) ---
def build_city_map() -> dict[str, str]:
    city_set = set()
    for hunter in ALL_HUNTERS:
        try:
            city_set.update(hunter.supported_cities())
        except NotImplementedError:
            continue
    return {str(i + 1): city for i, city in enumerate(sorted(city_set))}

CITY_MAP = build_city_map()

def parse_price(price: str) -> int | None:
    try:
        return int(price)
    except (TypeError, ValueError):
        return None

# --- Telegram bot setup ---
bot = telebot.TeleBot(BOT_TOKEN)

def create_custom_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    help_button = KeyboardButton('/help')
    markup.add(help_button)
    return markup

def send_message(chat_id: int | str, text: str):
    bot.send_message(chat_id, text, reply_markup=create_custom_keyboard())

# --- Command Handlers ---
@bot.message_handler(commands=['subscribe'])
def subscribe_message(message: Message):
    chat_id = str(message.chat.id)
    if users.subscribe(chat_id):
        print(f'New chat ID subscribed: {chat_id}')
        send_message(chat_id, 'You have been subscribed to receive the Netherlands housing notifications! '
                              'Use /start to select the cities you are interested in.')
    else:
        send_message(chat_id, 'You are already subscribed.')

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_message(message: Message):
    chat_id = str(message.chat.id)
    if users.unsubscribe(chat_id):
        print(f'Chat ID unsubscribed: {chat_id}')
        send_message(chat_id, 'You have been unsubscribed from receiving Netherlands housing notifications.')
    else:
        send_message(chat_id, 'You are not subscribed.')

@bot.message_handler(commands=['status'])
def status_message(message: Message):
    chat_id = str(message.chat.id)
    settings = users.get_settings(chat_id)
    if settings is None:
        bot.send_message(chat_id, 'You are not subscribed. Use /subscribe to receive notifications.')
        return
    if settings['cities']:
        pluralized = 'city is' if len(settings['cities']) == 1 else 'cities are'
        bot.send_message(chat_id, f"Your currently selected {pluralized}: {', '.join(settings['cities'])}.")
    else:
        bot.send_message(chat_id, 'You have not selected a city yet. Use /start to select one.')
    if settings['max_price'] is not None:
        bot.send_message(chat_id, f"Your maximum price filter is: {settings['max_price']}.")
    if settings['min_price'] is not None:
        bot.send_message(chat_id, f"Your minimum price filter is: {settings['min_price']}.")

@bot.message_handler(commands=['help'])
def help_message(message: Message):
    help_text = textwrap.dedent('''
        🌟 *Available Commands* 🌟

        📩 *Subscription:*
        /subscribe - Subscribe to apartment notifications.
        /unsubscribe - Unsubscribe from apartment notifications.

        🏙 *Cities:*
        /start - Select the cities you want to monitor.

        🔍 *Status:*
        /status - Check your selected cities and price filters.
        /list - Display the apartment listings found so far.

        💰 *Price Filters:*
        /set\\_min\\_price <amount> - Set your minimum price filter.
        /set\\_max\\_price <amount> - Set your maximum price filter.

        ❓ *Help:*
        /help - Display this help message.

        ⚠️ *Note:*
        Cities and price filters are personal: they only affect your own notifications.
    ''')
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['set_min_price'])
def set_min_price(message: Message):
    chat_id = str(message.chat.id)
    try:
        price = int(message.text.split()[1])
    except (IndexError, ValueError):
        bot.send_message(chat_id, 'Invalid input. Use /set_min_price <amount>.')
        settings = users.get_settings(chat_id)
        if settings is not None and settings['min_price'] is not None:
            bot.send_message(chat_id, f"Your current minimum price filter is {settings['min_price']}.")
        return
    newly_subscribed = users.set_min_price(chat_id, price)
    bot.send_message(chat_id, f'Your minimum price filter is set to {price}.')
    if newly_subscribed:
        send_message(chat_id, 'You have also been subscribed to notifications. Use /start to select your cities.')

@bot.message_handler(commands=['set_max_price'])
def set_max_price(message: Message):
    chat_id = str(message.chat.id)
    try:
        price = int(message.text.split()[1])
    except (IndexError, ValueError):
        bot.send_message(chat_id, 'Invalid input. Use /set_max_price <amount>.')
        settings = users.get_settings(chat_id)
        if settings is not None and settings['max_price'] is not None:
            bot.send_message(chat_id, f"Your current maximum price filter is {settings['max_price']}.")
        return
    newly_subscribed = users.set_max_price(chat_id, price)
    bot.send_message(chat_id, f'Your maximum price filter is set to {price}.')
    if newly_subscribed:
        send_message(chat_id, 'You have also been subscribed to notifications. Use /start to select your cities.')

@bot.message_handler(commands=['start'])
def start_message(message: Message):
    city_options = '\n'.join([f'{i}) {city}' for i, city in CITY_MAP.items()])
    bot.send_message(
        message.chat.id,
        'Please select the cities you want to monitor by typing the corresponding numbers '
        f'separated by commas (for example: 1,3):\n{city_options}',
        parse_mode='Markdown'
    )

def parse_city_indices(message: Message) -> set[str]:
    # extract comma separated values and convert to set
    return set([part.strip() for part in message.text.split(',')])

def is_city_selection(message: Message) -> bool:
    if message.text is None or message.text.startswith('/'):
        return False
    return parse_city_indices(message).issubset(CITY_MAP.keys())

@bot.message_handler(func=is_city_selection)
def city_selection_message(message: Message):
    chat_id = str(message.chat.id)
    cities = set([CITY_MAP[index] for index in parse_city_indices(message)])
    newly_subscribed = users.set_cities(chat_id, cities)
    pluralized = 'city' if len(cities) == 1 else 'cities'
    bot.send_message(chat_id, f"Hunters will now target the following {pluralized} for you: {', '.join(sorted(cities))}")
    if newly_subscribed:
        send_message(chat_id, 'You have also been subscribed to notifications. Use /unsubscribe to stop.')

@bot.message_handler(commands=['list'])
def list_message(message: Message):
    chat_id = str(message.chat.id)
    settings = users.get_settings(chat_id)
    found_any = False

    # Stream the history file rather than loading it: it holds every listing ever found
    for prey in read_listings('history.txt'):
        # Apply the user's price filters, if any
        if settings is not None:
            price = parse_price(prey['price'])
            if price is not None:
                if settings['min_price'] is not None and price < settings['min_price']:
                    continue
                if settings['max_price'] is not None and price > settings['max_price']:
                    continue
        found_any = True

        response = textwrap.dedent(f'''
            \U0001F4E2 *Listing Found:*

            Name: {prey['name']}
            Agency: {prey['agency']}
            Price: €{prey['price']}
            Link: {prey['link']}
        ''')
        bot.send_message(chat_id, response, parse_mode='Markdown')

    if not found_any:
        bot.send_message(chat_id, 'No listings have been found yet.')

@bot.message_handler(func=lambda message: True)
def unrecognized_message(message: Message):
    bot.send_message(message.chat.id, "Unrecognized command. Use /help to see available commands.")

# --- Core Logic: Hunters ---
def run_hunters():
    history = History('history.txt')
    shared_browser = SharedBrowser()
    started_hunters: set[str] = set()
    waiting_logged = False

    while runHunters:
        # Hunt the union of all users' cities, so selection changes apply without a restart
        cities = users.all_cities()
        if len(cities) == 0:
            if not waiting_logged:
                print('Waiting for at least one user to select a city...')
                waiting_logged = True
            time.sleep(5)
            continue
        waiting_logged = False

        preys: set[Prey] = set()
        for hunter in ALL_HUNTERS:
            unsupported = hunter.set_cities(cities)
            if len(unsupported) == len(cities):
                continue # Hunter does not support any of the selected cities
            if hunter.name not in started_hunters:
                hunter.start()
                started_hunters.add(hunter.name)
            try:
                hunter_preys = hunter.hunt(shared_browser.get())
                print(f'Hunter {hunter.name} found {len(hunter_preys)} preys')
                preys.update(hunter_preys)
            except Exception as e:
                print(f'Error with hunter {hunter.name}: {type(e).__name__}: {e}')
        shared_browser.park()

        new_preys = history.filter(preys)
        if len(new_preys) > 0:
            print(f'Found {len(new_preys)} new preys')

        # Notify each user according to their own city and price filters
        for prey in new_preys:
            message_text = textwrap.dedent(f'''
                📢 *Listing Found:*

                Name: {prey.name}
                {'Agency: ' + prey.agency if prey.agency is not None else ''}
                Price: €{prey.price}
                Link: {prey.link}
            ''')
            for chat_id in users.recipients_for(prey.city, parse_price(prey.price)):
                send_message(chat_id, message_text)

        # Sleep in small steps so shutdown stays responsive
        for _ in range(4 * 60 // 5):
            if not runHunters:
                break
            time.sleep(5)

    print('Stop hunters')
    for hunter in ALL_HUNTERS:
        if hunter.name in started_hunters:
            hunter.stop()
    shared_browser.close()

# --- Main Entrypoint ---
if __name__ == "__main__":
    t = threading.Thread(target=run_hunters)
    t.start()
    bot.infinity_polling(timeout=1200)  # Timeout after 20 minutes (1200 seconds)
    runHunters = False
    t.join()
