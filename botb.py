
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ← ここは必ず半角数字でサーバーIDを入れる（例：123456789012345678）
GUILD_ID =  1378983271039242242

waiting_queue = []  # 待機ユーザーリスト

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

@bot.tree.command(name="match", description="マッチングUIを表示")
@app_commands.guilds(discord.Object(id=GUILD_ID))  # ギルド限定コマンドにする
async def match(interaction: discord.Interaction):
    view = MatchView()
    waiting_count = len(waiting_queue)
    await interaction.response.send_message(
        f"マッチ開始またはキャンセルボタンを押してください。\n現在の待機人数: {waiting_count}人",
        view=view,
        ephemeral=True
    )

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    # ギルドコマンドだけ同期するならこっちの方が早いです
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'Logged in as {bot.user}')

# ここは必ず実際のBotトークンに差し替えてください！
bot.run("MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo")

