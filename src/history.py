from typing import Collection

from hunters.hunter import Prey


class History:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.seen_apartments = self.load_history()

    def load_history(self):
        try:
            with open(self.file_path, 'r') as file:
                seen_apartments = [line.strip() for line in file]
        except FileNotFoundError:
            seen_apartments = []
        return seen_apartments

    def save_history(self):
        with open(self.file_path, 'w') as file:
            file.write('\n'.join(self.seen_apartments))

    def filter(self, preys: Collection[Prey]):
        new_preys = [prey for prey in preys if str(prey) not in self.seen_apartments]
        self.seen_apartments.extend(str(prey) for prey in new_preys)
        self.save_history()
        return new_preys

    def get_all(self):
        """Retrieve all listings from the history file."""
        listings = []
        for line in self.seen_apartments:
            try:
                name, link, agency, price = line.split('|')
                listings.append({
                    'name': name.strip(),
                    'link': link.strip(),
                    'agency': agency.strip(),
                    'price': price.strip()
                })
            except ValueError:
                continue  # Skip malformed lines
        return listings

    def save_listing(self, name, link, agency, price):
        """Save a new listing to the history file."""
        entry = f"{name} | {link} | {agency} | {price}"
        if entry not in self.seen_apartments:
            self.seen_apartments.append(entry)
            self.save_history()
