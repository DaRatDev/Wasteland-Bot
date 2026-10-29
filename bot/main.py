import logging
import time

import discord
from discord import app_commands
from discord.ext import tasks

from . import config, meter
from .store import Store

log = logging.getLogger("wasteland")

VERSION = "0.2.0"
TICK_MINUTES = 5


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
                f"☢️ **Waste-O-Meter: {self.state.percent:.1f}%** of the way to a completely barren wasteland."
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
        current = meter.milestone(self.state.percent)
        if current != self.last_milestone:
            log.info("Waste-O-Meter crossed from %d%% to %d%%", self.last_milestone, current)
            # Announcing the change in #general comes in step 3
            self.last_milestone = current

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

    # --- activity events --------------------------------------------------

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not self._is_tracked(message.guild):
            return
        self._record("message")

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
