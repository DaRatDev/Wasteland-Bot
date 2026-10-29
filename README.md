# Wasteland Bot ☢️

A Discord bot for **The Wasteland** that tracks the **Waste-O-Meter**: how close the server is to being a completely barren wasteland. 90 days of total silence = 100%.

> Status: step 2. The Waste-O-Meter is tracking activity and `/wastemeter` shows the current reading. Announcements, visuals and excuses come next.

## How the Waste-O-Meter works

- While the server is quiet, the meter climbs about **1.1% a day**, so 90 silent days = 100%.
- Activity knocks it back down a bit. Every 4 activity points = -1%:
  - a message = 1 point
  - a reaction = 0.25 points
  - each person in voice = 0.1 points per minute (an hour of one person in voice is 6 points, or -1.5%)
- Bots don't count.
- On the very first start, the meter begins based on how long ago the last message in the server was.
- The reading is saved in `data/wasteland.db`, so restarts and updates don't reset it.

The numbers live at the top of `bot/meter.py` if you want to tune them.

## Commands

- `/wastemeter`: shows the current reading
- `/ping`: checks the bot is alive

---

## 1. Create the bot in Discord

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Name it (e.g. `Wasteland Bot`).
2. Open the **Bot** tab:
   - Click **Reset Token**, copy the token and keep it somewhere safe. This is your `DISCORD_TOKEN`.
   - Under **Privileged Gateway Intents**, turn on **Message Content Intent**. Save.
3. Open **OAuth2 → URL Generator**:
   - Scopes: `bot` and `applications.commands`
   - Bot permissions: `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`
   - Open the generated URL and add the bot to The Wasteland.
4. In Discord, turn on **User Settings → Advanced → Developer Mode**. Then:
   - Right-click the server icon → **Copy Server ID**. This is your `GUILD_ID`.
   - Right-click `#general` → **Copy Channel ID**. This is your `ANNOUNCE_CHANNEL_ID`.

## 2. Run it on your Synology NAS (Container Manager)

You need DSM 7.2+ with **Container Manager** installed from Package Center.

1. In **File Station**, create the folder `docker/wasteland-bot` (on `/volume1`).
2. Download this repo (**Code → Download ZIP** on GitHub), unzip it, and upload the contents into that folder so `docker-compose.yml` sits directly inside `docker/wasteland-bot`.
3. Make a copy of `.env.example` called `.env` in the same folder and fill in the three values from step 1. (Tip: edit it on your computer and upload it. File Station hides files starting with `.` unless you enable showing hidden files.)
4. Open **Container Manager → Project → Create**:
   - Project name: `wasteland-bot`
   - Path: `/volume1/docker/wasteland-bot`
   - Source: **Use existing docker-compose.yml**
   - Click through and **Done**. It builds the image and starts the bot.
5. Check **Container → wasteland-bot → Log**. You should see `Logged in as ...` and `Connected to server: The Wasteland`.
6. In Discord, type `/ping`. The bot should reply.

The bot restarts automatically if the NAS reboots. Its saved data goes in `docker/wasteland-bot/data`.

### Updating

Upload the new files over the old ones (keep your `.env` and `data` folder), then in **Container Manager → Project → wasteland-bot** choose **Action → Build**, which rebuilds and restarts it.

### Time zone

The weekly announcement uses the `TZ` value in `docker-compose.yml` (default `America/New_York`). Change it to your [time zone name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) if needed.

## Running locally (optional)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill it in
python -m bot.main
```
