from arabot.core import AnyMember, Ara, Category, Cog, Context
from arabot.core.utils import dtformat
from disnake import Embed, Message
from disnake.ext.commands import command
from disnake.ext.tasks import loop
from disnake.utils import utcnow


class RawDeletedMessage:
    __slots__ = "content", "author", "created_at", "deleted_at"

    def __init__(self, message: Message):
        self.content = message.content
        self.author = message.author
        self.created_at = message.created_at
        self.deleted_at = utcnow()


class Snipe(Cog, category=Category.FUN):
    GROUP_AGE_THRESHOLD = 300  # seconds since last message to end group
    EMPTY_SNIPE_MSG = "Nothing to snipe here 👀"

    def __init__(self, ara: Ara):
        self.ara = ara
        self._cache: dict[int, list[RawDeletedMessage]] = {}
        self.purge_cache.start()

    @Cog.listener()
    async def on_message_delete(self, msg: Message):
        if not msg.author.bot and msg.content:
            self._cache.setdefault(msg.channel.id, []).append(RawDeletedMessage(msg))

    @loop(minutes=1)
    async def purge_cache(self):
        now = utcnow()
        self._cache = {
            channel_id: messages
            for channel_id, messages in self._cache.items()
            for msg in messages
            if (now - msg.deleted_at).total_seconds() <= 3600
        }

    @command(brief="View deleted messages within the last hour")
    async def snipe(self, ctx: Context, *, target: AnyMember = False):
        if target is None:
            await ctx.send("User not found")
            return
        if ctx.channel.id not in self._cache:
            await ctx.send(self.EMPTY_SNIPE_MSG)
            return
        msg_pool = list(
            filter(
                lambda m: not target or m.author == target,
                sorted(self._cache[ctx.channel.id], key=lambda msg: msg.created_at)[-10:],
            )
        )
        if not msg_pool:
            await ctx.send(self.EMPTY_SNIPE_MSG)
            return
        embed = Embed(color=0x87011D)
        msg_group = []
        last_sender = msg_pool[0].author
        group_tail = msg_pool[0].created_at
        group_start = msg_pool[0].created_at

        for msg in msg_pool:
            if (
                msg.author != last_sender
                or (msg.created_at - group_tail).seconds >= self.GROUP_AGE_THRESHOLD
            ):
                field_name = f"{last_sender.display_name}, {dtformat(group_start)}:"
                msg_group = "\n".join(msg_group)[-1024:]
                embed.add_field(field_name, msg_group, inline=False)
                msg_group = []
                last_sender = msg.author
                group_start = msg.created_at
            group_tail = msg.created_at
            msg_group.append(msg.content)
        field_name = f"{last_sender.display_name}, {dtformat(group_start)}:"
        msg_group = "\n".join(msg_group)[-1024:]
        embed.add_field(field_name, msg_group, inline=False)
        while len(embed) > 6000:
            embed.remove_field(0)
        await ctx.send(embed=embed)

    @command(brief="View the last deleted message")
    async def last(self, ctx: Context, *, target: AnyMember = False):
        if target is None:
            await ctx.send("User not found")
            return
        if ctx.channel.id not in self._cache:
            await ctx.send(self.EMPTY_SNIPE_MSG)
            return
        try:
            last_msg = next(
                filter(
                    lambda m: not target or m.author == target,
                    reversed(self._cache[ctx.channel.id]),
                )
            )
        except StopIteration:
            await ctx.send(self.EMPTY_SNIPE_MSG)
            return
        embed = Embed(color=0x87011D)
        field_name = f"{last_msg.author.display_name}, {dtformat(last_msg.created_at)}:"
        embed.add_field(field_name, last_msg.content[-1024:])
        await ctx.send(embed=embed)

    @purge_cache.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    def cog_unload(self):
        self.purge_cache.cancel()


def setup(ara: Ara):
    ara.add_cog(Snipe(ara))
