import discord
from discord.ext import commands
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'client_secrets.json'  # 実際のファイル名に変更
SPREADSHEET_ID = '1P9supK0vR3M36Yt1R3rWfpx57mZckJ1nYRF8O4RsuK0'  # 実際のIDに変更
SHEET_NAME_MATCHES = 'Matches'
SHEET_NAME_RATINGS = 'Ratings'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

K = 32  # 定数（お好みで）

def update_ratings():
    sh = gc.open_by_key(SPREADSHEET_ID)
    sheet_matches = sh.worksheet(SHEET_NAME_MATCHES)
    sheet_ratings = sh.worksheet(SHEET_NAME_RATINGS)

    # 現在のレーティングを取得
    ratings_data = sheet_ratings.get_all_values()
    ratings = {}
    for row in ratings_data:
        if len(row) >= 2:
            try:
                ratings[row[0]] = float(row[1])
            except ValueError:
                # 不正な数値（#NUM!など）はスキップ
                print(f"スキップ: {row}")

    # まだ誰もいない場合
    if not ratings:
        ratings = {}

    # 試合データを取得
    match_data = sheet_matches.get_all_values()

    for match in match_data:
        if len(match) < 4:
            continue  # 不完全データ

        user, p1, p2, p3 = match[0], match[1], match[2], match[3]

        # 新規プレイヤーなら初期化
        for p in [p1, p2, p3]:
            if p not in ratings:
                ratings[p] = 1500

        # 勝者p1の期待勝率（2人相手の平均）
        e_p1_p2 = 1 / (1 + 10 ** ((ratings[p2] - ratings[p1]) / 400))
        e_p1_p3 = 1 / (1 + 10 ** ((ratings[p3] - ratings[p1]) / 400))
        e_p1 = (e_p1_p2 + e_p1_p3) / 2

        # 敗者の期待勝率（勝者に対してのみ）
        e_p2 = 1 / (1 + 10 ** ((ratings[p1] - ratings[p2]) / 400))
        e_p3 = 1 / (1 + 10 ** ((ratings[p1] - ratings[p3]) / 400))

        # レート更新
        ratings[p1] += K * (1 - e_p1)
        ratings[p2] += K * (0 - e_p2)
        ratings[p3] += K * (0 - e_p3)

    # 丸めて降順にソート
    output = [[player, round(rating)] for player, rating in ratings.items()]
    output.sort(key=lambda x: x[1], reverse=True)

    # シートに書き戻し
    sheet_ratings.clear()
    sheet_ratings.update('A1', output)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command()
async def input(ctx, val1: str, val2: str, val3: str):
    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(SHEET_NAME_MATCHES)

        user = ctx.author.display_name
        row = [user, val1, val2, val3]

        worksheet.append_row(row)
        await ctx.send(f'{user} のデータをスプレッドシートに追加しました。')

        # レーティング更新（APIではなくローカルで処理）
        update_ratings()
        await ctx.send('レーティング更新完了！')

    except Exception as e:
        await ctx.send(f'エラーが発生しました: {type(e).__name__} - {e}')

bot.run('MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo')

