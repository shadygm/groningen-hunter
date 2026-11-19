# Netherlands Apartment Hunter Bot

This Python bot helps you find your perfect apartment in the Netherlands. It continuously checks various apartment rental websites, looking for new listings that match your preferences. Whenever it finds a potential match, the bot sends a notification to your Telegram account. (Yes I did find the place I'm living today using this bot 😜)

<p align="center">
  <img src="https://github.com/brenocq/groningen-hunter/assets/17342434/6a83c8bc-a704-4d02-be39-b0df89974cc3">
</p>

## Features

- Monitors several apartment rental websites, including Pararius, Kamernet, 123Wonen, and more.
- Periodically refreshes the pages to find new listings.
- Sends Telegram notifications for new apartments that match your preferences.
- Supports multiple users, each with their own cities and price filters.
- Uses threading for efficient resource usage, with one thread running the Telegram bot and another managing the apartment-hunting process.

## Getting the bot to work

### Create a Telegram bot

On Telegram, search for "BotFather"
Send him the message

```
/newbot
```

Follow the BotFather steps!

When you are done, he should tell you the HTTP API token, we'll need this later.

### Windows setup

We will install the Windows Subsystem for Linux (WSL). Open the "Windows PowerShell" and run the following command:

```
wsl --install
```

Restart the computer and open the Ubuntu program. You can now follow the Ubuntu setup.

### Ubuntu setup

If you don't have docker installed, install docker.

```
sudo snap install docker
sudo groupadd docker
sudo usermod -aG docker ${USER}
newgrp docker
sudo chown root:docker /var/run/docker.sock
```

Then, clone the repository and build the Netherlands Apartment Hunter.

```
git clone https://github.com/brenocq/groningen-hunter.git
cd groningen-hunter
./hunter.sh --build
```

### Running the bot

Before running the bot, we need to set the Telegram HTTP API token (the one you got from the BotFather)

```
./hunter.sh --set-bot-token "YOUR-TELEGRAM-BOT-TOKEN"
./hunter.sh --run
```

The bot is now running, but we need to subscribe to be able to receive the apartment notifications in our Telegram chat. Send the following message to your bot on Telegram.

```
/subscribe
```

Then, select the cities you want to monitor with the `/start` command, and optionally configure your price filters. Each user has their own cities and price filters. For example:

```
/start
/set_max_price 1000
/set_min_price 300
```

All set up! You can now leave the bot running and wait for the notifications :)

```
./hunter.sh --run
```

If you implement new hunters or develop new features, please create a PR. If you find any bugs, please open a new issue. All help is welcome ;)

### Running as a systemd service

If you prefer not to use Docker, you can run the bot directly on any Linux system with APT and systemd as a systemd service.

```
git clone https://github.com/brenocq/groningen-hunter.git
cd groningen-hunter
./hunter.sh --set-bot-token "YOUR-TELEGRAM-BOT-TOKEN"
sudo ./setup-systemd.sh
```

To upgrade after pulling new code, just re-run `sudo ./setup-systemd.sh`. Configuration and history will be preserved.

#### Useful commands:

```
systemctl status groningen-hunter       # check service status
journalctl -u groningen-hunter -f       # follow the logs
sudo systemctl restart groningen-hunter # restart the bot
sudo ./setup-systemd.sh --uninstall     # remove the service
```

### Telegram Bot Commands

Once the bot is running, you can interact with it using the following commands:

- `/start` - Select the cities to monitor for apartment listings.
- `/subscribe` - Subscribe to receive apartment notifications.
- `/unsubscribe` - Unsubscribe from apartment notifications.
- `/status` - Check your selected cities and price filters.
- `/list` - Display the apartment listings found so far (filtered by your price filters).
- `/set_min_price <amount>` - Set your minimum price filter.
- `/set_max_price <amount>` - Set your maximum price filter.
- `/help` - Display a list of available commands and their descriptions.

## License

This project is licensed under the terms of the MIT License. See the [LICENSE](LICENSE) file for the full text.
