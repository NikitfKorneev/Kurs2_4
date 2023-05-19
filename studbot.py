import discord
from config import settings
from discord.ui import Button, View
from discord.ext import commands
import json

def get_server_prefix(client, message):
    with open("prefix.json","r") as f:
        prefix = json.load(f)
    
    return prefix[str(message.guild.id)]

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix= get_server_prefix, intents=intents)

@bot.event
async def on_guild_join(guild):
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix[str(guild.id)] = "!"

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)

"<------------[Автоматически меняет информацию о префиксе в json файле при выхода с сервера]------------>"

@bot.event
async def on_guild_remove(guild):
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix.pop(str(guild.id))

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)

"<------------[Смена префикса]------------>"

@bot.slash_command(id_server = [settings['id_server']])
async def setprefix(ctx: discord.ApplicationContext,*,newprefix:str):
    with open("prefix.json","r") as f:
        prefix = json.load(f)

    prefix[str(ctx.guild.id)] = newprefix

    with open("prefix.json","w") as f:
        json.dump(prefix,f,indent=4)
    await ctx.response.send_message(f"Префикс сменен на {newprefix}", ephemeral=True) 

def get_prefix():
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
        super().__init__()
        self.add_item(Button(label="Переход к просмотру ролевой системы", url="https://miro.com/app/board/uXjVMHAPgZY=/"))

class Accept(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="Потверждаю что ознакомился с правилами"))
        

@bot.slash_command(name="roles")
async def roles(ctx: discord.ApplicationContext):
    view = MyView()
    await ctx.send(view=view)
    
"<------------[++++++++++++++]------------>"

@bot.slash_command(id_server=[settings['id_server']])
async def welcome(ctx: discord.ApplicationContext):
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
async def setup_role_button(ctx):
    # Создаем новую кнопку с указанным ID роли
    role_button = RoleButton(role_id=1108739184962830408)
    await ctx.send('Click the button to get the role:', view=role_button)

















@bot.event
async def on_ready():
    print(f'Бот включен {bot.user}')


bot.run(settings['token'])