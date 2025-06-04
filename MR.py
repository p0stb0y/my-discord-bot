import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1378983271039242242  # 自分のギルドIDに置き換え

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Synced commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")

@app_commands.command(name="match", description="マッチングUIを表示")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def match(interaction: discord.Interaction):
    await interaction.response.send_message("マッチングコマンドです！")

@app_commands.command(name="result", description="結果入力コマンド")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def result(interaction: discord.Interaction):
    await interaction.response.send_message("結果入力コマンドです！")

bot.tree.add_command(match)
bot.tree.add_command(result)

bot.run("MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo")
