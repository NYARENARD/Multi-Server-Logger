import selfcord
import io
import aiohttp
import requests
from secondary import config

log_guild = config["log_guild"]
aux_channel = config["aux_channel"]

class Multi_Server_Logger(selfcord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def create_on_events(self, channel):
        gu = channel.guild
        ch = channel
        serv = self.get_guild(log_guild)
        aux = self.get_channel(aux_channel)
        if gu == serv:
            return "WRONG_GUILD"

        messages = [msg async for msg in aux.history(limit=200)]
        exists = 0
        for msg in messages:
            if f"GUILD {gu.id}" in msg.content:
                exists = 1
                pointer = msg
                break
        if exists:
            category = self.get_channel(int(pointer.content.split()[2]))
        else:
            category = await serv.create_category(gu.name)
            await aux.send(f"GUILD {gu.id} {category.id} ({gu.name})")
        
        exists = 0
        for msg in messages:
            if f"CHANNEL {ch.id}" in msg.content:
                exists = 1
                pointer = msg
                break
        if exists:
            new_ch = self.get_channel(int(pointer.content.split()[2]))
        else:
            new_ch = await serv.create_text_channel(ch.name, category=category)
            await aux.send(f"CHANNEL {ch.id} {new_ch.id} ({gu.name} -- {ch.name})")
        return new_ch

    async def on_typing(self, channel, user, when):
        if user.id == self.user.id:
            return
        await self.create_on_events(channel)

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        try:
            ch = await self.create_on_events(message.channel)
        except:
            return

        try:
            fp = requests.get(message.author.display_avatar.url).content
            emoji = await self.get_guild(log_guild).create_custom_emoji(name="avatar", image=fp)
            subload = f"<:{emoji.name}:{emoji.id}>"
        except:
            subload = ""
        att = []
        for a in message.attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(a.url) as resp:
                    att.append(selfcord.File(io.BytesIO(await resp.read()), a.filename))
       
        payload = "`MSG " + f"{message.author.name}#{message.author.discriminator}`".rjust(21) + f"{subload}"
        if message.reference == None:
            await ch.send(payload + f": {message.content}".replace("@everyone", "@ evryone"), files=att)
        else:
            messages = [msg async for msg in ch.history(limit=200)]
            pointer = None
            for msg in messages:
                if message.reference.resolved.content in msg.content:
                    pointer = msg
                    break
            if pointer: 
                await ch.send(payload + f" **Replied:** {message.content}".replace("@everyone", "@ evryone"), files=att, reference=pointer)
            else:
                await ch.send(payload + f" **Replied:** {message.content}".replace("@everyone", "@ evryone"), files=att)
        await self.get_guild(log_guild).delete_emoji(emoji)

    async def on_message_edit(self, before, after):
        if after.author.id == self.user.id:
            return
        try:
            ch = await self.create_on_events(after.channel)
        except:
            return
        
        payload = f"`UPD` **Updated:** {after.content}".replace("@everyone", "@ evryone")
        messages = [msg async for msg in ch.history(limit=200)]
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
        if message.author.id == self.user.id:
            return
        try:
            ch = await self.create_on_events(message.channel)
        except:
            return
        
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
    
    async def on_member_ban(self, guild, user):
        try:
            ch = await self.create_on_events(guild.channel)
        except:
            return
        payload = f"`BAN` **Banned:** {user.name}#{user.discriminator}"
        await ch.send(payload)

        
client = Multi_Server_Logger()
client.run(config["token_selfbot"])
