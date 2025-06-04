import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# あなたのDiscordサーバーIDに置き換えてください（半角数字）
GUILD_ID = 1378983271039242242

# --- Google Sheets 認証周り ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secrets.json", scope)
client = gspread.authorize(creds)

spreadsheet = client.open("レート戦")
matches_sheet = spreadsheet.worksheet("Matches")
ratings_sheet = spreadsheet.worksheet("Ratings")

K = 32  # Elo定数

def load_ratings():
    ratings = {}
    data = ratings_sheet.get_all_values()
    for row in data:
        if len(row) >= 2:
            player = row[0].strip()
            try:
                rating = float(row[1])
            except:
                rating = 1500
            if player:
                ratings[player] = rating
    return ratings

def save_ratings(ratings):
    output = [[player, round(rating)] for player, rating in ratings.items() if player]
    output.sort(key=lambda x: x[1], reverse=True)
    ratings_sheet.clear()
    if output:
        ratings_sheet.update('A1', output)

def update_ratings_nplayer(players, ratings):
    for p in players:
        if p not in ratings:
            ratings[p] = 1500
    winner = players[0]
    losers = players[1:]
    for loser in losers:
        Rw = ratings[winner]
        Rl = ratings[loser]
        Ew = 1 / (1 + 10 ** ((Rl - Rw) / 400))
        El = 1 / (1 + 10 ** ((Rw - Rl) / 400))
        ratings[winner] = Rw + K * (1 - Ew)
        ratings[loser] = Rl + K * (0 - El)
    return ratings

# ---------------------------------
# /result コマンドの実装（スラッシュコマンド版）
@bot.tree.command(
    name="result",
    description="結果入力を開始します",
    guild=discord.Object(id=GUILD_ID)  # ギルド限定で即時反映
)
async def result(interaction: discord.Interaction):
    questions = [
        "勝者は？",
        "敗者1は？",
        "敗者2は？",
        "勝利ウマ娘は？"
    ]
    answers = []

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    await interaction.response.send_message("結果入力を開始します。順番に答えてください。", ephemeral=True)

    for question in questions:
        await interaction.followup.send(question, ephemeral=True)
        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ 時間切れです。最初からやり直してください。", ephemeral=True)
            return
        answers.append(msg.content.strip())

    # スプレッドシートに4つの情報を記録（備考はD列）
    matches_sheet.append_row(answers)

    # レーティングの更新（最初の3人のみ使用）
    ratings = load_ratings()
    ratings = update_ratings_nplayer(answers[:3], ratings)
    save_ratings(ratings)

    await interaction.followup.send(
        f"✅ レーティングを更新しました！\n"
        f"勝者: {answers[0]}\n"
        f"敗者1: {answers[1]}\n"
        f"敗者2: {answers[2]}\n"
        f"勝利ウマ娘: {answers[3]}",
        ephemeral=True
    )

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)  # ギルド限定コマンドを即時同期
    print(f"Logged in as {bot.user}, synced commands for guild {GUILD_ID}")

bot.run("MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo")


