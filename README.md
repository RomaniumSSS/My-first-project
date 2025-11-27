# AI Goal Coach Bot (MVP)

Telegram bot for goal tracking and coaching using AI (OpenAI GPT-4o).

## Status
Alpha Testing.

## Features
- **Onboarding**: Set your name and main goal.
- **Goal Setting**: Define goals with title, description, and optional moodboard (photo).
- **AI Analysis**: Get feedback and first steps for your goals.
- **Check-ins**: Log progress (text/photo) and get AI feedback.

## Setup

### Prerequisites
- Python 3.11+
- SQLite
- OpenAI API Key
- Telegram Bot Token

### Installation

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   *(Or use `poetry install` if poetry is configured)*

3. Create `.env` file:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_KEY=sk-...
   OPENAI_MODEL=gpt-4o
   # Optional: Whitelist for Alpha (comma separated list of IDs, e.g. [12345, 67890])
   # ALLOWED_USER_IDS=[123456789] 
   ```

4. Initialize DB (if using Aerich or just run the bot as it auto-generates schemas for MVP):
   ```bash
   # If you want to use migrations:
   # aerich upgrade
   ```

### Running
```bash
python src/main.py
```

## Alpha Testing Instructions

**Goal:** Validate that the bot can handle basic goal setting and check-in flows without crashing.

### 1. Access
This bot is currently in **Closed Alpha**.
- If `ALLOWED_USER_IDS` is set in `src/config.py` (or env), only those Telegram User IDs can interact with the bot.
- To find your ID, use `@userinfobot` in Telegram. Add your ID to the whitelist if you are deploying your own instance.

### 2. Test Scenarios

#### A. Onboarding & New Goal
1. Send `/start`.
2. Follow prompts to enter your Name and Main Goal.
3. Send `/new_goal`.
4. Enter Title and Description.
5. (Optional) Send a photo when asked for visualization.
6. **Expected Result**: Bot thinks for a few seconds and returns a structured plan/motivation.

#### B. Check-in (Daily Routine)
1. Send `/checkin`.
2. Select the goal you created.
3. Write a report (e.g., "I did X and Y today") or send a photo proof.
4. **Expected Result**: Bot analyzes the report and gives feedback (Praise + Advice).

### 3. Feedback & Error Reporting
- **Logs**: Errors are logged to `bot.log` file in the root directory. Please attach this file when reporting bugs.
- **Feedback**: Please send your feedback directly to the developer or create an Issue in the repository.
    - What worked well?
    - What was confusing?
    - Did the AI give good advice?
