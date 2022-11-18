import selfcord
from selfcord.ext.tasks import loop
import io
import aiohttp
import os
from secondary import config

log_guild = config["log_guild"]
prefix = '!'
commands = ["link", "file"]
commands = [prefix + c for c in commands]

class Multi_Server_Logger(selfcord.Client):
    
    #EVENTS
    
    async def on_ready(self):
        print(f'Logged in: {self.user} (Selfbot)')
        
        
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
        await channel.send(f"`Banned:` {user.name}#{user.discriminator}")
    
    
    async def on_typing(self, channel, user, when):
        if self.user.id == user.id or log_guild == channel.guild.id:
            return
        ch = await self.create_get_channel(channel)
        await ch.trigger_typing()
    
    
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        if message.guild.id == log_guild:
            if message.content.split(' ')[0] == "!file":
                return await self.tofile(message)
            elif message.content.split(' ')[0] == "!link":
                return await self.getlink(message)
            else:
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
    
    
    #COMMANDS
    
    async def tofile(self, message):
        lst = message.content.split(' ', 3)
        filename = lst[1]
        filelen = int(lst[2])
        request = lst[3]
        await message.add_reaction('💬')
        with open(filename, 'w', encoding="utf-8") as f:
            counter = 0
            for message in [msg async for msg in message.channel.history(limit=10000)]:
                if request in message.content:
                    f.write(message.content + '\n')
                    counter += 1
                    if counter >= filelen:
                        break
        await message.channel.send(file=selfcord.File(filename))
        await message.add_reaction('✅')
        os.remove(filename)
    
    async def getlink(self, message):
        reference = message.reference.resolved
        guild_tosearch = reference.channel.category.name
        channel_tosearch = reference.channel.name
        channel = None
        for g in self.guilds:
            if g.name == guild_tosearch:
                for ch in g.channels:
                    if ch.name == channel_tosearch:
                        channel = ch
                        break
        if not channel:
            await message.channel.send("Сервер или канал не найден.")
            return
        pointer = None
        messages = [msg async for msg in channel.history(limit=10000)]
        for m in messages:
            if m.content.partition(": ")[2] in reference.content:
                pointer = m
                break
        messages = None
        if not pointer:
            await message.channel.send("Оригинальное сообщение не найдено.")
            return
        link = f"https://discord.com/channels/{pointer.guild.id}/{pointer.channel.id}/{pointer.id}"
        await message.channel.send(link)
    
    #HELPER-FUNCS
    
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
    
    
    def parse_content(self, string):
        return string.replace("@everyone", "@ evryone").replace("@here", "@ her")
    
    
    #LOOP
    
    async def setup_hook(self) -> None:
        self.del_empty_channels.start()
    
    @loop(seconds=120)
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
        
        
client = Multi_Server_Logger()
client.run(config["token_selfbot"])
