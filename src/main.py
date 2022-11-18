import selfcord
from selfcord.ext.tasks import loop
from selfcord.ext import commands
import io
import aiohttp
import os
import asyncio
from secondary import config


bot = commands.Bot(command_prefix='!', self_bot=True)
log_guild = config["log_guild"]
token = config["token_selfbot"]

#EVENTS

@bot.event
async def on_ready():
    print(f'Logged in: {bot.user} (Selfbot)')
       
     
@bot.event
async def on_member_join(member):
    if bot.user.id == member.id:
        return
    serv = bot.get_guild(log_guild)
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


@bot.event  
async def on_member_remove(member):
    if bot.user.id == member.id:
        return
    serv = bot.get_guild(log_guild)
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


@bot.event    
async def on_member_ban(guild, user):
    if bot.user.id == user.id or log_guild == guild.id:
        return
    serv = bot.get_guild(log_guild)
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


@bot.event    
async def on_typing(channel, user, when):
    if bot.user.id == user.id or log_guild == channel.guild.id:
        return
    ch = await bot.create_get_channel(channel)
    await ch.trigger_typing()


@bot.event
async def on_message(message):
    if message.author.id == bot.user.id or message.guild.id == log_guild:
        return
    ch = await bot.create_get_channel(message.channel)
    att = []
    for a in message.attachments:
        async with aiohttp.ClientSession() as session:
            async with session.get(a.url) as resp:
                att.append(selfcord.File(io.BytesIO(await resp.read()), a.filename))
   
    message.content = bot.parse_content(message.content)
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


@bot.event
async def on_message_edit(before, after):
    if after.author.id == bot.user.id or after.guild.id == log_guild:
        return
    ch = await bot.create_get_channel(after.channel)
    
    after.content = bot.parse_content(after.content)
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


@bot.event
async def on_message_delete(message):
    if message.author.id == bot.user.id or message.guild.id == log_guild:
        return
    ch = await bot.create_get_channel(message.channel)
    
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

@bot.command(aliases=["file", "файл"])
async def tofile(ctx, filename: str = "log.txt", filelen: int = 100, request: str = ''):
    if ctx.guild.id != log_guild or ctx.author == bot.user.id:
        return
    await ctx.message.add_reaction('💬')
    with open(filename, 'w', encoding="utf-8") as f:
        counter = 0
        for message in [msg async for msg in ctx.channel.history(limit=10000)]:
            if request in message:
                f.write(message + '\n')
                counter += 1
                if counter >= filelen:
                    break
    await ctx.send(file=filename)
    await ctx.message.add_reaction('✅')
    os.remove(filename)

@bot.command(aliases=["link", "ссылка", "ссылку"])
async def getlink(ctx):
    if ctx.guild.id != log_guild or ctx.author == bot.user.id:
        return
    reference = ctx.message.reference.resolved
    guild_tosearch = reference.category.name
    channel_tosearch = reference.channel.name

    channel = None
    for g in bot.guilds:
        if g.name == guild_tosearch:
            for ch in g.channels:
                if ch.name == channel_tosearch:
                    channel = ch
                    break
    if not channel:
        await ctx.send("Сервер или канал не найден.")
        return

    pointer = None
    messages = [msg async for msg in channel.history(limit=10000)]
    for m in messages:
        if reference.content in m.partition(": ")[2]:
            pointer = m
            break
    messages = None
    if not pointer:
        await ctx.send("Оригинальное сообщение не найдено.")
        return
    
    link = f"https://discord.com/channels/{pointer.guild.id}/{pointer.channel.id}/{pointer.id}"
    await ctx.send(link)


#LOOP


@loop(seconds=120)
async def del_empty_channels():
    serv = bot.get_guild(log_guild)
    for ch in serv.text_channels:
        try:
            if [msg async for msg in ch.history(limit=1)] == []:
                await ch.delete(reason="Empty channel.")
        except:
            return
                
@del_empty_channels.before_loop
async def before_loop():
    await bot.wait_until_ready()
                

#FUNCS-HELPERS


async def create_get_channel(ch):
    gu = ch.guild
    serv = bot.get_guild(log_guild)
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
    
def parse_content(string):
    return string.replace("@everyone", "@ evryone").replace("@here", "@ her")

asyncio.run(del_empty_channels())
bot.run(token)
