# 🤖 PoofiBot – Discord Bot

PoofiBot is a multifunctional Discord bot built with Python. It features slash commands, anime GIFs, reaction roles, and automatic welcome messages for new members.
It is uniquely made for [Twitch/Livemetmarrit](https://twitch.tv/livemetmarrit) to fit the needs for her discord community.

---

## 🚀 Features

### ✅ Prefix Commands
- `!setup_reactroles` – Automatically posts a message with emoji-based role selection. Available only to admins
- `!purge (amount)` - Removes messages of the amount specfied. Available only to those with manage_messages permissions

### ✅ Slash Commands
- `/help` - Shows a list of all the commands of this bot.
- `/regels` - Showws a list of all the rules of the discord server
- `/anime` – Sends a random anime GIF using the Nekos API.
- `/poll` - Lets users create a poll in which can a make a statement and add answers with emoij reactions in numbers.
- 

### 📌 Reaction Roles
Users can react to a message with emojis to gain or remove roles. The bot remembers the setup even after restarts by storing the message ID in `reaction_config.json`.

### 👋 Welcome Message
Automatically sends a welcome message in a specific channel when a new member joins your server.
Also automatically assigns the user with a specified role.

---
