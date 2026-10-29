import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    return int(value) if value else None


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: int | None
    announce_channel_id: int | None
    data_dir: Path
    log_level: str


def load() -> Config:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    return Config(
        token=token,
        guild_id=_int("GUILD_ID"),
        announce_channel_id=_int("ANNOUNCE_CHANNEL_ID"),
        data_dir=data_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
