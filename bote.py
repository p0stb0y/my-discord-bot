import discord
from keep_alive import keep_alive  # 上記Webサーバーコードを別ファイルにしてimportでもOK

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

keep_alive()
client.run('MTM3OTA4MTQ0MzY0MDIxMzUxNA.GrWkNv.Hd4qDBZKICYnzkEABH7IENss_CdXEblpM9fUuo')
