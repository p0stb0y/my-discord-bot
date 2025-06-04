import threading
from flask import Flask
import discord
from discord.ext import commands

# ===== Flask サーバーの設定 =====
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is online!"

def run_flask():
    # 本番用では debug=False にする
    app.run(host='0.0.0.0', port=8080, debug=False)

# ===== Discord BOT の設定 =====
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# ===== メイン処理 =====
if __name__ == '__main__':
    # Flaskをバックグラウンドスレッドで起動
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Discord BOT を起動（← 自分のトークンに置き換える）
    bot.run('MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo')
