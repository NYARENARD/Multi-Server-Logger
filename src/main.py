import selfcord
from selfcord.ext.tasks import loop
import io
import aiohttp
from secondary import config

log_guild = config["log_guild"]

class Multi_Server_Logger(selfcord.Client):
    async def on_ready(self):
        print(f'Logged in: {self.user} (Selfbot)')
       
    
    async def setup_hook(self) -> None:
        self.del_empty_channels.start()
    
    @loop(seconds=60)
    async def del_empty_channels(self):
        serv = self.get_guild(log_guild)
        for ch in serv.text_channels:
            try:
                if [msg async for msg in ch.history(limit=1)] == []:
                    await ch.delete(reason="Empty channel.")
            except:
                return
                
    @del_empty_channels.before_loop
    async def before_loop(self):
        await self.wait_until_ready()
                

    async def create_get_channel(self, ch):
        gu = ch.guild
        serv = self.get_guild(log_guild)
        if gu == serv:
            return None

        category = None
        for c in serv.categories:
            if c.name == gu.name:
                category = c
                break
        if not category:
            category = await serv.create_category(gu.name)

        channel = None
        for c in serv.text_channels:
            if c.name == ch.name.replace(' ', '-').lower():
                channel = c
                break
        if not channel:
            channel = await serv.create_text_channel(ch.name, category=category)
        return channel
        
    async def on_member_join(self, member):
        if self.user.id == member.id:
            return
        serv = self.get_guild(log_guild)
        category = None
        channel = None
        for cat in serv.categories:
            if cat.name == member.guild.name:
                category = cat
                break
        for ch in category.text_channels:
            if ch.name == "joined-left":
                channel = ch
                break
        if not channel:
            channel = await serv.create_text_channel("joined-left", category=category)
        await channel.send(f"`Joined:` {member.name}#{member.discriminator}")
        
    async def on_member_remove(self, member):
        if self.user.id == member.id:
            return
        serv = self.get_guild(log_guild)
        category = None
        channel = None
        for cat in serv.categories:
            if cat.name == member.guild.name:
                category = cat
                break
        for ch in category.text_channels:
            if ch.name == "joined-left":
                channel = ch
                break
        if not channel:
            channel = await serv.create_text_channel("joined-left", category=category)
        await channel.send(f"`  Left:` {member.name}#{member.discriminator}")
    
    async def on_member_ban(self, guild, user):
        if self.user.id == user.id or log_guild == guild.id:
            return
        serv = self.get_guild(log_guild)
        category = None
        channel = None
        for cat in serv.categories:
            if cat.name == guild.name:
                category = cat
                break
        for ch in category.text_channels:
            if ch.name == "joined-left":
                channel = ch
                break
        if not channel:
            channel = await serv.create_text_channel("joined-left", category=category)
        await channel.send(f"`Banned:` {member.name}#{member.discriminator}")
    
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
        messages = [msg async for msg in ch.history(limit=200)]
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
