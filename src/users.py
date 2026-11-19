import json
import threading
from typing import Optional


class UserStore:
    """Thread-safe per-chat user settings, persisted to a JSON file.

    Each entry maps a chat ID to its settings:
        {"cities": [...], "min_price": int | None, "max_price": int | None}
    A chat is subscribed if and only if it has an entry.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = threading.Lock()
        self.users: dict[str, dict] = self._load()

    def _load(self) -> dict:
        try:
            with open(self.file_path, 'r') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f'Warning: could not parse {self.file_path}, starting with no users')
            return {}

    def _save(self):
        # Write in place (no atomic rename): the file may be bind-mounted into
        # a Docker container, and replacing it would break the mount.
        with open(self.file_path, 'w') as f:
            json.dump(self.users, f, indent=2)

    # Create a record if missing and return whether it was created. Caller must hold the lock.
    def _ensure(self, chat_id: str) -> bool:
        if chat_id not in self.users:
            self.users[chat_id] = {'cities': [], 'min_price': None, 'max_price': None}
            return True
        return False

    def migrate_legacy(self, chat_id_csv: Optional[str], min_price: Optional[str], max_price: Optional[str]):
        """Import subscribers from the old global .env configuration (CHAT_ID, MINIMUM_PRICE, MAXIMUM_PRICE)."""
        with self.lock:
            if self.users or chat_id_csv is None or not chat_id_csv.strip():
                return
            for chat_id in chat_id_csv.split(','):
                chat_id = chat_id.strip()
                if not chat_id:
                    continue
                self.users[chat_id] = {
                    'cities': [],
                    'min_price': self._parse_price(min_price),
                    'max_price': self._parse_price(max_price),
                }
            self._save()
            print(f'Migrated {len(self.users)} subscriber(s) from the legacy .env configuration')

    @staticmethod
    def _parse_price(price: Optional[str]) -> Optional[int]:
        try:
            return int(price)
        except (TypeError, ValueError):
            return None

    def subscribe(self, chat_id: str) -> bool:
        """Return True if the chat was newly subscribed, False if it already was."""
        with self.lock:
            created = self._ensure(chat_id)
            if created:
                self._save()
            return created

    def unsubscribe(self, chat_id: str) -> bool:
        """Return True if the chat was subscribed, False otherwise."""
        with self.lock:
            if chat_id in self.users:
                del self.users[chat_id]
                self._save()
                return True
            return False

    def get_settings(self, chat_id: str) -> Optional[dict]:
        with self.lock:
            settings = self.users.get(chat_id)
            return dict(settings) if settings is not None else None

    # The setters subscribe the chat if needed and return True when it was newly subscribed
    def set_cities(self, chat_id: str, cities: set[str]) -> bool:
        with self.lock:
            created = self._ensure(chat_id)
            self.users[chat_id]['cities'] = sorted(cities)
            self._save()
            return created

    def set_min_price(self, chat_id: str, price: int) -> bool:
        with self.lock:
            created = self._ensure(chat_id)
            self.users[chat_id]['min_price'] = price
            self._save()
            return created

    def set_max_price(self, chat_id: str, price: int) -> bool:
        with self.lock:
            created = self._ensure(chat_id)
            self.users[chat_id]['max_price'] = price
            self._save()
            return created

    def all_cities(self) -> set[str]:
        """Union of the cities selected by all subscribed users."""
        with self.lock:
            return {city for user in self.users.values() for city in user['cities']}

    def recipients_for(self, city: Optional[str], price: Optional[int]) -> list[str]:
        """Chat IDs to notify about a listing in `city` at `price`.

        A price of None (unparsable) skips the price filters so the listing is not lost.
        """
        with self.lock:
            recipients = []
            for chat_id, user in self.users.items():
                if city not in user['cities']:
                    continue
                if price is not None:
                    if user['min_price'] is not None and price < user['min_price']:
                        continue
                    if user['max_price'] is not None and price > user['max_price']:
                        continue
                recipients.append(chat_id)
            return recipients
