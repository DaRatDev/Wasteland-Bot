import asyncio
from types import SimpleNamespace

from bot import messages
from bot.main import WastelandBot


def test_excuse_never_repeats_twice_in_a_row():
    previous = None
    for _ in range(200):
        current = messages.excuse()
        assert current != previous
        previous = current


class FakeMessage:
    def __init__(self, author_id):
        self.author = SimpleNamespace(id=author_id)
        self.replies = []

    async def reply(self, text, mention_author=True):
        self.replies.append(text)


def test_cooldown_per_person():
    bot = SimpleNamespace(last_excuse_at={})
    a, a2, b = FakeMessage(1), FakeMessage(1), FakeMessage(2)
    asyncio.run(WastelandBot._reply_with_excuse(bot, a))
    asyncio.run(WastelandBot._reply_with_excuse(bot, a2))  # same person, too soon
    asyncio.run(WastelandBot._reply_with_excuse(bot, b))
    assert len(a.replies) == 1 and len(a2.replies) == 0 and len(b.replies) == 1


def test_is_addressed():
    me = object()
    bot = SimpleNamespace(user=me)
    guild = object()

    def msg(mentions=(), replied_to=None, in_guild=True):
        ref = SimpleNamespace(resolved=replied_to) if replied_to is not None else None
        return SimpleNamespace(guild=guild if in_guild else None, mentions=list(mentions), reference=ref)

    import discord
    from unittest import mock

    bot_message = mock.Mock(spec=discord.Message)
    bot_message.author = me
    other_message = mock.Mock(spec=discord.Message)
    other_message.author = object()

    assert WastelandBot._is_addressed(bot, msg(mentions=[me]))
    assert WastelandBot._is_addressed(bot, msg(in_guild=False))
    assert WastelandBot._is_addressed(bot, msg(replied_to=bot_message))
    assert not WastelandBot._is_addressed(bot, msg(replied_to=other_message))
    assert not WastelandBot._is_addressed(bot, msg(mentions=[object()]))
