from typing import Collection, Iterator

from hunters.hunter import Prey


class History:
    """Listings that were already notified, stored one per line in a text file."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.seen_apartments = self.load_history()

    def load_history(self) -> set[str]:
        try:
            with open(self.file_path, 'r') as file:
                return {line.strip() for line in file}
        except FileNotFoundError:
            return set()

    def filter(self, preys: Collection[Prey]) -> list[Prey]:
        new_preys = []
        new_lines = []
        for prey in preys:
            line = str(prey).strip() # stripped, like the lines read back from the file
            if line not in self.seen_apartments:
                self.seen_apartments.add(line)
                new_preys.append(prey)
                new_lines.append(line)
        if new_lines:
            self.append_history(new_lines)
        return new_preys

    def append_history(self, lines: list[str]):
        with open(self.file_path, 'a') as file:
            if file.tell() > 0:
                file.write('\n')
            file.write('\n'.join(lines))


def read_listings(file_path: str) -> Iterator[dict]:
    """Yield the listings of a history file one at a time, without loading the whole file."""
    try:
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    name, link, agency, price = line.split('|')
                except ValueError:
                    continue  # Skip malformed lines
                yield {
                    'name': name.strip(),
                    'link': link.strip(),
                    'agency': agency.strip(),
                    'price': price.strip()
                }
    except FileNotFoundError:
        return
