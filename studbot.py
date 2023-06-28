import discord
from config import settings
from discord.ui import Button, View
from discord.ext import commands
from googletrans import Translator
from pytils import translit
import platform
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import asyncio
import json
import openai

CHANNEL_ID = '1108748083950534738'
INACTIVITY_PERIOD = 2
API_KEY = 'AIzaSyAAb1RW01ySR6Rojt4Sw'
OPENAI_API_KEY = 'sk-dSCtjWHUAyOkOsZe7m1zT3BlbkFJIy8X0r5H3'
ticket_category_name = "Тикеты"
role_name = '🕑 Гость'

translator = Translator()

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

@bot.event
async def on_guild_remove(guild):
    """Очистка json файла, префикса сервера откуда вышел бот"""
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix.pop(str(guild.id))

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)

@bot.command()
async def transl(ctx, *,text):
    translit_dict = {
        'q': 'й',
        'w': 'ц',
        'e': 'у',
        'r': 'к',
        't': 'е',
        'y': 'н',
        'u': 'г',
        'i': 'ш',
        'o': 'щ',
        'p': 'з',
        'a': 'ф',
        's': 'ы',
        'd': 'в',
        'f': 'а',
        'g': 'п',
        'h': 'р',
        'j': 'о',
        'k': 'л',
        'l': 'д',
        'z': 'я',
        'x': 'ч',
        'c': 'с',
        'v': 'м',
        'b': 'и',
        'n': 'т',
        'm': 'ь',
        ' ': ' ',
        '-': '-',
        '`': 'ё'
    }
    
    result = ''
    for char in text:
        if char.lower() in translit_dict:
            result += translit_dict[char.lower()]
        else:
            result += char

    await ctx.send(result)

@bot.command()
async def youtube_search(ctx, *, query):
    try:
        # Создаем YouTube Data API клиент
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # Осуществляем поиск видео по запросу
        search_response = youtube.search().list(
            q=query,
            part='id',
            maxResults=5
        ).execute()
        
        # Получаем ссылки на найденные видео
        video_links = []
        for item in search_response['items']:
            if item['id']['kind'] == 'youtube#video':
                video_links.append(f"https://www.youtube.com/watch?v={item['id']['videoId']}")
        
        # Отправляем ссылки в личные сообщения пользователю
        if video_links:
            user = ctx.author
            for link in video_links:
                await user.send(link)
            await ctx.send(f'Я отправил ссылки на видео по запросу "{query}" в личные сообщения.')
        else:
            await ctx.send(f'По запросу "{query}" не найдено видео на YouTube.')
    except Exception as e:
        await ctx.send(f'Ошибка при выполнении поиска: {str(e)}')

@bot.command()
async def prole(ctx, role_name):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=role_name)
    
    if role is None:
        await ctx.send(f"Роль '{role_name}' не найдена.")
        return
    
    online_users = [member for member in guild.members if role in member.roles and str(member.status) == 'online']
    
    message = f"Пользователи с ролью '{role_name}', находящиеся в сети:\n\n"
    for user in online_users:
        message += f"<@{user.id}>\n"
    
    await ctx.author.send(message)
    await ctx.send("Информация отправлена в личное сообщение.")

@bot.command()
async def timer(ctx, seconds):
    try:
        seconds = int(seconds)
    except ValueError:
        await ctx.send("Пожалуйста, укажите число секунд в качестве аргумента.")
        return

    await ctx.send(f"Таймер установлен на {seconds} секунд.")

    # Ожидаем указанное количество секунд
    await asyncio.sleep(seconds)

    # Отправляем уведомление о истечении времени в личное сообщение
    await ctx.author.send(f"Время истекло после {seconds} секунд!")



@bot.command()
async def poll(ctx, question, *options):
    # Создаем встраиваемое сообщение для голосования
    embed = discord.Embed(title="Голосование", description=question, color=discord.Color.blue())
    
    # Формируем список вариантов ответов
    options_text = "\n".join([f"{i + 1}. {option}" for i, option in enumerate(options)])
    embed.add_field(name="Варианты ответов", value=options_text, inline=False)
    
    # Отправляем встраиваемое сообщение
    message = await ctx.send(embed=embed)
    
    # Добавляем реакции к сообщению для каждого варианта ответа
    for i, _ in enumerate(options):
        emoji = get_emoji(i)
        await message.add_reaction(emoji)
    
    # Ожидаем реакции пользователей
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id
    
    try:
        reaction, user = await bot.wait_for("reaction_add", check=check, timeout=60)
        
        # Получаем выбранный вариант ответа
        selected_option = get_option(reaction.emoji, options)
        
        # Обновляем встраиваемое сообщение с результатом голосования
        embed.add_field(name="Результат", value=f"Вы выбрали вариант: {selected_option}")
        await message.edit(embed=embed)
    except TimeoutError:
        await message.edit(content="Голосование завершилось по таймауту.")
    
    # Удаляем сообщение пользователя
    await ctx.message.delete()

# Функция для получения соответствующего эмодзи по индексу
def get_emoji(index):
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    return emojis[index]

# Функция для получения соответствующего варианта ответа по эмодзи
def get_option(emoji, options):
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    index = emojis.index(emoji)
    return options[index]

@bot.command()
async def add_role(ctx, member: discord.Member, role: discord.Role, duration: int):
    # Проверяем, имеет ли пользователь право назначать роли
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.send("У вас нет разрешения на назначение ролей.")
        return
    
    # Проверяем, имеет ли бот право назначать роли
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("У меня нет разрешения на назначение ролей.")
        return
    
    # Назначаем роль пользователю
    await member.add_roles(role)
    await ctx.send(f"Роль `{role.name}` была назначена пользователю {member.mention} на {duration} секунд.")
    
    # Ждем указанное время
    await asyncio.sleep(duration)
    
    # Снимаем роль с пользователя
    await member.remove_roles(role)
    await ctx.send(f"Роль `{role.name}` была снята с пользователя {member.mention}.")

openai.api_key = OPENAI_API_KEY

@bot.command()
async def send_openai(ctx, *, message):
    # Разделяем элементы списка по разделителю ';'
    items = message.split(';')
    
    # Формируем нумерованный список с помощью Markdown
    formatted_list = '\n'.join([f'{index}. {item.strip()}' for index, item in enumerate(items, start=1)])
    
    # Отправляем сообщение в Chat API v3
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=formatted_list,
        max_tokens=4000,
        n=1,
        stop=None,
        temperature=0.7 
    )
    
    # Получаем ответ от Chat API
    reply = response.choices[0].text.strip()
    
    # Отправляем ответ в канал Discord
    await ctx.send(f"Ответ от Chat API: {reply}")

@bot.command()
async def system_info(ctx):
    # Получаем системные характеристики
    system_name = platform.system()
    processor = platform.processor()
    motherboard = platform.node()
    gpu = "Недоступно"
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0].name
    except ImportError:
        pass
    
    # Форматируем информацию в виде сообщения
    message = f"Системные характеристики:\n\n"
    message += f"ОС: {system_name}\n"
    message += f"Процессор: {processor}\n"
    message += f"Материнская плата: {motherboard}\n"
    message += f"Видеокарта: {gpu}\n"
    
    # Отправляем сообщение в канал Discord
    await ctx.message.delete()
    await ctx.send(message)
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
            await creates_temporary_channel(after.channel, member)

    if before.channel is not None and before.channel != after.channel:
        if len(before.channel.members) == 0:
            await delete_temporary_channel(before.channel)

async def creates_temporary_channel(channel, member):
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
