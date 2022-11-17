import selfcord
import io
import aiohttp
from secondary import config

log_guild = config["log_guild"]

class Multi_Server_Logger(selfcord.Client):
    async def on_ready(self):
        print(f'Logged in: {self.user} (Selfbot)')
   

    async def create_get_channel(self, ch):
        gu = ch.guild
        serv = self.get_guild(log_guild)
        if gu == serv:
            return None

        category = None
        for c in serv.channels:
            if c.name == serv.name:
                category = c
                break
        if not category:
            category = await serv.create_category(gu.name)

        channel = None
        for c in serv.channels:
            if c.name == ch.name:
                channel = c
                break
        if not channel:
            channel = await serv.create_text_channel(ch.name, category=category)
        return channel
        

    async def on_typing(self, channel, user, when):
        if self.user.id == user.id or log_guild == channel.guild.id:
            return
        ch = await self.create_get_channel(channel)
        await ch.trigger_typing()


    def parse_content(self, string):
        return string.replace("@everyone", "@ evryone").replace("@here", "@ her")


    async def on_message(self, message):
        if message.author.id == self.user.id or message.guild.id == log_guild:
            return

        ch = await self.create_get_channel(message.channel)

        att = []
        for a in message.attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(a.url) as resp:
                    att.append(selfcord.File(io.BytesIO(await resp.read()), a.filename))
       
        message.content = self.parse_content(message.content)
        payload = "`MSG " + f"{message.author.name}#{message.author.discriminator}`".rjust(21)
        
        if message.reference == None:
            await ch.send(payload + f": {message.content}", files=att)
        else:
            messages = [msg async for msg in ch.history(limit=100)]
            pointer = None
            for msg in messages:
                if message.reference.resolved.content in msg.content:
                    pointer = msg
                    break
            if pointer: 
                await ch.send(payload + f" **Replied:** {message.content}", files=att, reference=pointer)
            else:
                await ch.send(payload + f" **Replied:** {message.content}", files=att)


    async def on_message_edit(self, before, after):
        if after.author.id == self.user.id or after.guild.id == log_guild:
            return
        ch = await self.create_get_channel(after.channel)
        
        after.content = self.parse_content(after.content)
        payload = f"`UPD` **Updated:** {after.content}"
        messages = [msg async for msg in ch.history(limit=100)]
        pointer = None
        for msg in messages:
            if before.content in msg.content:
                pointer = msg
                break
        if pointer:
            await ch.send(payload, reference=pointer)
        else:
            await ch.send(payload)

    async def on_message_delete(self, message):
        if message.author.id == self.user.id or message.guild.id == log_guild:
            return

        ch = await self.create_get_channel(message.channel)
        
        payload = "`DEL` **Deleted**"
        messages = [msg async for msg in ch.history(limit=100)]
        pointer = None
        for msg in messages:
            if message.content in msg.content:
                pointer = msg
                break
        if pointer:
            await ch.send(payload, reference=pointer)
        else:
            await ch.send(payload)

        
client = Multi_Server_Logger()
client.run(config["token_selfbot"])
