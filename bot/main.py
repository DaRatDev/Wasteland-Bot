import asyncio
import io
import logging
import time
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import tasks

from . import config, messages, meter, visual
from .store import Store

log = logging.getLogger("wasteland")

VERSION = "0.4.0"
TICK_MINUTES = 5
EXCUSE_COOLDOWN_SECONDS = 30  # per person, so the bot can't be spammed


class WastelandBot(discord.Client):
    def __init__(self, cfg: config.Config):
        intents = discord.Intents.default()
        intents.message_content = True  # needed to see messages for the Waste-O-Meter
        intents.voice_states = True     # needed to track people in voice
        super().__init__(intents=intents)
        self.cfg = cfg
        self.tree = app_commands.CommandTree(self)
        self.store = Store(cfg.data_dir)
        self.state: meter.MeterState | None = None
        self.last_milestone = 0
        self.last_excuse_at: dict[int, float] = {}

    # --- setup -----------------------------------------------------------

    async def setup_hook(self) -> None:
        @self.tree.command(name="ping", description="Check if anyone's still out there.")
        async def ping(interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                f"📻 ...signal received. Barely. ({round(self.latency * 1000)} ms through the dust)"
            )

        @self.tree.command(name="wastemeter", description="How close is this place to a barren wasteland?")
        async def wastemeter(interaction: discord.Interaction) -> None:
            if self.state is None:
                await interaction.response.send_message("The Waste-O-Meter is still warming up. Try again in a moment.")
                return
            self._climb()
            await interaction.response.send_message(
                f"☢️ **Waste-O-Meter: {self.state.percent:.1f}%** of the way to a completely barren wasteland.",
                file=self._meter_image(),
            )

        # Syncing to one guild makes slash commands show up instantly
        if self.cfg.guild_id:
            guild = discord.Object(id=self.cfg.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id %s)", self.user, self.user.id)
        for guild in self.guilds:
            log.info("Connected to server: %s (id %s)", guild.name, guild.id)

        channel = self.get_channel(self.cfg.announce_channel_id) if self.cfg.announce_channel_id else None
        if channel is None:
            log.warning("ANNOUNCE_CHANNEL_ID not set or not visible; announcements will be skipped")
        else:
            log.info("Announcements will go to #%s", channel.name)

        # on_ready can fire again after a reconnect; only set up the meter once
        if self.state is None:
            self._load_meter()
            self.tick.start()

    def _guild(self) -> discord.Guild | None:
        if self.cfg.guild_id:
            return self.get_guild(self.cfg.guild_id)
        return self.guilds[0] if self.guilds else None

    def _load_meter(self) -> None:
        saved = self.store.load()
        if saved:
            self.state, self.last_milestone = saved
            log.info("Loaded Waste-O-Meter at %.1f%%", self.state.percent)
        else:
            days = self._days_since_last_message()
            self.state = meter.from_silence(days, time.time())
            self.last_milestone = meter.milestone(self.state.percent)
            log.info("First run: last message was %.1f days ago, starting at %.1f%%", days, self.state.percent)
        self._climb()
        self._save()

    def _days_since_last_message(self) -> float:
        guild = self._guild()
        if guild is None:
            return 0.0
        latest = None
        for channel in guild.text_channels:
            if channel.last_message_id:
                sent = discord.utils.snowflake_time(channel.last_message_id).timestamp()
                latest = sent if latest is None else max(latest, sent)
        if latest is None:
            return 0.0
        return max(0.0, time.time() - latest) / 86400

    # --- meter bookkeeping ------------------------------------------------

    def _climb(self) -> None:
        self.state = meter.climb(self.state, time.time())

    def _save(self) -> None:
        self.store.save(self.state, self.last_milestone)

    def _record(self, kind: str, amount: float = 1.0) -> None:
        if self.state is None:
            return
        points = meter.POINTS[kind] * amount
        self.store.log_activity(kind, points)
        self._climb()
        self.state = meter.knock_down(self.state, points)
        self._check_milestone()
        self._save()

    def _check_milestone(self) -> None:
        mark = meter.next_announced_mark(self.state.percent, self.last_milestone)
        if mark is None:
            return
        log.info("Waste-O-Meter moved from the %d%% mark to %d%%", self.last_milestone, mark)
        text = messages.mark_reached(mark, self.last_milestone)
        self.last_milestone = mark
        asyncio.get_running_loop().create_task(self._announce(text))

    # --- announcements ----------------------------------------------------

    def _meter_image(self) -> discord.File:
        png = visual.render(self.state.percent)
        return discord.File(io.BytesIO(png), filename="waste-o-meter.png")

    async def _announce(self, text: str) -> None:
        channel = self.get_channel(self.cfg.announce_channel_id) if self.cfg.announce_channel_id else None
        if channel is None:
            log.warning("Skipping announcement, no announcement channel: %s", text)
            return
        try:
            await channel.send(text, file=self._meter_image())
        except discord.HTTPException:
            log.exception("Could not post announcement")

    def _last_weekly_slot(self, now: datetime) -> datetime:
        """The most recent weekly report time at or before now."""
        slot = now.replace(hour=self.cfg.weekly_hour, minute=0, second=0, microsecond=0)
        slot -= timedelta(days=(now.weekday() - self.cfg.weekly_day) % 7)
        if slot > now:
            slot -= timedelta(days=7)
        return slot

    async def _maybe_post_weekly(self) -> None:
        now = datetime.now(self.cfg.timezone)
        slot = self._last_weekly_slot(now)
        last = self.store.get_meta("last_weekly")
        if last is None:
            # First run: don't post straight away, wait for the next slot
            self.store.set_meta("last_weekly", slot.isoformat())
            return
        if datetime.fromisoformat(last) >= slot:
            return
        self.store.set_meta("last_weekly", slot.isoformat())
        # If the bot was offline for a day or more, skip this one instead of posting late
        if now - slot > timedelta(days=1):
            return
        await self._announce(messages.weekly(self.state.percent))

    def _is_tracked(self, guild: discord.Guild | None) -> bool:
        if guild is None:
            return False
        return self.cfg.guild_id is None or guild.id == self.cfg.guild_id

    @tasks.loop(minutes=TICK_MINUTES)
    async def tick(self) -> None:
        guild = self._guild()
        people_in_voice = 0
        if guild:
            for channel in guild.voice_channels + guild.stage_channels:
                people_in_voice += sum(1 for m in channel.members if not m.bot)
        if people_in_voice:
            self._record("voice_minute", people_in_voice * TICK_MINUTES)
        else:
            self._climb()
            self._check_milestone()
            self._save()
        log.debug("Tick: %.2f%% (%d in voice)", self.state.percent, people_in_voice)
        await self._maybe_post_weekly()

    # --- activity events --------------------------------------------------

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if self._is_addressed(message):
            await self._reply_with_excuse(message)
        if self._is_tracked(message.guild):
            self._record("message")

    def _is_addressed(self, message: discord.Message) -> bool:
        """True for a DM, an @mention of the bot, or a reply to one of its messages."""
        if message.guild is None:
            return True
        if self.user in message.mentions:
            return True
        ref = message.reference
        resolved = ref.resolved if ref else None
        return isinstance(resolved, discord.Message) and resolved.author == self.user

    async def _reply_with_excuse(self, message: discord.Message) -> None:
        now = time.monotonic()
        if now - self.last_excuse_at.get(message.author.id, -EXCUSE_COOLDOWN_SECONDS) < EXCUSE_COOLDOWN_SECONDS:
            return
        self.last_excuse_at[message.author.id] = now
        try:
            await message.reply(messages.excuse(), mention_author=False)
        except discord.HTTPException:
            log.exception("Could not reply with an excuse")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.member is None or payload.member.bot:
            return
        if not self._is_tracked(payload.member.guild):
            return
        self._record("reaction")


def main() -> None:
    cfg = config.load()
    logging.basicConfig(
        level=cfg.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    log.info("Wasteland Bot v%s starting", VERSION)
    WastelandBot(cfg).run(cfg.token, log_handler=None)


if __name__ == "__main__":
    main()
