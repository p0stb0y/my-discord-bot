
from discord.ext import commands 
from discord import app_commands
import discord
import asyncio
import time

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from glicko2 import Player as GlickoPlayer

SERVICE_ACCOUNT_FILE = 'client_secrets.json'
SPREADSHEET_ID = '1P9supK0vR3M36Yt1R3rWfpx57mZckJ1nYRF8O4RsuK0'

def get_sheets_service():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def get_all_players(sheet):
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Ratings!A2:D').execute()
    return result.get('values', [])

def players_to_dict(players_data):
    players_dict = {}
    for row in players_data:
        if not row or not row[0].strip():
            continue
        name = row[0].strip()
        player = GlickoPlayer()
        if len(row) > 1 and row[1]:
            player.setRating(float(row[1]))
        if len(row) > 2 and row[2]:
            player.setRd(float(row[2]))
        if len(row) > 3 and row[3]:
            player.vol = float(row[3])
        players_dict[name] = player
    return players_dict

def dict_to_values(players_dict):
    values = []
    for name, player in players_dict.items():
        values.append([
            name,
            round(player.getRating(), 2),
            round(player.getRd(), 2),
            round(player.vol, 5)
        ])
    values.sort(key=lambda x: float(x[1]) if x[1] else 0, reverse=True)
    return values

def update_ratings(sheet, winner_name, loser1_name, loser2_name):
    players_data = get_all_players(sheet)
    players = players_to_dict(players_data)

    for pname in [winner_name, loser1_name, loser2_name]:
        if pname not in players:
            players[pname] = GlickoPlayer()

    winner = players[winner_name]
    loser1 = players[loser1_name]
    loser2 = players[loser2_name]

    try:
        winner.update_player(
            [loser1.getRating(), loser2.getRating()],
            [loser1.getRd(), loser2.getRd()],
            [1.0, 1.0]
        )
        loser1.update_player(
            [winner.getRating()],
            [winner.getRd()],
            [0.0]
        )
        loser2.update_player(
            [winner.getRating()],
            [winner.getRd()],
            [0.0]
        )
    except AttributeError:
        raise RuntimeError("GlickoPlayer.update_player メソッドが存在しません。別の実装を検討してください。")

    updated_values = dict_to_values(players)
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Ratings!A2:D',
        valueInputOption='RAW',
        body={'values': updated_values}
    ).execute()

def append_to_sheet(sheet, values):
    return sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Matches!A:D',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [values]}
    ).execute()

# Discord Bot 設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1378983271039242242
waiting_queue = {}  # user_id -> time_added

async def timeout_checker():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"ギルドID {GUILD_ID} が見つかりません。")
        return
    channel = discord.utils.get(guild.channels, name="マッチング部屋")
    if not channel or not isinstance(channel, discord.TextChannel):
        print("『マッチング部屋』チャンネルが見つかりません。")
        return

    while True:
        now = time.time()
        # 5分 = 300秒に変更
        to_remove = [uid for uid, joined in waiting_queue.items() if now - joined > 300]
        if to_remove:
            print(f"Timeout checker: removing users {to_remove}")
        for uid in to_remove:
            del waiting_queue[uid]
            user = bot.get_user(uid)
            if user:
                try:
                    await channel.send(f"⏰ <@{uid}> さん、5分経過のためマッチ待機を自動キャンセルしました。再度マッチ開始してください。")
                    print(f"Sent mention timeout message for user {user}")
                except Exception as e:
                    print(f"Failed to send mention for {user}: {e}")
        await asyncio.sleep(10)

class MatchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="マッチ開始", style=discord.ButtonStyle.primary, custom_id="match_start")
    async def match_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in waiting_queue:
            await interaction.response.send_message(
                f"すでにマッチ待機中です。\n現在の待機人数: {len(waiting_queue)}人",
                ephemeral=True
            )
            return

        waiting_queue[user_id] = time.time()
        await interaction.response.send_message(
            f"マッチ待機に登録しました。\n現在の待機人数: {len(waiting_queue)}人",
            ephemeral=True
        )

        if len(waiting_queue) >= 3:
            matched = list(waiting_queue.keys())[:3]
            for uid in matched:
                del waiting_queue[uid]
            mentions = ", ".join(f"<@{uid}>" for uid in matched)
            first_user_mention = f"<@{matched[0]}>"

            match_channel = discord.utils.get(interaction.guild.channels, name="マッチング部屋")
            message_text = (
                f"マッチング成立！ {mentions} がマッチしました！\n"
                f"{first_user_mention} 部屋立てお願いします"
            )

            if match_channel and isinstance(match_channel, discord.TextChannel):
                await match_channel.send(message_text)
            else:
                await interaction.channel.send(message_text)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger, custom_id="cancel_match")
    async def cancel_match(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in waiting_queue:
            await interaction.response.send_message("現在マッチ待機中ではありません。", ephemeral=True)
            return

        del waiting_queue[user_id]
        await interaction.response.send_message(
            f"マッチ待機をキャンセルしました。\n現在の待機人数: {len(waiting_queue)}人",
            ephemeral=True
        )

@app_commands.command(name="match", description="マッチングUIを表示")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def match(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"マッチ開始またはキャンセルボタンを押してください。\n現在の待機人数: {len(waiting_queue)}人",
        view=MatchView(),
        ephemeral=True
    )

@app_commands.command(name="result", description="結果入力を開始します")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def result(interaction: discord.Interaction):
    questions = ["勝者は？", "敗者1は？", "敗者2は？", "勝利ウマ娘は？"]
    answers = []

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    await interaction.response.send_message(questions[0], ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ 時間切れです。最初からやり直してください。", ephemeral=True)
        return
    answers.append(msg.content.strip())

    for question in questions[1:]:
        await interaction.followup.send(question, ephemeral=True)
        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ 時間切れです。最初からやり直してください。", ephemeral=True)
            return
        answers.append(msg.content.strip())

    sheet = get_sheets_service()

    try:
        update_ratings(sheet, answers[0], answers[1], answers[2])
        append_to_sheet(sheet, answers)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 処理中にエラーが発生しました: {e}", ephemeral=True)
        return

    await interaction.followup.send(
        f"✅ 結果を受け付けました！\n"
        f"勝者: {answers[0]}\n敗者1: {answers[1]}\n敗者2: {answers[2]}\n勝利ウマ娘: {answers[3]}",
        ephemeral=True
    )

@app_commands.command(name="wait", description="現在のマッチ待機人数を表示します")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def wait(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"現在の待機人数は {len(waiting_queue)}人です。",
        ephemeral=True
    )

# コマンド登録
bot.tree.add_command(match)
bot.tree.add_command(result)
bot.tree.add_command(wait)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    bot.add_view(MatchView())
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    asyncio.create_task(timeout_checker())
    print(f"✅ Synced commands to guild {GUILD_ID}")
    print(f"🟢 Logged in as {bot.user}")

bot.run("MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo")
