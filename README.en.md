# FlyzexBot

FlyzexBot is a Telegram bot with a glassmorphism-inspired interface that helps guild and group owners manage membership requests, XP, and trophy leaderboards. The project is built on the asynchronous version of `python-telegram-bot` and includes a lightweight FastAPI web app for reviewing stored data.

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Running the Admin WebApp](#running-the-admin-webapp)
- [Testing](#testing)
- [Deployment Tips](#deployment-tips)
- [Project Structure](#project-structure)

## Features
### Private (DM) Flow
- Collects guild membership applications with an inline (glass) UI.
- Allows admins to review, approve, or reject requests.
- Notifies applicants of the final decision.

### Group Flow
- Automatic XP system that rewards active members.
- Ignores helper bot messages to prevent unfair XP gain.
- Trophy (cups) leaderboard with admin-controlled cup creation.
- Members can view, but not modify, leaderboards.
- `/help` provides an in-chat cheat sheet and `/myxp` shows personal progress.
- Glass `/panel` dashboard summarises group stats with quick moderation buttons.

### Security & Reliability
- Persistent JSON storage with optional SQLite backups.
- Rate limiting, logging, and robust exception handling.
- Unit tests for critical modules.

## Architecture Overview
```
FlyzexBotV2/
├─ bot.py                # Telegram bot entrypoint
├─ flyzexbot/            # Core bot logic and handlers
├─ webapp/               # FastAPI app exposing stored data
├─ config/settings.yaml  # Runtime configuration (copy from example)
└─ cachetools/           # Caching helpers used by the bot
```

The bot and web application share the same storage layer so that administrators can inspect pending requests and leaderboards without leaving Telegram.

## Getting Started
### Prerequisites
- Python 3.10+
- A Telegram bot token
- (Optional) An admin API key for the web application

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
1. Copy `config/settings.example.yaml` to `config/settings.yaml` and update the values for your environment.
2. Set the environment variables:
   - `BOT_TOKEN`: Telegram bot token
   - `ADMIN_API_KEY`: token required to access the admin-only HTTP endpoints

## Running the Bot
```bash
python bot.py
```

The storage file defined in `config/settings.yaml` (defaults to `data/storage.json`) is a UTF-8 JSON document that can be inspected with any text editor.

## Running the Admin WebApp
The repository ships with a FastAPI application that exposes pending applications, XP leaderboard, and cup leaderboard.

1. Install dependencies (already covered by `requirements.txt`).
2. Ensure `webapp` settings are configured in `config/settings.yaml` (`host`, `port`, and optional public `url`).
3. Run the bot and the web server in separate processes:
   ```bash
   # Terminal 1
   python bot.py

   # Terminal 2
   uvicorn webapp.server:app --host 0.0.0.0 --port 8080
   ```
4. For production deployments place the web app behind a reverse proxy (e.g., Nginx) and limit access with authentication or network policies.

The default web UI (`webapp/index.html`) offers quick links to:
- `/api/applications/pending`
- `/api/xp`
- `/api/cups`

These endpoints return live data rendered in the interface.

## Testing
```bash
pytest
```

## Deployment Tips
- Consider platforms such as Heroku, AWS, or DigitalOcean for hosting.
- Configure environment variables and set up CI/CD to automate updates.
- Protect the admin API key and rotate it securely if necessary.

## Project Structure
```
FlyzexBotV2/
├─ README.md
├─ README.en.md
├─ README.fa.md
├─ bot.py
├─ config/
├─ flyzexbot/
├─ tests/
└─ webapp/
```
