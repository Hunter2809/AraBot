import re

from arabot.core import Ara, Category, Cog, Context, pfxless
from arabot.core.utils import bold, dsafe
from disnake import Embed
from disnake.ext.commands import command


class Urban(Cog, category=Category.LOOKUP):
    def __init__(self, ara: Ara):
        self.ara = ara

    BASE_URL = "https://api.urbandictionary.com/v0/define"
    QUERY_PREFIX = r"^(?:wh?[ao]t(?:['’]?s|\sis)\s)"
    WORDS_IGNORE = "|".join(
        (
            "up",
            "good",
            "with",
            "it",
            "this",
            "that",
            "so",
            "the",
            "about",
            "goin",
            "happenin",
            "wrong",
            "my",
            "your",
            "ur",
            "next",
            "da",
            "dis",
            "dat",
            "new",
            "he",
            "she",
            "better",
            "worse",
            "tho",
        )
    )

    @command(aliases=["ud"], brief="Search term in Urban Dictionary")
    async def urban(self, ctx: Context, *, term: str):
        for predefined, definition in self.definitions.items():
            if term.lower() == predefined.lower():
                await ctx.send(embed=Embed(description=definition).set_author(name=predefined))
                return

        if not (definitions := await self.fetch_definitions(term)):
            if ctx.prefix:  # if command was invoked directly by user, not by urban_listener
                await ctx.send(f"Definition for {bold(term)} not found")
            return

        ...  # TODO: Embed pagination

    async def fetch_definitions(self, query: str) -> list[str] | None:
        data = await self.session.fetch_json(self.BASE_URL, params={"term": query})
        return data.get("list")

    @pfxless(regex=QUERY_PREFIX + rf"((?:(?!{WORDS_IGNORE}).)*?)\??$")
    async def urban_listener(self, msg):
        if self.urban.enabled:
            term = re.search(self.QUERY_PREFIX + r"(.*?)\??$", msg.content, re.IGNORECASE).group(1)
            await self.urban(await self.ara.get_context(msg), term=term)

    async def cog_load(self):
        await self.ara.wait_until_ready()
        self.definitions = {
            self.ara.name: "An awesome bot written by an awesome guy",
            self.ara.owner.name: "An awesome guy",
        }


def setup(ara: Ara):
    ara.add_cog(Urban(ara))
