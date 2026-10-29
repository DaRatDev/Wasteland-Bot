import logging

import discord
from discord import app_commands

from . import config

log = logging.getLogger("wasteland")


class WastelandBot(discord.Client):
    def __init__(self, cfg: config.Config):
        intents = discord.Intents.default()
        intents.message_content = True  # needed to see messages for the Waste-O-Meter
        intents.voice_states = True     # needed to track people in voice
        super().__init__(intents=intents)
        self.cfg = cfg
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        @self.tree.command(name="ping", description="Check if anyone's still out there.")
        async def ping(interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                f"📻 ...signal received. Barely. ({round(self.latency * 1000)} ms through the dust)"
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


def main() -> None:
    cfg = config.load()
    logging.basicConfig(
        level=cfg.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    WastelandBot(cfg).run(cfg.token, log_handler=None)


if __name__ == "__main__":
    main()
