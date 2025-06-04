

import discord
from discord.ext import commands
from discord import app_commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True  # メッセージコンテンツの読み取りを許可
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1378983271039242242 # 自分のギルドIDに置き換えてください

waiting_queue = []

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

        waiting_queue.append(user_id)
        await interaction.response.send_message(
            f"マッチ待機に登録しました。\n現在の待機人数: {len(waiting_queue)}人",
            ephemeral=True
        )

        if len(waiting_queue) >= 3:
            matched = waiting_queue[:3]
            del waiting_queue[:3]

            mentions = ", ".join(f"<@{uid}>" for uid in matched)
            match_channel = discord.utils.get(interaction.guild.channels, name="マッチング部屋")

            message_text = f"マッチング成立！ {mentions} がマッチしました！\n{mentions} 部屋立てお願いします"

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

        waiting_queue.remove(user_id)
        await interaction.response.send_message(
            f"マッチ待機をキャンセルしました。\n現在の待機人数: {len(waiting_queue)}人",
            ephemeral=True
        )

@app_commands.command(name="match", description="マッチングUIを表示")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def match(interaction: discord.Interaction):
    waiting_count = len(waiting_queue)
    view = MatchView()
    await interaction.response.send_message(
        f"マッチ開始またはキャンセルボタンを押してください。\n現在の待機人数: {waiting_count}人",
        view=view,
        ephemeral=True
    )

@app_commands.command(name="result", description="結果入力を開始します")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def result(interaction: discord.Interaction):
    questions = [
        "勝者は？",
        "敗者1は？",
        "敗者2は？",
        "勝利ウマ娘は？"
    ]
    answers = []

    await interaction.response.send_message("結果入力を開始します。質問に答えてください。", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    for question in questions:
        await interaction.followup.send(question, ephemeral=True)
        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send(" 時間切れです。最初からやり直してください。", ephemeral=True)
            return
        answers.append(msg.content.strip())

    # ここでスプレッドシートへの記録やレーティング更新の処理など追加可能

    await interaction.followup.send(
        f"✅ 結果を受け付けました！\n"
        f"勝者: {answers[0]}\n"
        f"敗者1: {answers[1]}\n"
        f"敗者2: {answers[2]}\n"
        f"勝利ウマ娘: {answers[3]}",
        ephemeral=True
    )

bot.tree.add_command(match)
bot.tree.add_command(result)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Synced commands to guild {GUILD_ID}")
    print(f"Logged in as {bot.user}")

bot.run("MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo")
