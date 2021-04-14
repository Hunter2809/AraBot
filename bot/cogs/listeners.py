from discord.ext.commands import Cog, CommandNotFound
from discord.ext.commands.errors import (
    CommandOnCooldown,
    MissingPermissions,
    CheckFailure,
    BadArgument,
    MissingRequiredArgument,
    ExpectedClosingQuoteError,
)
from ..utils.general import set_presence


class Listeners(Cog):
    def __init__(self, client):
        self.bot = client

    @Cog.listener()
    async def on_ready(self):
        await set_presence(self.bot, 3, "#lewd")
        print("Ready!")

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            if not ctx.command.hidden:
                await ctx.reply(f"Cooldown expires in {error.retry_after:.0f} seconds")
            return
        if isinstance(error, MissingPermissions):
            if not ctx.command.hidden:
                await ctx.reply("Missing permissions")
            return
        if hasattr(ctx.command, "on_error") or isinstance(
            error,
            (  # Ignore following errors
                CommandNotFound,
                CheckFailure,
                BadArgument,
                MissingRequiredArgument,
                ExpectedClosingQuoteError,
            ),
        ):
            return
        raise error


def setup(client):
    client.add_cog(Listeners(client))
