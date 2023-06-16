import discord
from config import settings
from discord.ui import Button, View
from discord.ext import commands
import json

ticket_category_name = "Тикеты"
role_name = '🕑 Гость'

def get_server_prefix(client, message):
    with open("prefix.json","r") as f:
        prefix = json.load(f)
    
    return prefix[str(message.guild.id)]

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True
intents.guild_messages = True
bot = commands.Bot(command_prefix= get_server_prefix, intents=intents)

@bot.command()
async def autorole(ctx, *, role_name_input):
    global role_name

    # Проверяем, существует ли указанная роль в сервере
    role = discord.utils.get(ctx.guild.roles, name=role_name_input)
    if role is None:
        await ctx.send(f"Роль '{role_name_input}' не существует.")
        return

    role_name = role_name_input
    await ctx.send(f"Авто роль изменена на '{role_name}'.")

@bot.event
async def on_member_join(member):
    global role_name
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role is not None:
        await member.add_roles(role)

@bot.event
async def on_guild_join(guild):
    """Заполнение json файла при заходе бота на сервер"""
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix[str(guild.id)] = "!"

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)

"<------------[Автоматически меняет информацию о префиксе в json файле при выхода с сервера]------------>"

@bot.event
async def on_guild_remove(guild):
    """Очистка json файла, префикса сервера откуда вышел бот"""
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix.pop(str(guild.id))

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)

"<------------[Вывод префикса]------------>"

@bot.slash_command(id_server = [settings['id_server']])
async def prefix(ctx: discord.ApplicationContext)-> str:
    """Функция которая выводит информацию о префиксе для команд на определенном сервере"""
    with open('prefix.json') as file:
        data = json.load(file)
        if settings['id_server'] in data:
            templates = data[settings['id_server']]
        else:
            templates = "Ключ сервера не найден"
    await ctx.respond(f"Префикс сервера - {templates}")

"<------------[Временные войс каналы]------------>"
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None and after.channel != before.channel:
        if "time" in after.channel.name.lower():
            await create_temporary_channel(after.channel, member)

    if before.channel is not None and before.channel != after.channel:
        if len(before.channel.members) == 0:
            await delete_temporary_channel(before.channel)

async def create_temporary_channel(channel, member):
    category = channel.category 
    if "time" in channel.name.lower():
        new_channel = await channel.clone() 
        await new_channel.edit(name=f"Temp")  
        await new_channel.edit(category=None)  
        await new_channel.set_permissions(channel.guild.default_role, connect=True)  
        await new_channel.set_permissions(new_channel.guild.me, connect=True)  
        await member.move_to(new_channel)

async def delete_temporary_channel(channel):
    if "temp" in channel.name.lower():
        await channel.delete()


"<------------[Cистема тикетов]------------>"
@bot.command()
async def ticket(ctx):
    # Создаем временный текстовый канал
    ticket_channel = await create_temporary_channel(ctx.author)

    # Отправляем сообщение с информацией о созданном канале
    await ctx.send(f"Создан тикет: {ticket_channel.mention}")

    # Отправляем сообщение с кнопкой закрытия тикета
    await send_close_ticket_message(ticket_channel)

async def create_temporary_channel(author):
    guild = author.guild
    category = discord.utils.get(guild.categories, name=ticket_category_name)

    # Проверяем, есть ли категория для тикетов. Если нет, создаем новую категорию.
    if category is None:
        category = await guild.create_category(name=ticket_category_name)

    # Создаем временный текстовый канал
    ticket_channel = await category.create_text_channel(name=f"ticket-{author.name}",
                                                       overwrites=await get_channel_overwrites(guild, author))

    return ticket_channel

async def get_channel_overwrites(guild, author):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        author: discord.PermissionOverwrite(read_messages=True)
    }
    return overwrites

async def send_close_ticket_message(channel):
    # Создаем View для кнопки
    class CloseTicketView(View):
        def __init__(self):
            super().__init__()
            self.timeout = None

        @discord.ui.button(label='Закрыть тикет', style=discord.ButtonStyle.danger, emoji='🔒')
        async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
            await channel.delete()

    # Создаем сообщение с кнопкой закрытия тикета
    embed = discord.Embed(title='Тикет', description='Для закрытия тикета нажмите кнопку ниже.')
    view = CloseTicketView()
    message = await channel.send(embed=embed, view=view)

    return message

"<------------[Смена префикса]------------>"

@bot.slash_command(id_server = [settings['id_server']])
async def setprefix(ctx: discord.ApplicationContext,*,newprefix:str):
    """Установка нового префикса на сервере"""
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix[str(ctx.guild.id)] = newprefix

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)
    await ctx.response.send_message(f"Префикс сменен на {newprefix}", ephemeral=True) 

def get_prefix():
    """Чтение префикса их файла"""
    with open('prefix.json') as file:
        data = json.load(file)
        if settings['id_server'] in data:
            templates = data[settings['id_server']]
        else:
            templates = "Ключ сервера не найден"
        return templates

"<------------[Кнопка]------------>"

class MyView(View):
    def __init__(self):
        """Создании кнопки для перехода на ролевую систему"""
        super().__init__()
        self.add_item(Button(label="Переход к просмотру ролевой системы", url="https://miro.com/app/board/uXjVMHAPgZY=/"))

class Accept(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="Потверждаю что ознакомился с правилами"))
        

@bot.slash_command(name="roles")
async def roles(ctx: discord.ApplicationContext):
    """Вывод ссылки на ролевую модель в виде таблицы"""
    view = MyView()
    await ctx.send(view=view)
    
"<------------[++++++++++++++]------------>"

@bot.slash_command(id_server=[settings['id_server']])
async def welcome(ctx: discord.ApplicationContext):
    """Вывод правил сервера"""
    emb = discord.Embed(title='Правила')
    emb.add_field(name=':one: Запрещено', value='Использование микрофона без разрешения во время учебного процесса', inline=False)
    emb.add_field(name=':two: Запрещено', value='Использование звуковой панели', inline=False)
    emb.add_field(name=':three: Запрещено', value='Установка имени отличного от образца', inline=False)
    role_button = RoleButton(role_id=1108739184962830408)
    await ctx.send(view=role_button)
    await ctx.response.send_message(embed=emb)

class RoleButton(View):
    def __init__(self, role_id):
        super().__init__()
        self.role_id = role_id
        self.role_id_old = "1108739091211767808"

    @discord.ui.button(label='Я принимаю правила', style=discord.ButtonStyle.primary)
    async def get_role(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = interaction.user
        role = interaction.guild.get_role(self.role_id)
        old_role = interaction.guild.get_role(self.role_id_old)
        await member.add_roles(role)
        await member.remove_roles(old_role)
        await interaction.response.send_message(f"Поздравляю вы получили роль {role.name}", ephemeral=True)

@bot.command()
async def start(ctx, role: discord.Role):
    allowed_roles = [1108741366541979759,1108741692485546054,1108741762547187814,1108741847678980216,1108741923398746206,1108742278660505630]
    role_id_check = role.id
    if role_id_check not in allowed_roles:
       await ctx.send(f"Запрещено тэгать эту роль!")
       await ctx.message.delete()
       return
    await ctx.message.delete()
    await ctx.send(f"<@&{role_id_check}> Подключаемся к паре!")

@bot.command()
async def role_id(ctx, role: discord.Role):
    role_id = role.id
    await ctx.send(f"ID роли '{role.name}': {role_id}")

@bot.command()
async def setup_role_button(ctx):
    # Создаем новую кнопку с указанным ID роли
    role_button = RoleButton(role_id=1108739184962830408)
    await ctx.send('Click the button to get the role:', view=role_button)

def has_adm_role():
    def predicate(ctx):
        """Задает ограницения по определенной роли"""
        adm_role = discord.utils.get(ctx.guild.roles, name="📌Администратор")
        return adm_role in ctx.author.roles
    return commands.check(predicate)

@bot.slash_command(id_server = [settings['id_server']])
@has_adm_role()
async def userinfo(ctx: discord.ApplicationContext, user: discord.User):
    """Вывод информации о пользователе"""
    user_id = user.id
    username = user.name
    avatar = user.display_avatar.url
    await ctx.response.send_message(f'Пользователь найден: {user_id} -- {username}\n{avatar}', ephemeral=True)

@userinfo.error
async def roll_error(ctx):
    """Вывод ошибки при нарушении прав пользования командами"""
    await ctx.send('Извините, но у вас нет роли "📌Администратор" для использования этой команды.')

@bot.command() 
async def members(ctx):
    """Вывод всех тегов пользователей"""
    for guild in bot.guilds:
        for member in guild.members:
            await ctx.send(f"Пользователь - {member}")

@bot.slash_command(id_server=[settings['id_server']])
async def info_command(ctx: discord.ApplicationContext):
    """Вывод всех команд и их уровни доступа"""
    emb = discord.Embed(title='Все команды')
    emb.add_field(name='Уровень доступа | Название ', value='Функционал', inline=False)
    emb.add_field(name='3 уровень доступа | members', value='Вывод всех тегов пользователей', inline=False)
    emb.add_field(name='2 уровень доступа | userinfo', value='Вывод персональной информации о человеке', inline=False)
    emb.add_field(name='Общий уровень доступа | welcome', value='Вывод правил сервера', inline=False)
    emb.add_field(name='1 уровень доступа | roles', value='Переход на доску миро с описанием ролевой модели', inline=False)
    emb.add_field(name='2 уровень доступа | setprefix', value='Установка нового префикса на сервере', inline=False)
    await ctx.response.send_message(embed=emb, ephemeral=True) 

word_responses = {
    'бля': 'Не матерись!'
}

@bot.event
async def on_message(message):
    if not message.author.bot:
        content = message.content.lower()

        for word, response in word_responses.items():
            if word in content:
                await message.delete()
                await message.channel.send(response)
                break  

    await bot.process_commands(message) 

@bot.event
async def on_ready():
    """Вывод в консоль информации о состоянии бота"""
    print(f'Бот включен {bot.user}')

bot.run(settings['token'])