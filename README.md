# FlyzexBot cPanel Setup Guide

This short guide walks you through deploying FlyzexBot on a shared host that uses **cPanel**. Follow the steps in order and you will have the Telegram bot (and optional FastAPI web panel) running in your hosting environment.

---

## 1. Prepare the Project Files
1. Download the project archive from GitHub or clone it locally.
2. In cPanel, open **File Manager** and upload the project into the folder you want to run it from (for example: `~/flyzexbot`).
3. Make sure the uploaded tree contains:
   - `bot.py`
   - the `flyzexbot/` package
   - the `webapp/` folder (for the optional admin panel)
   - the `config/` folder with `settings.example.yaml`
   - `requirements.txt`

## 2. Create a Python Application in cPanel
1. Open **Setup Python App** in cPanel.
2. Click **Create Application** and choose:
   - Python version **3.10** or newer.
   - Application root pointing to the folder where you uploaded the project (e.g. `~/flyzexbot`).
   - Leave the startup file and entry point empty (the bot is started manually).
3. After the app is created, copy the **Virtual Environment Path** displayed at the top of the page.

## 3. Install Project Dependencies
1. Click the **Run Pip Installer** button in the Python App page, or open the **Terminal** in cPanel.
2. Activate the virtual environment:
   ```bash
   source /home/<cpanel-user>/<venv-path>/bin/activate
   ```
3. Install the requirements inside the environment:
   ```bash
   pip install -r /home/<cpanel-user>/flyzexbot/requirements.txt
   ```

## 4. Configure the Bot
1. Duplicate `config/settings.example.yaml` as `config/settings.yaml` in the same folder.
2. Edit `config/settings.yaml` and set the storage path and other options to match your hosting setup.
3. In the cPanel Python App page, add the following **Environment Variables** (click **Add Variable** for each):
   - `BOT_TOKEN` → your Telegram bot token
   - `ADMIN_API_KEY` → secret key for the admin web routes (any strong string)

## 5. Start FlyzexBot
1. In the cPanel Terminal, make sure the virtual environment is active (`source .../bin/activate`).
2. Run the bot:
   ```bash
   cd /home/<cpanel-user>/flyzexbot
   python bot.py
   ```
3. Leave the terminal open so the bot keeps running. For long-running sessions, consider `tmux`, `screen`, or a background process manager supported by your host.

## 6. (Optional) Run the Web Dashboard
1. The FastAPI admin panel lives in `webapp/`.
2. With the same virtual environment activated, start the server:
   ```bash
   uvicorn webapp.server:app --host 0.0.0.0 --port 8080
   ```
3. Use cPanel **Application Manager** or a reverse proxy (e.g. via `.htaccess`) to expose the chosen port if your hosting plan allows it.

## 7. Keep the App Updated
1. To update the bot, upload the new files (or pull changes via `git`) into the same directory.
2. Re-run `pip install -r requirements.txt` if dependencies changed.
3. Restart the bot process so the new code loads.

---

Need more help? Check the detailed documentation in `README.en.md` or reach out to your hosting provider for assistance with cPanel-specific tools.
